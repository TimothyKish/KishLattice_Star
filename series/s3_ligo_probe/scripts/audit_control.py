import json
import os
import math
from collections import Counter

LAKE_PATH = "../lake/l1_ligo_premerger_control.jsonl"

def print_audit():
    print(f"[*] MONDY DIRECTIVE: Compiling PRE-MERGER Peak Distribution...")
    if not os.path.exists(LAKE_PATH): return

    registers = []
    total_clean = 0
    in_target = 0

    with open(LAKE_PATH, 'r') as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("klghs_exclusion_reason") and "instrumental" in rec.get("klghs_exclusion_reason", ""):
                continue
                
            total_clean += 1
            scalar = rec["scalar_kls"]
            register = int(round(scalar * math.pi))
            registers.append(register)
            if 15.5 <= (scalar * math.pi) <= 16.5:
                in_target += 1

    print("\n--- PRE-MERGER NOISE DISTRIBUTION (Control) ---")
    counts = Counter(registers)
    for reg in range(12, 21):
        count = counts.get(reg, 0)
        bar = "█" * count
        print(f"Register {reg:2d} | {bar} ({count})")
        
    print("-" * 56)
    print(f"Total Clean Physical Peaks: {total_clean}")
    if total_clean > 0:
        print(f"Natural Hit Rate (Reg 16): {(in_target/total_clean)*100:.1f}%\n")

if __name__ == "__main__":
    print_audit()