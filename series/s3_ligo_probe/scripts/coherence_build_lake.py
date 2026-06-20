import os
import json
import glob
import numpy as np
import warnings
from gwpy.timeseries import TimeSeries
from scipy.signal import coherence

warnings.filterwarnings("ignore")

# --- KLGHS VOL 12 PRE-REGISTERED PARAMETERS (V6 UN-GATED) ---
DATA_DIR = "../lake/strain_data/"
OUTPUT_JSONL = "../lake/ligo_coherence.jsonl"
DOMAIN = "ligo_coherence"

FS = 16384
WINDOW_LEN = 0.1
OVERLAP = 0.5
NPERSEG = int(FS * WINDOW_LEN)      
NOVERLAP = int(NPERSEG * OVERLAP)   
NFFT = 4096                         

# CORROBORATION PASS THRESHOLDS (VIRGO EMPIRICAL - NO ADMISSION GATING)
C_THRESH_VIRGO = 0.0847                 
DELTA_C_THRESH_VIRGO = 0.03               

TARGET_LOW = 2865.5
TARGET_HIGH = 5546.0
K_GEO = 16.0 / np.pi

def execute_v6_coherence():
    print(f"[*] ATLAS DIRECTIVE: Initiating V6 UN-GATED CROSS-SPECTRAL Coherence Pipeline...")
    
    events = {}
    for f in glob.glob(os.path.join(DATA_DIR, "*.hdf5")):
        base = os.path.basename(f)
        parts = base.rsplit('_', 1)
        if len(parts) < 2: continue
        event = parts[0]
        det = parts[1][:2]
        if event not in events: events[event] = {}
        events[event][det] = f

    # The N=86 Baseline: Must have H1 and L1 to even be evaluated
    eligible_events = {e: files for e, files in events.items() if 'H1' in files and 'L1' in files}
    print(f"[*] Found {len(eligible_events)} eligible H1-L1 base events (N Ceiling).")
    
    valid_primary = 0
    valid_3det_corroborated = 0
    excluded_records = 0
    
    with open(OUTPUT_JSONL, 'w') as out_f:
        for event, files in eligible_events.items():
            lane2_corroborated = False
            is_excluded = False
            reason = None
            
            try:
                # 1. Load Data
                h1_ts = TimeSeries.read(files['H1'], format='hdf5').value
                l1_ts = TimeSeries.read(files['L1'], format='hdf5').value
                
                # Check for offline primary detectors
                if np.isnan(h1_ts).any() or np.isnan(l1_ts).any():
                    is_excluded = True
                    reason = "primary_detector_offline"
                    raise ValueError(reason)

                # Slicing
                pre_start, pre_end = int(0.0 * FS), int(1.9 * FS)
                post_start, post_end = int(2.1 * FS), int(3.0 * FS)
                
                h1_pre, h1_post = h1_ts[pre_start:pre_end], h1_ts[post_start:post_end]
                l1_pre, l1_post = l1_ts[pre_start:pre_end], l1_ts[post_start:post_end]
                
                # LANE 1: PRIMARY PASS (H1-L1) - UNGATED
                f_pre, c_pre = coherence(h1_pre, l1_pre, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
                f_post, c_post = coherence(h1_post, l1_post, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
                delta_c = c_post - c_pre
                
                bin_mask = (f_post >= TARGET_LOW) & (f_post <= TARGET_HIGH)
                f_bin = f_post[bin_mask]
                c_post_bin = c_post[bin_mask]
                delta_c_bin = delta_c[bin_mask]
                
                # Extract the peak frequency, regardless of amplitude
                max_idx = np.argmax(delta_c_bin)
                f_peak = f_bin[max_idx]
                max_delta = delta_c_bin[max_idx]
                max_post = c_post_bin[max_idx]
                
                valid_primary += 1
                
                # LANE 2: CORROBORATION PASS (VIRGO)
                if 'V1' in files:
                    v1_ts = TimeSeries.read(files['V1'], format='hdf5').value
                    if not np.isnan(v1_ts).any():
                        v1_pre, v1_post = v1_ts[pre_start:pre_end], v1_ts[post_start:post_end]
                        
                        _, c_h1v1_pre = coherence(h1_pre, v1_pre, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
                        _, c_h1v1_post = coherence(h1_post, v1_post, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
                        delta_h1v1 = c_h1v1_post - c_h1v1_pre
                        
                        _, c_l1v1_pre = coherence(l1_pre, v1_pre, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
                        _, c_l1v1_post = coherence(l1_post, v1_post, fs=FS, window='hann', nperseg=NPERSEG, noverlap=NOVERLAP, nfft=NFFT)
                        delta_l1v1 = c_l1v1_post - c_l1v1_pre
                        
                        # Check at the EXACT peak frequency found by H1-L1
                        v1_h1_post_peak = c_h1v1_post[bin_mask][max_idx]
                        v1_h1_delta_peak = delta_h1v1[bin_mask][max_idx]
                        
                        v1_l1_post_peak = c_l1v1_post[bin_mask][max_idx]
                        v1_l1_delta_peak = delta_l1v1[bin_mask][max_idx]
                        
                        if (v1_h1_post_peak > C_THRESH_VIRGO and v1_h1_delta_peak > DELTA_C_THRESH_VIRGO) or \
                           (v1_l1_post_peak > C_THRESH_VIRGO and v1_l1_delta_peak > DELTA_C_THRESH_VIRGO):
                            lane2_corroborated = True
                            valid_3det_corroborated += 1

                scalar_kls = np.log(1 + f_peak) / np.log(K_GEO)
                
                record = {
                    "source": "LIGO_GWTC3_COHERENCE_V6",
                    "domain": DOMAIN,
                    "id": event,
                    "lane1_pass": True, # All clean H1/L1 events pass in V6
                    "lane2_corroborated": lane2_corroborated,
                    "f_peak_coherence_hz": float(f_peak),
                    "coherence_excess_peak": float(max_delta),
                    "coherence_post": float(max_post),
                    "scalar_kls": float(scalar_kls),
                    "klghs_excluded": False,
                    "klghs_exclusion_reason": None
                }
                out_f.write(json.dumps(record) + '\n')
                    
            except Exception as e:
                is_excluded = True
                record = {
                    "source": "LIGO_GWTC3_COHERENCE_V6", "domain": DOMAIN, "id": event, 
                    "lane1_pass": False, "lane2_corroborated": False, 
                    "f_peak_coherence_hz": 0.0, "coherence_excess_peak": 0.0, "coherence_post": 0.0,
                    "scalar_kls": 0.0, "klghs_excluded": True, "klghs_exclusion_reason": str(e)
                }
                out_f.write(json.dumps(record) + '\n')
                excluded_records += 1

    print(f"\n[+] V6 UN-GATED COHERENCE COMPLETE.")
    print(f"[*] Total Base Events Processed: {valid_primary + excluded_records}")
    print(f"--------------------------------------------------")
    print(f"[+] PRIMARY PASS (H1-L1 ONLY):      {valid_primary} events")
    print(f"[+] 3-DETECTOR CORROBORATED (V1):   {valid_3det_corroborated} events")
    print(f"--------------------------------------------------")
    print(f"[+] Lake written to {OUTPUT_JSONL}")

if __name__ == "__main__":
    execute_v6_coherence()