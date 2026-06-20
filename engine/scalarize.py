# ==============================================================================
# COPYRIGHT: (c) 2026 KishLattice 16/pi Initiative LLC.
# FOUNDER: Timothy John Kish
#
# LICENSE & TERMS OF USE:
# This software, including the 16/pi kinematic framework and scalarization 
# engines, is open and available for scientific testing, empirical validation, 
# and academic peer review. 
#
# ATTRIBUTION REQUIREMENT:
# Any publication, derivative code, dataset generation, or public distribution 
# relying on this framework must explicitly cite the "KishLattice 16/pi Initiative" 
# and credit Timothy John Kish. 
#
# Commercial utilization, proprietary harvesting, or uncredited reproduction 
# is strictly prohibited without explicit written permission.
# ==============================================================================
# SCRIPT: scalarize.py
# TARGET: Apply domain-native scalarization to all promoted lakes
# AUTHORS: Timothy John Kish
# AUDIT STATUS: Lyra-verified 2026-05-15 (Streaming memory-safe rewrite + Heartbeat)
#
# UPGRADE Vol 11.1: Rule 1.5 — Config-Driven Scalar Dispatch
#   Reads scalarize.json at startup (cached once). All domains defined in
#   scalarize.json now receive correct scalar computation even if no named
#   handler exists in the dispatch table. This fixes:
#     - Broken multi-attribute lakes: k2a-k2d, h1b-h1d, g1a-g1c, galactic_mass,
#       orbital_transit, p_transit
#     - Wrongbox lakes: now run genuine wrong-projection math on real data
#       (log_volumetric, log_inverse) rather than silently returning 0.0
#   Priority: named handlers always win. Config dispatch is the new fallback
#   layer BEFORE the final (0.0, 0.0) return.
# ==============================================================================

#!/usr/bin/env python
import json
import math
import time
from pathlib import Path
from typing import Dict, Any, Iterable

ROOT       = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs"
INPUT_DIR  = ROOT / "lakes" / "inputs_promoted"
OUTPUT_DIR = ROOT / "lakes" / "unified"
HEARTBEAT_PATH = OUTPUT_DIR / "lattice_heartbeat.json"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PI    = math.pi
K_GEO = 16.0 / PI
LOG_K = math.log(K_GEO)

# ==============================================================================
# RULE 1.5: CONFIG-DRIVEN SCALAR DISPATCH
# Loads scalarize.json once at startup and caches it.
# Used as fallback layer in scalarize_record() before returning (0.0, 0.0).
# ==============================================================================

SCALARIZE_CONFIG_PATH = CONFIG_DIR / "scalarize.json"

