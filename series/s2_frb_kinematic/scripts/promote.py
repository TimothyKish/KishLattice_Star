import os
import shutil
import hashlib

SOURCE_PATH = "../lake/l4_frb_kinematic.jsonl"
PROMOTED_DIR = "../../../lakes/inputs_promoted/"

# [ATLAS DIRECTIVE APPLIED]: New naming convention
LAKE_ID = "l4_frb_kinematic"
TARGET_FILENAME = f"{LAKE_ID}_promoted.jsonl"
PROMOTED_PATH = os.path.join(PROMOTED_DIR, TARGET_FILENAME)

def generate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def promote_lake():
    print(f"[*] Executing V2 Promotion Protocol for {LAKE_ID}...")
    if not os.path.exists(SOURCE_PATH): return
    if not os.path.exists(PROMOTED_DIR): os.makedirs(PROMOTED_DIR)

    source_hash = generate_md5(SOURCE_PATH)
    shutil.copy2(SOURCE_PATH, PROMOTED_PATH)
    promoted_hash = generate_md5(PROMOTED_PATH)
    
    if source_hash == promoted_hash:
        print(f"[+] SUCCESS: Lake cleanly promoted.")
        print(f"[+] Target: {PROMOTED_PATH}")
        print(f"[+] MD5 Checksum: {promoted_hash}")
    else:
        print(f"[!] ERROR: Checksum mismatch! Aborting.")
        os.remove(PROMOTED_PATH)

if __name__ == "__main__":
    promote_lake()