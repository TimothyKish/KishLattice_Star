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

C_THRESH_PRIMARY = 0.163
DELTA_C_THRESH_PRIMARY = 0.05

TARGET_LOW = 2865.5
TARGET_HIGH = 5546.0

def run_smoke_alarm_test():
    print(f"[*] MONDY DIRECTIVE: Executing 'Look-Elsewhere' Smoke Alarm Test...")
    print(f"[*] Testing Lane 1 logic against PURE PRE-MERGER NOISE.\n")
    
    events = {}
    for f in glob.glob(os.path.join(DATA_DIR, "*.hdf5")):
        base = os.path.basename(f)
        parts = base.rsplit('_', 1)
        if len(parts) < 2: continue
        event = parts[0]
        det = parts[1][:2]
        if event not in events: events[event] = {}
        events[event][det] = f

    eligible_events = {e: files for e, files in events.items() if 'H1' in files and 'L1' in files}
    
    false_positives = 0
    total_tested = 0
    
    for event, files in eligible_events.items():
        try:
            h1_ts = TimeSeries.read(files['H1'], format='hdf5').value
            l1_ts = TimeSeries.read(files['L1'], format='hdf5').value
            
            if np.isnan(h1_ts).any() or np.isnan(l1_ts).any():
                continue

            # MONDY'S CONTROL: Split the 2.0s pure noise baseline into two chunks
            # Chunk A (Control Baseline): 0.0s to 0.9s
            # Chunk B (Fake "Post" Window): 1.0s to 1.9s
            h1_noise_A = h1_ts[int(0.0 * FS):int(0.9 * FS)]
            l1_noise_A = l1_ts[int(0.0 * FS):int(0.9 * FS)]
            
            h1_noise_B = h1_ts[int(1.0 * FS):int(1.9 * FS)]
            l1_noise_B = l1_ts[int(1.0 * FS):int(1.9 * FS)]
            
            # Run Coherence
            _, c_noise_A = coherence(h1_noise_A, l1_noise_A, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
            f_bin, c_noise_B = coherence(h1_noise_B, l1_noise_B, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
            
            delta_c = c_noise_B - c_noise_A
            
            bin_mask = (f_bin >= TARGET_LOW) & (f_bin <= TARGET_HIGH)
            c_noise_B_masked = c_noise_B[bin_mask]
            delta_c_masked = delta_c[bin_mask]
            
            # THE FLAWED LOGIC
            max_idx = np.argmax(delta_c_masked)
            max_delta = delta_c_masked[max_idx]
            max_post = c_noise_B_masked[max_idx]
            
            total_tested += 1
            
            # If pure noise passes the threshold, it is a False Positive
            if max_post > C_THRESH_PRIMARY and max_delta > DELTA_C_THRESH_PRIMARY:
                false_positives += 1
                
        except Exception:
            pass

    print("==================================================")
    print("--- FALSE POSITIVE SMOKE ALARM (PURE NOISE) ---")
    print("==================================================")
    print(f"[*] Total Noise Events Tested: {total_tested}")
    print(f"[*] Total False Positives:     {false_positives}")
    if total_tested > 0:
        print(f"[!] FALSE POSITIVE RATE:       {(false_positives/total_tested)*100:.1f}%")
    print("==================================================")

if __name__ == "__main__":
    run_smoke_alarm_test()