def _load_scalarize_config():
    """Load scalarize.json once at startup. Returns domain config dict."""
    if not SCALARIZE_CONFIG_PATH.exists():
        print(f"[WARN] scalarize.json not found at {SCALARIZE_CONFIG_PATH}")
        return {}
    try:
        with open(SCALARIZE_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        domains = cfg.get("domains", {})
        print(f"[scalarize.json] Loaded config for {len(domains)} domains.")
        return domains
    except Exception as e:
        print(f"[WARN] Could not load scalarize.json: {e}")
        return {}

# Cached once at module import — not reloaded per record
_SCALARIZE_DOMAIN_CONFIG = _load_scalarize_config()


def scalarize_from_config(record, domain):
    """
    Rule 1.5: Config-driven scalar dispatch.

    Reads the domain entry from the cached scalarize.json config, extracts
    the specified field from the record, and applies the specified formula.

    Formula types (matching scalarize.json spec):
      log_standard:   log(1 + x/x0) / log(k_geo)   — standard positive measurement
      log_inverse:    log(1 + x0/x) / log(k_geo)   — inverse (wrong projection for wrongboxes)
      log_ratio:      log(x/x0) / log(k_geo)        — ratio without offset
      log_volumetric: log(1 + x^3) / log(k_geo)     — cubic transform (wrong projection)

    The wrongbox domains use log_volumetric or log_inverse intentionally:
      orbital_wrongbox:   period_days cubed    — geometrically wrong for a 1D period
      kinematic_wrongbox: v_perp cubed         — geometrically wrong for a 1D velocity
      stellar_wrongbox:   P0_ms inverted       — geometrically wrong for a period
      materials_wrongbox: volume log_standard  — the field itself is already 3D

    Returns (scalar_kls, scalar_klc) — both set to the same computed scalar.
    Returns (0.0, 0.0) only if domain not in config, field missing, or invalid.
    """
    cfg = _SCALARIZE_DOMAIN_CONFIG.get(domain)
    if cfg is None:
        return (0.0, 0.0)

    field        = cfg.get("field")
    formula_type = cfg.get("formula_type", "log_standard")
    x0           = float(cfg.get("x0", 1.0))

    if not field:
        return (0.0, 0.0)

    # Field extraction: check top-level record, then _raw_payload, then payload
    raw_val = (
        record.get(field)
        or (record.get("_raw_payload") or {}).get(field)
        or (record.get("payload") or {}).get(field)
    )

    if raw_val is None:
        return (0.0, 0.0)

    try:
        x = float(raw_val)
    except (TypeError, ValueError):
        return (0.0, 0.0)

    # Negative values: take absolute (physical magnitudes are always positive)
    if x < 0:
        x = abs(x)

    # Apply the formula
    try:
        if formula_type == "log_standard":
            # Standard: log(1 + x/x0) / log(k_geo)
            sc = math.log(1.0 + x / x0) / LOG_K

        elif formula_type == "log_inverse":
            # Inverse: log(1 + x0/x) / log(k_geo)
            # Used in wrongboxes: inverts a quantity that should not be inverted.
            # Will produce real non-zero scalars. Their harmonic structure (or lack
            # thereof) is the physical test.
            if x == 0:
                return (0.0, 0.0)
            sc = math.log(1.0 + x0 / x) / LOG_K

        elif formula_type == "log_ratio":
            # Ratio: log(x/x0) / log(k_geo)
            if x <= 0 or x0 <= 0:
                return (0.0, 0.0)
            sc = math.log(x / x0) / LOG_K

        elif formula_type == "log_volumetric":
            # Volumetric (cubic): log(1 + x^3) / log(k_geo)
            # Used in wrongboxes: cubes a 1D quantity (period, velocity) to apply
            # a 3D volumetric projection. Deliberately wrong geometry.
            # Will produce real non-zero scalars. Their harmonic structure (or lack
            # thereof) is the physical test.
            x3 = x ** 3
            if not math.isfinite(x3):
                # Overflow on very large values — scale down and recompute
                sc = math.log(x) * 3.0 / LOG_K
            else:
                sc = math.log(1.0 + x3) / LOG_K

        else:
            # Unknown formula type — genuine fallthrough
            return (0.0, 0.0)

        if not math.isfinite(sc):
            return (0.0, 0.0)

        return (sc, sc)

    except (ValueError, OverflowError, ZeroDivisionError):
        return (0.0, 0.0)


def load_enabled_lakes():
    cfg = json.load(open(CONFIG_DIR / "volumes.json", "r", encoding="utf-8"))
    return tuple(n for n, m in cfg.get("volumes", {}).items() if m.get("enabled", False))

LAKES = load_enabled_lakes()
MODE  = "geometry"

def compute_geometry_payload(raw):
    return {"coordinates": [], "dimensionality": 0, "geometry_type": "unknown"}

# ==============================================================================
# HEARTBEAT TELEMETRY
# ==============================================================================
def write_heartbeat(pct, elapsed, total_tasks, completed_tasks, current_action):
    eta = (elapsed / max(1, completed_tasks)) * (total_tasks - completed_tasks) if completed_tasks > 0 else 0
    data = {
        "timestamp_utc": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        "progress_pct": min(100.0, max(0.0, round(pct, 2))),
        "completed": completed_tasks,
        "total": total_tasks,
        "eta_seconds": round(eta, 1),
        "current_action": current_action
    }
    try:
        with open(HEARTBEAT_PATH, 'w') as f:
            json.dump(data, f)
    except Exception:
        pass

# ==============================================================================
# EXISTING HANDLERS — unchanged, read from _raw_payload (legacy Vol5-8 format)
# ==============================================================================
def scalarize_biology(record):
    payload = record.get("_raw_payload", {}) or {}
    inv = payload.get("scalar_invariant")
    return (float(inv), float(inv)) if inv is not None else (0.0, 0.0)

def scalarize_chemistry(record):
    payload = record.get("_raw_payload", {}) or {}
    inv = payload.get("scalar_invariant")
    return (float(inv), float(inv)) if inv is not None else (0.0, 0.0)

def scalarize_materials(record):
    payload = record.get("_raw_payload", {}) or {}
    inv = payload.get("lattice_deviation") or payload.get("scalar_invariant")
    return (float(inv), float(inv)) if inv is not None else (0.0, 0.0)

def scalarize_frb(record):
    payload = record.get("_raw_payload", {}) or {}
    inv = payload.get("scalar_invariant")
    return (float(inv), float(inv)) if inv is not None else (0.0, 0.0)

def scalarize_null(record):
    return 0.0, 0.0

# ==============================================================================
# NEW HANDLERS (Vol9) — read flat fields from promoted records
# ==============================================================================
def _log_scalar(val):
    """Standard: log(val + 1) / log(k_geo). Returns 0.0 if invalid."""
    try:
        fval = float(val)
        if fval < 0: fval = abs(fval)
        if not math.isfinite(fval) or fval == 0: return 0.0
        sc = math.log(fval + 1.0) / LOG_K
        return sc if math.isfinite(sc) else 0.0
    except (TypeError, ValueError):
        return 0.0

def scalarize_nuclear_binding(record):
    sc = _log_scalar(record.get("binding_energy_mev_per_A"))
    return (sc, sc)

def scalarize_nuclear_decay(record):
    """Double-log: log(log(half_life_seconds + 1) + 1) / log(k_geo)"""
    try:
        hl = float(record.get("half_life_seconds", 0))
        if hl <= 0 or not math.isfinite(hl): return (0.0, 0.0)
        inner = math.log(hl + 1.0)
        if inner <= 0: return (0.0, 0.0)
        sc = math.log(inner + 1.0) / LOG_K
        sc = sc if math.isfinite(sc) else 0.0
        return (sc, sc)
    except (TypeError, ValueError):
        return (0.0, 0.0)

def scalarize_atomic_ionisation(record):
    sc = _log_scalar(record.get("ionisation_energy_eV"))
    return (sc, sc)

def scalarize_molecular_c60(record):
    sc = _log_scalar(record.get("frequency_cm1"))
    return (sc, sc)

def scalarize_stellar_cycle(record):
    sc = _log_scalar(record.get("interval_days"))
    return (sc, sc)

def scalarize_gravitational_wave(record):
    sc = _log_scalar(record.get("f_ring_hz"))
    return (sc, sc)

def scalarize_tidal(record):
    sc = _log_scalar(record.get("interval_hours"))
    return (sc, sc)

def scalarize_cmb_anisotropy(record):
    dt = record.get("delta_T_uK")
    if dt is None:
        dl = record.get("Dl_uK2", 0)
        try:
            dl_f = float(dl)
            dt = math.sqrt(dl_f) if dl_f > 0 else 0.0
        except (TypeError, ValueError):
            dt = 0.0
    sc = _log_scalar(dt)
    return (sc, sc)

# ==============================================================================
# NEW HANDLERS (Vol10)
# ==============================================================================
def scalarize_seismic_temporal(record):
    sc = _log_scalar(record.get("interval_days"))
    return (sc, sc)

def scalarize_orbital_ttv(record):
    sc = _log_scalar(record.get("ttv_absolute_minutes"))
    return (sc, sc)

def scalarize_subnuclear_mass(record):
    sc = _log_scalar(record.get("invariant_mass_gev"))
    return (sc, sc)

def scalarize_biology_backbone(record):
    try:
        val = float(record.get("angle_degrees", 0) or 0)
        sc = _log_scalar(abs(val))
        return (sc, sc)
    except (TypeError, ValueError):
        return (0.0, 0.0)

# ==============================================================================
# DISPATCH TABLE
# Priority order:
#   1. Named domain handlers (all existing code above — unchanged)
#   2. Rule 1.5: scalarize_from_config() — config-driven fallback
#   3. Legacy scalar_kls fallback (unchanged)
#   4. Final (0.0, 0.0)
# ==============================================================================
def scalarize_record(record, lake_id):
    domain       = (record.get("domain") or "").lower()
    domain_group = domain

    if domain in ("mechanical", "behavioral", "mathematical", "cosmological_null"):
        domain_group = "null"

    # --- Named handlers (priority 1: unchanged from original) ---
    if domain_group == "biology":
        scalar_kls, scalar_klc = scalarize_biology(record)
    elif domain_group == "chemistry":
        scalar_kls, scalar_klc = scalarize_chemistry(record)
    elif domain_group == "materials":
        scalar_kls, scalar_klc = scalarize_materials(record)
    elif domain_group in (
        "astrophysics", 
        "frb", 
        "stellar", 
        "planetary", 
        "cosmology"
    ):
        scalar_kls, scalar_klc = scalarize_frb(record)
    elif domain_group == "null":
        scalar_kls, scalar_klc = scalarize_null(record)
    elif domain_group == "nuclear_binding":
        scalar_kls, scalar_klc = scalarize_nuclear_binding(record)
    elif domain_group == "nuclear_decay":
        scalar_kls, scalar_klc = scalarize_nuclear_decay(record)
    elif domain_group == "atomic_ionisation":
        scalar_kls, scalar_klc = scalarize_atomic_ionisation(record)
    elif domain_group == "molecular_c60":
        scalar_kls, scalar_klc = scalarize_molecular_c60(record)
    elif domain_group == "stellar_cycle":
        scalar_kls, scalar_klc = scalarize_stellar_cycle(record)
    elif domain_group == "gravitational_wave":
        scalar_kls, scalar_klc = scalarize_gravitational_wave(record)
    elif domain_group in (
        "planetary_atlantic", 
        "planetary_gulf", 
        "planetary_pacific", 
        "planetary_indian"
    ):
        scalar_kls, scalar_klc = scalarize_tidal(record)
    elif domain_group == "cmb_anisotropy":
        scalar_kls, scalar_klc = scalarize_cmb_anisotropy(record)
    elif domain_group == "seismic_temporal":
        scalar_kls, scalar_klc = scalarize_seismic_temporal(record)
    elif domain_group == "orbital_ttv":
        scalar_kls, scalar_klc = scalarize_orbital_ttv(record)
    elif domain_group == "subnuclear_mass":
        scalar_kls, scalar_klc = scalarize_subnuclear_mass(record)
    elif domain_group == "biology_backbone":
        scalar_kls, scalar_klc = scalarize_biology_backbone(record)
    else:
        # --- Rule 1.5: Config-driven dispatch (priority 2) ---
        # Before returning zeros, check scalarize.json for this domain.
        # Handles all lakes defined in config without a named handler:
        #   - Multi-attribute lakes: stellar_spindown, stellar_dm, stellar_age,
        #     stellar_bfield, subnuclear_pt_lead, subnuclear_pt_sublead,
        #     subnuclear_eta, galactic_radius, galactic_sersic, galactic_mass,
        #     orbital_transit, orbital_eccentricity, orbital_inclination
        #   - Wrongbox lakes: orbital_wrongbox, kinematic_wrongbox,
        #     stellar_wrongbox, materials_wrongbox
        #     (These use log_volumetric or log_inverse — genuine wrong-projection
        #      math on real data, not silent zeros from a missing handler.)
        scalar_kls, scalar_klc = scalarize_from_config(record, domain_group)

    # --- Legacy fallback (priority 3: unchanged from original) ---
    if scalar_kls == 0.0 and scalar_klc == 0.0:
        existing = record.get("scalar_kls", 0.0)
        if existing != 0.0:
            scalar_kls = existing
            scalar_klc = record.get("scalar_klc", existing)

    raw  = record.get("_raw_payload", {}) or {}
    meta = dict(record.get("meta", {}))
    meta.setdefault("source",           "vol10_promotion_sovereign_lake")
    meta.setdefault("ingest_timestamp", "2026-05-10T00:00:00Z")
    meta.setdefault("sovereign",        False)

    return {
        "entity_id":        record.get("entity_id") or record.get("id"),
        "domain":           domain,
        "volume":           record.get("volume") or record.get("vol"),
        "lake_id":          lake_id,
        "geometry_payload": compute_geometry_payload(raw),
        "scalar_kls":       scalar_kls,
        "scalar_klc":       scalar_klc,
        "meta":             meta,
        "_raw_payload":     raw,
    }

if __name__ == "__main__":
    start_time = time.time()
    
    print("\n" + "=" * 60)
    print("  [MONITORING TIP] Open a new terminal and run:")
    print("  python engine/sidecar.py")
    print("  to view the live byte-streaming progress dashboard.")
    print("=" * 60 + "\n")
    
    # Pre-flight: calculate total bytes for smooth global progress bar
    total_bytes = 0
    valid_lakes = []
    
    for lake in LAKES:
        in_path = INPUT_DIR / f"{lake}_promoted.jsonl"
        if in_path.exists():
            total_bytes += in_path.stat().st_size
            valid_lakes.append(lake)
            
    global_bytes_processed = 0
    lakes_completed = 0
    
    write_heartbeat(0, 0, len(valid_lakes), 0, "Initializing Scalarization...")

    for lake in valid_lakes:
        in_path  = INPUT_DIR / f"{lake}_promoted.jsonl"
        out_path = OUTPUT_DIR / f"{lake}_scalarized.jsonl"

        print(f"Scalarizing {lake}: {in_path.name} -> {out_path.name} (mode={MODE})")

        records_this_lake = 0
        last_save = time.time()
        
        with in_path.open("r", encoding="utf-8") as fin, out_path.open("w", encoding="utf-8") as fout:
            for line in fin:
                global_bytes_processed += len(line.encode('utf-8'))
                
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    processed_rec = scalarize_record(rec, lake)
                    fout.write(json.dumps(processed_rec, ensure_ascii=False) + "\n")
                    records_this_lake += 1
                
                if time.time() - last_save > 2.0:
                    pct = (global_bytes_processed / total_bytes) * 100 if total_bytes > 0 else 0
                    write_heartbeat(pct, time.time() - start_time, len(valid_lakes), lakes_completed, f"Crunching {lake} ({records_this_lake:,} recs)")
                    last_save = time.time()
                    
        lakes_completed += 1
        pct = (global_bytes_processed / total_bytes) * 100 if total_bytes > 0 else 0
        write_heartbeat(pct, time.time() - start_time, len(valid_lakes), lakes_completed, f"Finished {lake}")