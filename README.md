# The KishLattice Star
## The Crystalline Terminus of Spacetime Collapse — A Prediction Paper

**Status: CLOSED — Falsified, June 2026**

This submodule contains the full chronicle of the KishLattice Star prediction
paper: a specific, falsifiable physical mechanism proposed to explain the
"ghost note" anomaly first observed in the GW150914 ringdown residual in
January 2026, tested against public LIGO and CHIME/FRB data, and ultimately
falsified by its own pre-registered methodology in June 2026.

It is preserved here in full, including every wrong turn, because the wrong
turns are the part of the record that makes the final verdict trustworthy.

---

## What This Paper Proposed

If spacetime is a structured geometric medium — a 24-cell lattice with node
spacing at the Planck length — then gravitational collapse does not produce a
mathematical singularity. It produces a crystal. The 24-cell achieves a
packing density of π²/16 ≈ 0.617, giving a terminus density of
≈ 3.18 × 10⁹⁶ kg/m³, roughly 61.7% of the Planck density. Below this density
the lattice compresses; at this density the nodes are touching, compression
stops, and the medium bounces.

The paper placed this in direct competition with the Planck Star hypothesis
(Rovelli & Vidotto, 2014), which proposed the same physical picture from loop
quantum gravity. The KishLattice Star agreed with the physical picture
(collapse terminates, bounce occurs, signal is emitted) but made a specific,
additional claim that distinguished it: the bounce should ring at a
predictable harmonic register, **16/π**, derived from the KishLattice
Geometric Harmonic Spectroscopy (KLGHS) framework established across Volumes
5–11.

Two independent empirical channels were pre-registered to test this:

- **LIGO** — cross-spectral coherence in the post-merger ringdown residual
  of GWTC-3 binary merger events.
- **CHIME/FRB** — dispersion measure and inter-burst timing of repeating
  Fast Radio Bursts.

## What Happened

