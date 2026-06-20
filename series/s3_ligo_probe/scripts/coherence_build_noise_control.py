import os
import json
import glob
import numpy as np
import warnings
from gwpy.timeseries import TimeSeries
from scipy.signal import coherence

warnings.filterwarnings("ignore")

DATA_DIR = "../lake/strain_data/"
OUTPUT_JSONL = "../lake/ligo_coherence_NOISE_CONTROL.jsonl"
DOMAIN = "ligo_coherence_NOISE_CONTROL"

FS = 16384
WINDOW_LEN = 0.1
OVERLAP = 0.5
NPERSEG = int(FS * WINDOW_LEN)      
NOVERLAP = int(NPERSEG * OVERLAP)   
NFFT = 4096                         

TARGET_LOW = 2865.5
TARGET_HIGH = 5546.0
K_GEO = 16.0 / np.pi

def build_noise_control_lake():
    print(f"[*] MONDY DIRECTIVE: Building PURE NOISE Control Lake...")
    
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
    
    valid_primary = 0
    excluded_records = 0
    
    with open(OUTPUT_JSONL, 'w') as out_f:
        for event, files in eligible_events.items():
            try:
                h1_ts = TimeSeries.read(files['H1'], format='hdf5').value
                l1_ts = TimeSeries.read(files['L1'], format='hdf5').value
                
                if np.isnan(h1_ts).any() or np.isnan(l1_ts).any():
                    raise ValueError("primary_detector_offline")

                # Chunk A (Control Baseline): 0.0s to 0.9s
                # Chunk B (Fake "Post" Window): 1.0s to 1.9s
                h1_noise_A = h1_ts[int(0.0 * FS):int(0.9 * FS)]
                l1_noise_A = l1_ts[int(0.0 * FS):int(0.9 * FS)]
                h1_noise_B = h1_ts[int(1.0 * FS):int(1.9 * FS)]
                l1_noise_B = l1_ts[int(1.0 * FS):int(1.9 * FS)]
                
                _, c_noise_A = coherence(h1_noise_A, l1_noise_A, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
                f_bin, c_noise_B = coherence(h1_noise_B, l1_noise_B, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
                
                delta_c = c_noise_B - c_noise_A
                
                bin_mask = (f_bin >= TARGET_LOW) & (f_bin <= TARGET_HIGH)
                f_bin_masked = f_bin[bin_mask]
                c_noise_B_masked = c_noise_B[bin_mask]
                delta_c_masked = delta_c[bin_mask]
                
                max_idx = np.argmax(delta_c_masked)
                f_peak = f_bin_masked[max_idx]
                max_delta = delta_c_masked[max_idx]
                max_post = c_noise_B_masked[max_idx]
                
                scalar_kls = np.log(1 + f_peak) / np.log(K_GEO)
                
                record = {
                    "source": "LIGO_CONTROL_V6",
                    "domain": DOMAIN,
                    "id": event,
                    "lane1_pass": True,
                    "lane2_corroborated": False, # Ignored for noise control
                    "f_peak_coherence_hz": float(f_peak),
                    "coherence_excess_peak": float(max_delta),
                    "coherence_post": float(max_post),
                    "scalar_kls": float(scalar_kls),
                    "klghs_excluded": False,
                    "klghs_exclusion_reason": None
                }
                out_f.write(json.dumps(record) + '\n')
                valid_primary += 1
                    
            except Exception as e:
                record = {
                    "source": "LIGO_CONTROL_V6", "domain": DOMAIN, "id": event, 
                    "lane1_pass": False, "lane2_corroborated": False, 
                    "f_peak_coherence_hz": 0.0, "coherence_excess_peak": 0.0, "coherence_post": 0.0,
                    "scalar_kls": 0.0, "klghs_excluded": True, "klghs_exclusion_reason": str(e)
                }
                out_f.write(json.dumps(record) + '\n')
                excluded_records += 1

    print(f"\n[+] NOISE CONTROL LAKE BUILD COMPLETE.")
    print(f"[*] Total Base Events Processed: {valid_primary + excluded_records}")
    print(f"[+] VALID NOISE RECORDS ADMITTED: {valid_primary}")
    print(f"[+] Lake written to {OUTPUT_JSONL}")

if __name__ == "__main__":
    build_noise_control_lake()