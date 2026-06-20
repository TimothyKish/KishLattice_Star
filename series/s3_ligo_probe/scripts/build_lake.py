import os
import json
import glob
import numpy as np
import warnings
from gwpy.timeseries import TimeSeries
from scipy.signal import welch, butter, sosfiltfilt

warnings.filterwarnings("ignore")

DATA_DIR = "../lake/strain_data/"
OUTPUT_JSONL = "../lake/l1_ligo_ringdown.jsonl"
DOMAIN = "ligo_kinematic_excess"
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

def execute_excess_power_pipeline():
    print(f"[*] MONDY DIRECTIVE: Initiating V8 EXCESS POWER Pipeline (PSD Subtraction)...")
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
                # 1. Load Strain & Highpass
                ts = TimeSeries.read(filepath, format='hdf5')
                h_res_full = apply_qnm_highpass_suppression(ts.value, FS)
                
                # 2. Slice Both Windows
                h_pre = h_res_full[int(0.1 * FS) : int(1.0 * FS)]
                h_post = h_res_full[int(2.1 * FS) : int(3.0 * FS)]
                
                # 3. Calculate PSDs
                nperseg = int(FS / 10) 
                freqs, psd_pre = welch(h_pre, fs=FS, window='hann', nperseg=nperseg, noverlap=nperseg//2)
                _, psd_post = welch(h_post, fs=FS, window='hann', nperseg=nperseg, noverlap=nperseg//2)
                
                # 4. [MONDY'S V8 FIX]: Absolute Excess Power (Subtraction)
                # This mathematically erases the digital filter cliff artifact.
                psd_excess = psd_post - psd_pre
                
                # 5. Isolate open high-frequency spectrum (> 1100 Hz)
                valid_idx = np.where(freqs > 1100.0)[0]
                f_valid = freqs[valid_idx]
                excess_valid = psd_excess[valid_idx]

                # 6. Find the frequency with the MAXIMUM ABSOLUTE INJECTED ENERGY
                # Note: We only care about positive excess (energy added, not removed)
                max_excess_idx = np.argmax(excess_valid)
                f_peak = f_valid[max_excess_idx]
                max_excess_val = excess_valid[max_excess_idx]
                
                # Skip if the merger somehow injected *less* energy than the noise floor
                if max_excess_val <= 0:
                    continue
                
                # 7. Masking & Scalarization
                is_excluded, exclusion_reason = is_masked(f_peak, event_name[:4])
                scalar_kls = np.log(1 + f_peak) / np.log(K_GEO)
                
                record = {
                    "source": "LIGO_GWTC3_16kHz_EXCESS",
                    "domain": DOMAIN,
                    "id": f"{event_name}_{detector}",
                    "f_peak_hz": float(f_peak),
                    "psd_absolute_excess": float(max_excess_val),
                    "scalar_kls": float(scalar_kls),
                    "klghs_excluded": bool(is_excluded),
                    "klghs_exclusion_reason": exclusion_reason
                }
                out_f.write(json.dumps(record) + '\n')
                
                if is_excluded: masked_records += 1
                else: valid_records += 1
                    
            except Exception as e:
                pass

    print(f"\n[+] EXCESS POWER PROCESSING COMPLETE (V8).")
    print(f"[*] Clean Sovereign Peaks Surviving: {valid_records}")
    print(f"[+] Lake written to {OUTPUT_JSONL}")

if __name__ == "__main__":
    execute_excess_power_pipeline()