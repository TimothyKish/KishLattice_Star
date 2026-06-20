import json
import os

LAKE_PATH = "../lake/l4_frb_kinematic.jsonl"

def validate_lake():
    print(f"[*] Commencing Vol 12 strict audit of {LAKE_PATH}")
    
    if not os.path.exists(LAKE_PATH):
        print(f"[!] ERROR: Lake not found at {LAKE_PATH}")
        return False

    records = []
    with open(LAKE_PATH, 'r') as f:
        for line in f:
            records.append(json.loads(line))

    if not records:
        print("[!] ERROR: Lake is empty.")
        return False

    dt_values = []
    for i, rec in enumerate(records):
        if "delta_t" not in rec or "id" not in rec or "domain" not in rec:
            print(f"[!] ERROR: Malformed schema in record {i}")
            return False
            
        if rec["delta_t"] <= 0:
            print(f"[!] ERROR: Audit failed. Negative or zero time interval found.")
            return False
            
        dt_values.append(rec["delta_t"])

    print(f"[+] Schema and Rule validation passed.")
    print(f"[+] Record count: {len(records)}")
    print(f"[+] \u0394t Range: {min(dt_values):.2f}s to {max(dt_values):.2f}s")
    print(f"[+] Status: GREEN FOR PROMOTION")
    return True

if __name__ == "__main__":
    validate_lake()