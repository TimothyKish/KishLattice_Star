import os
import glob
import numpy as np
import warnings
from gwpy.timeseries import TimeSeries
from scipy.signal import coherence

warnings.filterwarnings("ignore")

DATA_DIR = "../lake/strain_data/"
FS = 16384
WINDOW_LEN = 0.1
OVERLAP = 0.5
NPERSEG = int(FS * WINDOW_LEN)
NOVERLAP = int(NPERSEG * OVERLAP)
NFFT = 4096

TARGET_LOW = 2865.5
TARGET_HIGH = 5546.0

def audit_global_virgo_floor():
    print(f"[*] LYRA DIRECTIVE: Calculating Global Virgo Empirical Coherence Floor...")
    
    events = {}
    for f in glob.glob(os.path.join(DATA_DIR, "*.hdf5")):
        base = os.path.basename(f)
        event = base.split('_')[0]
        det = base.split('_')[1][:2]
        if event not in events: events[event] = {}
        events[event][det] = f

    three_det_events = {e: files for e, files in events.items() if 'H1' in files and 'L1' in files and 'V1' in files}
    print(f"[*] Analyzing {len(three_det_events)} physical events with full 3-detector data...\n")
    
    global_h1_v1_coherence = []
    global_l1_v1_coherence = []

    for event, files in three_det_events.items():
        try:
            # Baseline window only: t0 - 2.0s to t0 - 0.1s
            h1_ts = TimeSeries.read(files['H1'], format='hdf5').value[int(0.0 * FS):int(1.9 * FS)]
            l1_ts = TimeSeries.read(files['L1'], format='hdf5').value[int(0.0 * FS):int(1.9 * FS)]
            v1_ts = TimeSeries.read(files['V1'], format='hdf5').value[int(0.0 * FS):int(1.9 * FS)]
            
            # Skip NaNs
            if np.isnan(h1_ts).any() or np.isnan(l1_ts).any() or np.isnan(v1_ts).any():
                continue
                
            f_coh, c_h1_v1 = coherence(h1_ts, v1_ts, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
            _, c_l1_v1 = coherence(l1_ts, v1_ts, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
            
            bin_mask = (f_coh >= TARGET_LOW) & (f_coh <= TARGET_HIGH)
            
            # Append all raw coherence bins from the target frequency range into the global pool
            global_h1_v1_coherence.extend(c_h1_v1[bin_mask])
            global_l1_v1_coherence.extend(c_l1_v1[bin_mask])
            
        except Exception as e:
            pass # Silently skip corrupted files to keep audit running

    # Calculate the true global 95th percentiles
    p95_h1_v1 = np.percentile(global_h1_v1_coherence, 95)
    p95_l1_v1 = np.percentile(global_l1_v1_coherence, 95)
    
    # Atlas's Derived Threshold: The maximum of either pair's 95th percentile
    derived_threshold = max(p95_h1_v1, p95_l1_v1)

    print("==================================================")
    print("--- GLOBAL VIRGO EMPIRICAL NOISE FLOOR (2.8k - 5.5k Hz) ---")
    print("==================================================")
    print(f"[*] Total Frequency Bins Analyzed: {len(global_h1_v1_coherence):,}")
    print(f"[*] H1-V1 95th Percentile: {p95_h1_v1:.4f}")
    print(f"[*] L1-V1 95th Percentile: {p95_l1_v1:.4f}")
    print("-" * 50)
    print(f"[+] DERIVED VIRGO THRESHOLD: > {derived_threshold:.4f}")
    print("==================================================")

if __name__ == "__main__":
    audit_global_virgo_floor()