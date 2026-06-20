import os
import glob
import warnings
from gwpy.timeseries import TimeSeries
from gwosc.datasets import event_gps, event_detectors

warnings.filterwarnings("ignore")

DATA_DIR = "../lake/strain_data/"

def fetch_all_virgo():
    print("[*] LYRA DIRECTIVE: Fetching Full Virgo (V1) Catalog for H1-L1 Pairs...")
    
    # 1. Identify events we already care about (events where we have H1 and L1)
    events = {}
    for f in glob.glob(os.path.join(DATA_DIR, "*.hdf5")):
        base = os.path.basename(f)
        event = base.split('_')[0]
        det = base.split('_')[1][:2]
        if event not in events: events[event] = set()
        events[event].add(det)
        
    eligible_events = [e for e, dets in events.items() if 'H1' in dets and 'L1' in dets]
    print(f"[*] Found {len(eligible_events)} eligible H1-L1 base events.")
    
    downloads = 0
    for event in eligible_events:
        # Check if V1 is actually published for this event
        try:
            available_dets = list(event_detectors(event))
            if 'V1' not in available_dets:
                continue # Virgo was offline or not published, skip
                
            v1_file = os.path.join(DATA_DIR, f"{event}_V1.hdf5")
            if not os.path.exists(v1_file):
                gps = event_gps(event)
                print(f"  [+] Downloading V1 for {event} (GPS: {gps})...")
                # Pull the exact same 4-second window at 16kHz
                ts = TimeSeries.fetch_open_data('V1', gps - 2, gps + 2, sample_rate=16384, cache=True)
                ts.write(v1_file, format='hdf5')
                downloads += 1
            else:
                pass # Already cached
        except Exception as e:
            print(f"  [!] Failed on {event}: {e}")

    print(f"\n[+] FETCH COMPLETE. {downloads} new Virgo files downloaded.")

if __name__ == "__main__":
    fetch_all_virgo()