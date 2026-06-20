import os
import json
import glob
import numpy as np
import warnings
from gwpy.timeseries import TimeSeries
from scipy.signal import welch, find_peaks, butter, sosfiltfilt

warnings.filterwarnings("ignore")

DATA_DIR = "../lake/strain_data/"
# NEW OUTPUT LAKE FOR THE CONTROL
OUTPUT_JSONL = "../lake/l1_ligo_premerger_control.jsonl"
DOMAIN = "ligo_kinematic_control"
FS = 16384 
K_GEO = 16.0 / np.pi

def is_masked(f_hz, run_prefix):
    for harmonic in range(60, int(FS/2), 60):
        if abs(f_hz - harmonic) <= 2.0:
            return True, f"instrumental_line_mask_60Hz_harmonic_{harmonic}"
    if run_prefix in ['GW15', 'GW17']: 
        for mode in range(330, 350, 10):
            if abs(f_hz - mode) <= 5.0:
                return True, "instrumental_line_mask_O1O2_violin"
    else: 
        for mode in range(500, 510, 2):
            if abs(f_hz - mode) <= 5.0:
                return True, "instrumental_line_mask_O3_violin"
    return False, None

def apply_qnm_highpass_suppression(data, fs):
    nyq = 0.5 * fs
    sos = butter(5, 1000.0 / nyq, btype='high', analog=False, output='sos')
    return sosfiltfilt(sos, data)

def execute_control_pipeline():
    print(f"[*] MONDY DIRECTIVE: Initiating PRE-MERGER Control Pipeline (Unwhitened)...")
    files = glob.glob(os.path.join(DATA_DIR, "*.hdf5"))
    if not files: return

    valid_records = 0
    masked_records = 0
    
    with open(OUTPUT_JSONL, 'w') as out_f:
        for filepath in files:
            filename = os.path.basename(filepath)
            parts = filename.split('_')
            event_name = parts[0]
            detector = parts[1][:2] 
            
            try:
                ts = TimeSeries.read(filepath, format='hdf5')
                h_full = ts.value
                
                h_res_full = apply_qnm_highpass_suppression(h_full, FS)
                
                # [MONDY'S CONTROL FIX]: Slice the PRE-MERGER window (t0 - 1.9s to t0 - 1.0s)
                # t0 is at 2.0s in our 4-second file.
                # 2.0 - 1.9 = 0.1s.  2.0 - 1.0 = 1.0s.
                h_res_window = h_res_full[int(0.1 * FS) : int(1.0 * FS)]
                
                nperseg = int(FS / 10) 
                freqs, psd = welch(h_res_window, fs=FS, window='hann', nperseg=nperseg, noverlap=nperseg//2)
                
                valid_idx = np.where(freqs > 1100.0)[0]
                f_valid = freqs[valid_idx]
                psd_valid = psd[valid_idx]

                peaks, properties = find_peaks(psd_valid, prominence=0)
                if len(peaks) == 0: continue
                    
                global_peak_idx = peaks[np.argmax(properties["prominences"])]
                f_peak = f_valid[global_peak_idx]
                amp_peak = psd_valid[global_peak_idx]
                
                is_excluded, exclusion_reason = is_masked(f_peak, event_name[:4])
                scalar_kls = np.log(1 + f_peak) / np.log(K_GEO)
                
                record = {
                    "source": "LIGO_GWTC3_16kHz_PREMERGER",
                    "domain": DOMAIN,
                    "id": f"{event_name}_{detector}_control",
                    "f_peak_hz": float(f_peak),
                    "psd_amplitude": float(amp_peak),
                    "scalar_kls": float(scalar_kls),
                    "klghs_excluded": bool(is_excluded),
                    "klghs_exclusion_reason": exclusion_reason
                }
                out_f.write(json.dumps(record) + '\n')
                
                if is_excluded: masked_records += 1
                else: valid_records += 1
                    
            except Exception as e:
                pass

    print(f"\n[+] CONTROL PROCESSING COMPLETE.")
    print(f"[*] Clean Pre-Merger Peaks Surviving: {valid_records}")
    print(f"[+] Control Lake written to {OUTPUT_JSONL}")

if __name__ == "__main__":
    execute_control_pipeline()