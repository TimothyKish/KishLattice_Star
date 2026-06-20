import os
import glob
import numpy as np
import warnings
from gwpy.timeseries import TimeSeries
from scipy.signal import welch, coherence

warnings.filterwarnings("ignore")

DATA_DIR = "../lake/strain_data/"
FS = 16384
WINDOW_LEN = 0.1
OVERLAP = 0.5
NPERSEG = int(FS * WINDOW_LEN)      # 1638 samples
NOVERLAP = int(NPERSEG * OVERLAP)   # 819 samples
NFFT = 4096                         # ~4 Hz resolution

TARGET_LOW = 2865.5
TARGET_HIGH = 5546.0

def audit_virgo_hardware():
    print(f"[*] LYRA DIRECTIVE: Auditing Virgo (V1) High-Frequency Noise Floor...")
    
    events = {}
    for f in glob.glob(os.path.join(DATA_DIR, "*.hdf5")):
        base = os.path.basename(f)
        event = base.split('_')[0]
        det = base.split('_')[1][:2]
        if event not in events: events[event] = {}
        events[event][det] = f

    three_det_events = {e: files for e, files in events.items() if 'H1' in files and 'L1' in files and 'V1' in files}
    print(f"[*] Found {len(three_det_events)} locally cached events with H1, L1, and V1 available.\n")
    
    if len(three_det_events) == 0:
        print("[!] ERROR: No V1 strain files found in local cache. Download required.")
        return

    sample_events = list(three_det_events.keys())
    
    v1_psd_ratios = []
    h1_v1_coh_95 = []
    l1_v1_coh_95 = []

    for event in sample_events:
        files = three_det_events[event]
        try:
            h1_ts = TimeSeries.read(files['H1'], format='hdf5').value[int(0.0 * FS):int(1.9 * FS)]
            l1_ts = TimeSeries.read(files['L1'], format='hdf5').value[int(0.0 * FS):int(1.9 * FS)]
            v1_ts = TimeSeries.read(files['V1'], format='hdf5').value[int(0.0 * FS):int(1.9 * FS)]
            
            # [LYRA FIX]: Check for offline detectors (NaNs)
            if np.isnan(h1_ts).any() or np.isnan(l1_ts).any() or np.isnan(v1_ts).any():
                print(f"  [!] Skipping {event}: Detector offline during this window (NaNs detected).")
                continue
            
            f_psd, h1_psd = welch(h1_ts, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP)
            _, l1_psd = welch(l1_ts, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP)
            _, v1_psd = welch(v1_ts, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP)
            
            bin_mask = (f_psd >= TARGET_LOW) & (f_psd <= TARGET_HIGH)
            h1_median = np.median(h1_psd[bin_mask])
            l1_median = np.median(l1_psd[bin_mask])
            v1_median = np.median(v1_psd[bin_mask])
            
            avg_ligo_noise = (h1_median + l1_median) / 2.0
            noise_ratio = v1_median / avg_ligo_noise
            v1_psd_ratios.append(noise_ratio)

            f_coh, c_h1_v1 = coherence(h1_ts, v1_ts, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
            _, c_l1_v1 = coherence(l1_ts, v1_ts, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
            
            coh_mask = (f_coh >= TARGET_LOW) & (f_coh <= TARGET_HIGH)
            h1_v1_coh_95.append(np.percentile(c_h1_v1[coh_mask], 95))
            l1_v1_coh_95.append(np.percentile(c_l1_v1[coh_mask], 95))
            
        except Exception as e:
            print(f"[!] Warning: Data processing failed on {event}: {e}")

    print("==================================================")
    print("--- VIRGO TARGET-BIN HARDWARE AUDIT (2.8k - 5.5k Hz) ---")
    print("==================================================")
    if v1_psd_ratios:
        print(f"[*] Average V1 Noise Amplitude vs LIGO: {np.mean(v1_psd_ratios):.2f}x louder")
        print("-" * 50)
        print(f"[*] Empirical 95th %ile Coherence (H1-V1): {np.mean(h1_v1_coh_95):.4f}")
        print(f"[*] Empirical 95th %ile Coherence (L1-V1): {np.mean(l1_v1_coh_95):.4f}")
        print(f"[*] Theoretical K=17 Coherence Threshold : 0.1630")
    print("==================================================")
    
    if np.mean(v1_psd_ratios) > 5.0:
        print("\n[!] ARCHITECT WARNING: Virgo noise floor is severely elevated in this band.")
        print("    A separate V1 threshold or dynamic scaling is absolutely required.")

if __name__ == "__main__":
    audit_virgo_hardware()