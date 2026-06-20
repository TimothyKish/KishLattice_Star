import os
import warnings
from gwpy.timeseries import TimeSeries
from gwosc.datasets import event_gps

warnings.filterwarnings("ignore")

DATA_DIR = "../lake/strain_data/"
os.makedirs(DATA_DIR, exist_ok=True)

# Three classic multi-detector events
SAMPLE_EVENTS = ['GW170814', 'GW190425', 'GW190521']

def fetch_virgo_samples():
    print("[*] LYRA DIRECTIVE: Fetching V1 (Virgo) 16kHz strain for hardware audit...")
    
    for event in SAMPLE_EVENTS:
        try:
            gps = event_gps(event)
            print(f"\n  [+] Processing {event} (GPS: {gps})")
            
            for det in ['H1', 'L1', 'V1']:
                filename = os.path.join(DATA_DIR, f"{event}_{det}.hdf5")
                if not os.path.exists(filename):
                    print(f"      -> Downloading {det}...")
                    # 4 second window: t0 - 2s to t0 + 2s
                    ts = TimeSeries.fetch_open_data(det, gps - 2, gps + 2, sample_rate=16384, cache=True)
                    ts.write(filename, format='hdf5')
                else:
                    print(f"      -> {det} already cached.")
        except Exception as e:
            print(f"  [!] Failed to fetch {event}: {e}")

    print("\n[+] FETCH COMPLETE. The audit is ready to run.")

if __name__ == "__main__":
    fetch_virgo_samples()