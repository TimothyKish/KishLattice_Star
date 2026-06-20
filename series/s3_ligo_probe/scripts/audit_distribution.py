import json
import os
import math
from collections import Counter

LAKE_PATH = "../lake/l1_ligo_ringdown.jsonl"

def print_audit():
    print(f"[*] Compiling Global Peak Distribution across all Registers...")
    
    if not os.path.exists(LAKE_PATH): return

    registers = []
    total_clean = 0
    in_target = 0

    with open(LAKE_PATH, 'r') as f:
        for line in f:
            rec = json.loads(line)
            # Ignore peaks that hit the known physical hardware bounds
            if rec.get("klghs_exclusion_reason") and "instrumental" in rec.get("klghs_exclusion_reason", ""):
                continue
                
            total_clean += 1
            scalar = rec["scalar_kls"]
            
            # Multiply by Pi to map the scalar back to the N-register space
            register = int(round(scalar * math.pi))
            registers.append(register)
            
            # Target bin is 15.5 to 16.5 in the Pi-scaled space
            if 15.5 <= (scalar * math.pi) <= 16.5:
                in_target += 1

    print("\n--- SPECTRAL PROMINENCE DISTRIBUTION (Pi-Scaled Registers) ---")
    counts = Counter(registers)
    
    for reg in range(12, 21):
        count = counts.get(reg, 0)
        bar = "█" * count
        marker = "<-- 16/\u03C0 TARGET" if reg == 16 else ""
        print(f"Register {reg:2d} | {bar} ({count}) {marker}")
        
    print("-" * 56)
    print(f"Total Clean Physical Peaks: {total_clean}")
    print(f"Peaks naturally landing in 16/\u03C0 bin: {in_target}")
    
    # Safe Math Fix to prevent ZeroDivisionError
    if total_clean > 0:
        print(f"Natural Hit Rate: {(in_target/total_clean)*100:.1f}%\n")
    else:
        print(f"Natural Hit Rate: N/A (0 clean peaks)\n")

if __name__ == "__main__":
    print_audit()