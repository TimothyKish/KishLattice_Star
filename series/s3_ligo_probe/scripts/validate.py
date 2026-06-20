import os
import json

# Relative to the scripts folder
LAKE_DIR = "../lake/"
TARGET_FILE = "ligo_coherence.jsonl"
FILE_PATH = os.path.abspath(os.path.join(LAKE_DIR, TARGET_FILE))

REQUIRED_FIELDS = [
    "source", "domain", "id", "lane1_pass", "lane2_corroborated",
    "f_peak_coherence_hz", "coherence_excess_peak", "coherence_post",
    "scalar_kls", "klghs_excluded", "klghs_exclusion_reason"
]

def validate():
    print(f"[*] MONDY DIRECTIVE: Validating {TARGET_FILE} Schema...")
    if not os.path.exists(FILE_PATH):
        print(f"[!] ERROR: {FILE_PATH} not found. Did you run coherence_build_lake.py?")
        return

    valid = 0
    excluded = 0
    errors = 0

    with open(FILE_PATH, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                record = json.loads(line)
                for field in REQUIRED_FIELDS:
                    if field not in record:
                        print(f"  [!] Record {line_num} missing field: {field}")
                        errors += 1
                        break
                if record.get('klghs_excluded'):
                    excluded += 1
                else:
                    valid += 1
            except json.JSONDecodeError:
                print(f"  [!] Invalid JSON on line {line_num}")
                errors += 1

    print("==================================================")
    print(f"[*] Total Valid Records Admitted:   {valid}")
    print(f"[*] Total Records Excluded:         {excluded}")
    print(f"[*] Total Schema Errors:            {errors}")
    print("==================================================")
    if errors == 0:
        print("[+] VALIDATION PASSED. Clear to promote.")
    else:
        print("[!] VALIDATION FAILED. Fix schema errors before promoting.")

if __name__ == "__main__":
    validate()