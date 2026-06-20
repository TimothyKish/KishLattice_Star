import json
import os

# Toolbelt Architecture Pathing
LAKE_PATH = "../lake/l3_frb_structural.jsonl"
MIN_DM_THRESHOLD = 10.0

def validate_lake():
    print(f"[*] Commencing Vol 12 strict audit of {LAKE_PATH}")
    
    if not os.path.exists(LAKE_PATH):
        print(f"[!] ERROR: Lake not found at {LAKE_PATH}")
        return False

    records = []
    with open(LAKE_PATH, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError:
                print(f"[!] ERROR: Malformed JSON on line {line_num}")
                return False

    if not records:
        print("[!] ERROR: Lake is empty.")
        return False

    dm_values = []
    for i, rec in enumerate(records):
        # Schema enforcement
        if "dm" not in rec or "id" not in rec or "domain" not in rec:
            print(f"[!] ERROR: Malformed schema in record {i}")
            return False
        
        # Rule enforcement
        if rec["dm"] < MIN_DM_THRESHOLD:
            print(f"[!] ERROR: Audit failed. Record {rec['id']} violates DM >= {MIN_DM_THRESHOLD} rule.")
            return False
            
        dm_values.append(rec["dm"])

    print(f"[+] Schema and Rule validation passed.")
    print(f"[+] Record count: {len(records)}")
    print(f"[+] DM Range: {min(dm_values):.2f} to {max(dm_values):.2f} pc/cm3")
    print(f"[+] Status: GREEN FOR PROMOTION")
    return True

if __name__ == "__main__":
    validate_lake()