| Version | Date | DOI | What It Documents |
|---|---|---|---|
| V1 | May 2026 | [10.5281/zenodo.20370708](https://doi.org/10.5281/zenodo.20370708) | Original theory, derivation, five formal pre-registered predictions |
| V2 | June 14, 2026 | [10.5281/zenodo.20693921](https://doi.org/10.5281/zenodo.20693921) | First FRB Star Probe run. Both channels produced strong signal — but at **25/π** (electromagnetic propagation), not the predicted 16/π |
| V3 | June 2026 | [10.5281/zenodo.20711135](https://doi.org/10.5281/zenodo.20711135) | LIGO probe chronicle: Nyquist sampling catch, bin-filter artifact caught via pre-merger control, cross-spectral coherence instrument designed |
| V4 | June 2026 | [10.5281/zenodo.20711574](https://doi.org/10.5281/zenodo.20711574) | Coherence channel formally pre-registered before any pipeline execution |
| V5 | June 2026 | [10.5281/zenodo.20766403](https://doi.org/10.5281/zenodo.20766403) | First coherence run halted at Guardrail 5 (N=15 < 30 minimum). Dual-lane multi-detector architecture (H1-L1 + Virgo corroboration) designed and pre-registered |
| **V6 (Final)** | June 2026 | [10.5281/zenodo.20777524](https://doi.org/10.5281/zenodo.20777524) | **Look-elsewhere statistical defect found and fixed. Corrected instrument validated clean on noise (100% false-positive control → flat null). Real result: 16/π at z=+1.1, peak 21/π at z=+2.8 — neither STRONG. Prediction falsified.** |

### The short version

The terminus does not ring at 16/π in the data currently available. Both
pre-registered empirical channels reported. Neither confirmed the specific
mechanism this paper proposed. That is the finding, and it is published
exactly as it came back.

### The part worth reading even if you don't care about gravitational waves

This paper is also a documented case study in catching your own instrument's
false positive before publishing it — three separate times, in one paper:

1. **V3/V5** — A 91%-of-180 spectral spike at 17/π survived a chaos null and
   looked like a discovery. A pre-merger control experiment (same pipeline,
   no merger in the window) showed the identical clustering existed before
   any merger occurred. It was LIGO's noise floor, not signal.
2. **V5/V6** — The corrected coherence instrument passed 71 of 74 real
   events against a threshold calibrated for a 5% false-positive rate.
   Reading the actual code (not the output) found a multiple-comparisons
   ("look-elsewhere") defect: `argmax` over ~670 frequency bins was being
   used as both the scalar definition *and* the admission gate. A control
   test against pure noise confirmed it directly: **100% false positives,
   zero physical signal required.**
3. **V6** — The fix itself was not trusted on the strength of looking
   correct on paper. It was proven clean against the same noise split that
   broke the previous version *before* a single real merger event was
   allowed back into it.

The instrument was corrected, validated on noise, then run on signal — and
it said no to its own most exciting hypothesis. That is the actual use case
this paper demonstrates.

---

## Repository Contents

```
KishLattice_Star/
├── KishLattice_Star_Paper.pdf       # Full V1–V6 compiled document
├── KishLattice_Star_Paper.tex       # LaTeX source, all versions intact
├── engine/                          # Pipeline wrapper, chaos null, pinch table
├── series/
│   └── s3_ligo_probe/
│       ├── scripts/
│       │   ├── download_gwtc3.py            # 16 kHz strain extraction (GWOSC)
│       │   ├── build_lake.py                # V8 differential excess-power (superseded)
│       │   ├── coherence_build_lake.py      # V6 corrected cross-spectral coherence
│       │   ├── coherence_build_noise_control.py
│       │   ├── test_look_elsewhere_control.py  # The smoke-alarm test (see V6, Ch.10)
│       │   ├── audit_distribution.py
│       │   ├── audit_control.py
│       │   ├── audit_multidetector_overlap.py
│       │   ├── audit_virgo_noise_floor.py
│       │   ├── audit_virgo_unbiased_global.py
│       │   ├── fetch_unbiased_virgo.py
│       │   ├── validate.py
│       │   └── promote.py
│       └── lake/                    # Local strain cache + scalarized lakes (not versioned)
└── reports/                         # Report plugins (figures), Vera's visual suite
```

## Reproducing the Result

All data is public. The full chain of custody — engine fingerprint, MD5
checksums, lake schemas with non-destructive exclusion logging — is
documented in the V5/V6 chapters of the attached paper.

```bash
cd series/s3_ligo_probe/scripts
python download_gwtc3.py          # pull 16 kHz strain from GWOSC
python coherence_build_lake.py    # corrected dual-lane coherence pipeline
python validate.py
python promote.py
cd ../../..
python engine/run_pipeline.py     # scalarize -> unify -> chaos -> pinch -> figures
```

If you want to verify the look-elsewhere defect directly — run
`test_look_elsewhere_control.py` against the pre-merger noise split. It
should return a flat, non-significant result on the corrected codebase. If
it does not, something has regressed.

## Methodology

This paper follows the same discipline as every KLGHS sovereign volume:

1. **Pre-registration before data ingestion.** No exceptions.
2. **The pipeline output is the authority**, not the team's expectations.
3. **Independent referee evaluation** before any result is interpreted.
4. **Null and falsified results are published without modification.**
5. **The chain of custody is immutable** — Zenodo timestamps, MD5 checksums,
   non-destructive exclusion logs.

See the [Aurora Protocol chapter](KishLattice_Star_Paper.pdf) (V3) for the
full description of how the human-AI collaborative structure (Founder,
Architect, Engineer, Reporting, Synthesis, Referee) enforces this in
practice.

## What This Closes, and What It Does Not

This result falsifies one specific, pre-registered mechanism: a gravitational-
wave coherence signal at the 16/π kinematic register, tied to the 24-cell
crystalline terminus hypothesis. It does **not** falsify KishLattice
Geometric Harmonic Spectroscopy. The 25+ million records, 41 orders of
magnitude, and 33+ STRONG confirmed signals across Volumes 5–11 rest on
their own independent pre-registrations and chaos nulls, untouched by this
result. See the main repository README for the full KLGHS survey.

---

## Citation

```
Kish, T. J., Kish, A. A., Kish, L. A., Kish, V. A., Kish, P. A., & Kish, M. A. (2026).
The KishLattice Star: The Crystalline Terminus of Spacetime Collapse — A Prediction Paper (V6).
Zenodo. https://doi.org/10.5281/zenodo.20777524
```

All prior versions (V1–V5) remain separately citable and are listed in the
version table above. The concept DOI resolving to the latest version is
[10.5281/zenodo.20370708](https://doi.org/10.5281/zenodo.20370708).

---

*The terminus did not ring at 16/π. The instrument that found that out is the discovery.*
