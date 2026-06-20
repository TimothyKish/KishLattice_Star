import os
import warnings
from gwpy.timeseries import TimeSeries
from gwosc.datasets import find_datasets, event_detectors, event_gps

warnings.filterwarnings("ignore")

DATA_DIR = "../lake/strain_data/"
os.makedirs(DATA_DIR, exist_ok=True)
TARGET_CATALOGS = ['GWTC-1-confident', 'GWTC-2', 'GWTC-2.1-confident', 'GWTC-3-confident']

def fetch_unbiased_virgo_catalog():
    print("[*] LYRA DIRECTIVE: Fetching Unbiased 3-Detector Catalog (H1, L1, V1)...")
    
    raw_events = []
    for catalog in TARGET_CATALOGS:
        raw_events.extend(find_datasets(type='events', catalog=catalog))
    unique_events = sorted(list(set([e.split('-')[0] for e in raw_events])))
    
    target_events = []
    for event in unique_events:
        try:
            dets = list(event_detectors(event))
            if 'H1' in dets and 'L1' in dets and 'V1' in dets:
                target_events.append(event)
        except: pass

    print(f"[*] Identified {len(target_events)} global events with H1, L1, and V1.")
    
    downloads = 0
    for event in target_events:
        gps = event_gps(event)
        for det in ['H1', 'L1', 'V1']:
            filename = os.path.join(DATA_DIR, f"{event}_{det}.hdf5")
            if not os.path.exists(filename):
                print(f"  [+] Downloading {det} for {event} (GPS: {gps})...")
                try:
                    ts = TimeSeries.fetch_open_data(det, gps - 2, gps + 2, sample_rate=16384, cache=True)
                    ts.write(filename, format='hdf5')
                    downloads += 1
                except Exception as e:
                    print(f"      [!] Failed: {e}")

    print(f"\n[+] FETCH COMPLETE. {downloads} missing files downloaded.")

if __name__ == "__main__":
    fetch_unbiased_virgo_catalog()