import json
from gwosc.datasets import find_datasets, event_detectors
import warnings

warnings.filterwarnings("ignore")

TARGET_CATALOGS = ['GWTC-1-confident', 'GWTC-2', 'GWTC-2.1-confident', 'GWTC-3-confident']

def audit_multidetector_availability():
    print("[*] LYRA DIRECTIVE: Auditing Multi-Detector Availability across GWTC 1-3...")
    
    raw_events = []
    for catalog in TARGET_CATALOGS:
        raw_events.extend(find_datasets(type='events', catalog=catalog))

    # Deduplicate to just the base event name (e.g., GW150914)
    unique_events = sorted(list(set([e.split('-')[0] for e in raw_events])))
    print(f"[*] Total unique physical mergers identified: {len(unique_events)}\n")

    matrix = {
        "exactly_1": 0,
        "exactly_2": 0,
        "exactly_3": 0,
        "exactly_4": 0,
        "h1_l1_pairs": 0,
        "rescued_by_v1_k1": 0,
        "v1_participations": 0,
        "k1_participations": 0
    }

    for event in unique_events:
        try:
            # Query GWOSC API for which detectors actively recorded this specific event
            det_list = list(event_detectors(event))
            count = len(det_list)
            
            if count == 1: matrix["exactly_1"] += 1
            elif count == 2: matrix["exactly_2"] += 1
            elif count == 3: matrix["exactly_3"] += 1
            elif count == 4: matrix["exactly_4"] += 1

            has_h1 = 'H1' in det_list
            has_l1 = 'L1' in det_list
            has_v1 = 'V1' in det_list
            has_k1 = 'K1' in det_list
            
            if has_v1: matrix["v1_participations"] += 1
            if has_k1: matrix["k1_participations"] += 1
            
            # Did it have the baseline H1-L1 pair?
            if has_h1 and has_l1:
                matrix["h1_l1_pairs"] += 1
            # If it missed H1 or L1, does Virgo or KAGRA step in to provide a pair? (e.g., H1-V1)
            elif count >= 2:
                matrix["rescued_by_v1_k1"] += 1

        except Exception as e:
            print(f"[!] Warning: Could not resolve detectors for {event}: {e}")

    # Generate Atlas's Required Report
    print("==================================================")
    print("--- DELIVERABLE 1: DETECTOR OVERLAP MATRIX ---")
    print("==================================================")
    print(f"[*] Total Events with Exactly 2 Detectors: {matrix['exactly_2']}")
    print(f"[*] Total Events with Exactly 3 Detectors: {matrix['exactly_3']}")
    print(f"[*] Total Events with Exactly 4 Detectors: {matrix['exactly_4']}")
    print("-" * 50)
    print(f"[*] Total Virgo (V1) Participations: {matrix['v1_participations']}")
    print(f"[*] Total KAGRA (K1) Participations: {matrix['k1_participations']}")
    print("-" * 50)
    print(f"[>] Baseline H1+L1 Pairs (Our V9 Lake):    {matrix['h1_l1_pairs']}")
    print(f"[>] Events RESCUED by V1/K1 (New Events):  {matrix['rescued_by_v1_k1']}")
    print(f"[+] THEORETICAL MAX PAIRED EVENTS (N):     {matrix['h1_l1_pairs'] + matrix['rescued_by_v1_k1']}")
    print("==================================================")

if __name__ == "__main__":
    audit_multidetector_availability()