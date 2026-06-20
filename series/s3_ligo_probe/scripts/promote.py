import os
import shutil

# The file we just built and validated
SOURCE_FILE = "../lake/ligo_coherence.jsonl"
SOURCE_PATH = os.path.abspath(SOURCE_FILE)

# The EXACT name the KLGHS engine expects based on volumes.json
PROMOTED_FILENAME = "s3_ligo_coherence_promoted.jsonl"

def find_project_root():
    """Climbs up the directory tree to find the KishLattice Star root."""
    current_dir = os.path.abspath(os.path.dirname(__file__))
    while current_dir:
        # Check if we hit the root by looking for the engine directory
        if os.path.exists(os.path.join(current_dir, "engine", "run_pipeline.py")):
            return current_dir
        
        parent = os.path.dirname(current_dir)
        if parent == current_dir: # Hit the top of the drive
            break
        current_dir = parent
    return None

def promote():
    print(f"[*] ATLAS DIRECTIVE: Promoting to Master Ledger...")
    
    if not os.path.exists(SOURCE_PATH):
        print(f"[!] ERROR: Source file {SOURCE_PATH} not found.")
        return

    root_dir = find_project_root()
    if not root_dir:
        print("[!] ERROR: Could not locate the KishLattice Star root directory.")
        print("    Ensure this script is running somewhere inside the project folder.")
        return

    # Construct the exact path to inputs_promoted
    dest_dir = os.path.join(root_dir, "lakes", "inputs_promoted")
    os.makedirs(dest_dir, exist_ok=True)
    
    dest_path = os.path.join(dest_dir, PROMOTED_FILENAME)

    # Perform the copy and rename
    shutil.copy2(SOURCE_PATH, dest_path)

    print("==================================================")
    print(f"[+] PROMOTION SUCCESSFUL")
    print(f"  -> Source:      {SOURCE_PATH}")
    print(f"  -> Destination: {dest_path}")
    print("==================================================")
    print("[*] The KLGHS Engine is now armed. Clear to run_pipeline.py.")

if __name__ == "__main__":
    promote()