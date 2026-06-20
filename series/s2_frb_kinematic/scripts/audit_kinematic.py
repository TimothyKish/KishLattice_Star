import json
import os

LAKE_PATH = "../lake/l4_frb_kinematic.jsonl"

def audit_timing_windows():
    print(f"[*] Commencing Vol 12 Star Probe Audit on {LAKE_PATH}...")
    
    if not os.path.exists(LAKE_PATH):
        print(f"[!] ERROR: Lake not found at {LAKE_PATH}")
        return

    intervals = []
    with open(LAKE_PATH, 'r') as f:
        for line in f:
            intervals.append(json.loads(line)["delta_t"])

    if not intervals:
        print("[!] Lake is empty.")
        return

    total = len(intervals)

    # Calculate Activity Window Contamination Bins
    fast = sum(1 for dt in intervals if dt <= 60)
    hour = sum(1 for dt in intervals if 60 < dt <= 3600)
    day = sum(1 for dt in intervals if 3600 < dt <= 86400)
    month = sum(1 for dt in intervals if 86400 < dt <= 2592000)
    year = sum(1 for dt in intervals if dt > 2592000)

    print("\n--- \u0394t DISTRIBUTION AUDIT ---")
    print(f"Total Intervals: {total}")
    print(f"Sub-Minute (< 60s):          {fast}   (Pure Kinematic)")
    print(f"Sub-Hour (1m - 1hr):         {hour}   (Pure Kinematic)")
    print(f"Sub-Day (1hr - 24hr):        {day}    (Likely Kinematic)")
    print(f"Multi-Day/Month (1d - 30d):  {month}  (ACTIVITY GAP CONTAMINATION)")
    print(f"Multi-Year (> 30d):          {year}   (MACRO ORBIT CONTAMINATION)")
    print("----------------------------\n")
    print("[!] Atlas requires a strict cutoff threshold to be pre-registered before V2 rebuild.")

if __name__ == "__main__":
    audit_timing_windows()