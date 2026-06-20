import os
import warnings
from gwosc.datasets import find_datasets, event_gps
from gwpy.timeseries import TimeSeries

# Suppress LIGO observatory metadata warnings to keep the terminal clean
warnings.filterwarnings("ignore")

# Configuration
DOWNLOAD_DIR = "../lake/strain_data/"
SAMPLING_RATE = 16384 # Mandatory 16 kHz
DETECTORS = ['H1', 'L1']
WINDOW_RADIUS = 2.0 # 2 seconds before and 2 seconds after the merger

TARGET_CATALOGS = ['GWTC-1-confident', 'GWTC-2', 'GWTC-2.1-confident', 'GWTC-3-confident']

def pull_spacetime_fabric_surgically():
    print("[*] ATLAS DIRECTIVE: Initiating Surgical 16 kHz Strain Extraction...")
    
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    # 1. Gather all confident events
    raw_events = []
    for catalog in TARGET_CATALOGS:
        raw_events.extend(find_datasets(type='events', catalog=catalog))
        
    # Deduplicate base event names (e.g., GW150914-v1 and GW150914-v3 become just GW150914)
    unique_events = sorted(list(set([e.split('-')[0] for e in raw_events])))
    print(f"[*] Identified {len(unique_events)} unique physical mergers across GWTC-1/2/3.")

    successful_pulls = 0
    missing_data = []

    for event in unique_events:
        print(f"\n[*] Target: {event}")
        
        try:
            # Resolve the exact GPS time of the merger
            gps_time = event_gps(event)
            start_time = gps_time - WINDOW_RADIUS
            end_time = gps_time + WINDOW_RADIUS
        except Exception as e:
            print(f"[!] Could not resolve GPS time for {event}. Skipping.")
            continue

        for det in DETECTORS:
            dest_path = os.path.join(DOWNLOAD_DIR, f"{event}_{det}_16k.hdf5")
            
            if os.path.exists(dest_path):
                print(f"    [-] {det}: Already exists on disk. Skipping.")
                successful_pulls += 1
                continue
                
            print(f"    [>] Streaming {det} 16 kHz data from continuous archive...")
            try:
                # gwpy reaches into the archive and extracts only the 4 seconds we need
                ts = TimeSeries.fetch_open_data(
                    det, 
                    start_time, 
                    end_time, 
                    sample_rate=SAMPLING_RATE,
                    verbose=False
                )
                
                # Save the surgical slice to our local lake
                ts.write(dest_path, format='hdf5')
                print(f"    [+] {det}: Secured.")
                successful_pulls += 1
                
            except Exception as e:
                # This catches times when a detector was physically offline during the merger
                print(f"    [!] {det}: Offline or data unavailable ({e})")
                missing_data.append(f"{event}_{det}")

    print("\n" + "="*50)
    print(f"[+] DATA ARCHEOLOGY COMPLETE.")
    print(f"[+] Successfully extracted {successful_pulls} surgical strain files.")
    if missing_data:
        print(f"[!] The following {len(missing_data)} event/detector combinations were physically unavailable:")
        for m in missing_data:
            print(f"    - {m}")
        print("[!] These will be documented as anticipated exclusions.")
    print("="*50)

if __name__ == "__main__":
    pull_spacetime_fabric_surgically()