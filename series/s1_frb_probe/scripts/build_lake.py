import json
import os
import math

# Toolbelt Architecture Pathing
INPUT_JSON = "../lake/chime_live_data.json"
OUTPUT_JSONL = "../lake/l3_frb_structural.jsonl"
DOMAIN_NAME = "frb_structural"
MIN_DM_THRESHOLD = 10.0 # Pre-registered constraint: exclude local foreground

def build_frb_structural_lake():
    print(f"[*] Building {DOMAIN_NAME} lake for Probe 1...")
    
    if not os.path.exists(INPUT_JSON):
        print(f"[!] ERROR: {INPUT_JSON} not found. Awaiting data pull.")
        return

    with open(INPUT_JSON, 'r') as f:
        try:
            raw_data = json.load(f)
        except json.JSONDecodeError:
            print("[!] ERROR: Invalid JSON format in source file.")
            return

    initial_count = len(raw_data)
    filtered_count = 0
    dropped_foreground = 0
    dropped_nulls = 0

    with open(OUTPUT_JSONL, 'w') as out_f:
        for row in raw_data:
            tns_name = row.get("tns_name", "UNKNOWN")
            
            # Prefer best-fit DM, fallback to bonsai_dm
            dm_val = row.get("dm_fitb")
            if dm_val is None or math.isnan(dm_val):
                dm_val = row.get("bonsai_dm")
            
            if dm_val is None or math.isnan(dm_val):
                dropped_nulls += 1
                continue
                
            dm_val = float(dm_val)

            # Enforce the > 10 pc/cm3 rule
            if dm_val < MIN_DM_THRESHOLD:
                dropped_foreground += 1
                continue

            record = {
                "source": "chime_frb_cat1",
                "domain": DOMAIN_NAME,
                "id": tns_name,
                "dm": dm_val
            }
            out_f.write(json.dumps(record) + '\n')
            filtered_count += 1

    print(f"[*] Raw records: {initial_count}")
    print(f"[*] Dropped foreground (DM < 10): {dropped_foreground}")
    print(f"[*] Dropped nulls/NaNs: {dropped_nulls}")
    print(f"[+] Valid cosmological records written: {filtered_count}")
    print(f"[+] Successfully generated {OUTPUT_JSONL}")

if __name__ == "__main__":
    build_frb_structural_lake()