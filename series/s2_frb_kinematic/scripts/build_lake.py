import json
import os

# Toolbelt Architecture Pathing
INPUT_JSON = "../lake/chime_live_data.json"
OUTPUT_JSONL = "../lake/l4_frb_kinematic.jsonl"
DOMAIN_NAME = "frb_kinematic"

# [ATLAS DIRECTIVE APPLIED]: Pre-registered kinematic window limits
MIN_DT = 0.1       # Exclude simultaneous multi-component bursts
MAX_DT = 86400.0   # 24 Hours. Exclude macro-orbit/activity gaps.

def build_frb_kinematic_lake_v2():
    print(f"[*] Building {DOMAIN_NAME} lake for Probe 1 (V2 Strict Filter)...")
    
    if not os.path.exists(INPUT_JSON):
        print(f"[!] ERROR: {INPUT_JSON} not found. Awaiting data pull.")
        return

    with open(INPUT_JSON, 'r') as f:
        raw_data = json.load(f)

    # 1. Group bursts by Repeater Source
    repeaters = {}
    for row in raw_data:
        rep_name = row.get("repeater_name", "").strip()
        mjd = row.get("mjd_400")
        
        if rep_name and mjd is not None:
            if rep_name not in repeaters:
                repeaters[rep_name] = []
            repeaters[rep_name].append({
                "tns_name": row.get("tns_name"),
                "mjd": float(mjd)
            })

    # 2. Sort chronologically and calculate Delta T
    valid_intervals = 0
    dropped_gaps = 0
    
    with open(OUTPUT_JSONL, 'w') as out_f:
        for rep_name, bursts in repeaters.items():
            if len(bursts) < 2:
                continue 
                
            bursts.sort(key=lambda x: x["mjd"])
            
            for i in range(1, len(bursts)):
                prev_burst = bursts[i-1]
                curr_burst = bursts[i]
                
                delta_t_seconds = (curr_burst["mjd"] - prev_burst["mjd"]) * 86400.0
                
                # Apply the Atlas Pre-Registered Filter
                if MIN_DT < delta_t_seconds <= MAX_DT: 
                    record = {
                        "source": "chime_frb_cat1",
                        "domain": DOMAIN_NAME,
                        "id": f"{rep_name}_{prev_burst['tns_name']}_to_{curr_burst['tns_name']}",
                        "delta_t": delta_t_seconds
                    }
                    out_f.write(json.dumps(record) + '\n')
                    valid_intervals += 1
                else:
                    dropped_gaps += 1

    print(f"[*] Total unique repeaters parsed: {len(repeaters)}")
    print(f"[*] Dropped {dropped_gaps} intervals (Activity Gaps > 24hr or < 0.1s)")
    print(f"[+] Valid Pure Kinematic intervals extracted: {valid_intervals}")
    print(f"[+] Successfully generated {OUTPUT_JSONL}")

if __name__ == "__main__":
    build_frb_kinematic_lake_v2()