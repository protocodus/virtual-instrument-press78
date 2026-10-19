# Key-level component diagnostic — 19 October 2026

The carrier change contributes more to the Bowed Bass regression in this fixed renderer: **carrier-only +0.156114 dB**, modulator-only +0.055765 dB, and both together +0.209059 dB in joint stereo band error. This is a **posthoc diagnostic**, undertaken after the [full candidate failed its original adoption gate](hardware-key-level-b13-2026-10-19.md). That failure stands. Neither hybrid is adopted, and production source, presets and defaults remain unchanged.

The [complete JSON report](key-level-decomposition-2026-10-19.json) retains all 100 windows, all four metrics, every regression, source identities and the frozen diagnostic design. No source-routing defect was identified in the bounded review. The source-derived lookup itself remains independently verified; the synthesis and output model around it remains approximate.

## Separately frozen experiment

Before compilation or diagnostic audio, protocol SHA256 `14c811257c8ce7cbc0fa2af8ad9fb93bfc5586701a0f800196180b37823d019c` bound two copies of the rejected candidate. **ModulatorOnly** replaces only its firmware carrier-gain call with the legacy call. **CarrierOnly** replaces only the firmware modulator-gain call. Every other source byte is identical. Both request `keyLevelModel=1`, with Original pitch fixed at `pitchModel=1`.

Each variant renders the complete unchanged-map performance: 1,761 note-ons, 1,761 offs and 100 program changes. The same 100 absolute windows, 32-frame latency trim, Recorded chorus epoch and four metrics are retained. No timing, gain, EQ, pitch, patch, envelope or other parameter was fitted. The metric's established single stereo-pair RMS normalization is unchanged. Existing Legacy and full Firmware WAVs are reused; no diagnostic auditions were exported.

This is a whole-performance component comparison, not isolated resynthesis of one preset. Per-note and chord balance, preceding release tails, envelopes, allocation and chorus contribute to its window scores. The two new pressure logs are byte-identical to the original full Firmware log. All 1,761 actual note-ons have the same carrier mute/admission decision under legacy and firmware rules, so that optimization does not confound these component substitutions.

## Fixed results

Lower is better. All differences below are relative to Legacy; these are descriptive error changes, not percentages of fidelity or new acceptance gates.

| All-100 metric | Legacy | ModulatorOnly difference | CarrierOnly difference | Full Firmware difference |
| --- | ---: | ---: | ---: | ---: |
| Joint band, dB | 3.143844 | -0.062167 | +0.007481 | -0.052867 |
| Mid band, dB | 2.734649 | -0.071410 | +0.010008 | -0.059171 |
| STFT convergence | 0.550977 | -0.001656 | -0.001094 | -0.002759 |
| STFT log, dB | 3.160115 | -0.010477 | +0.006063 | -0.004346 |

| Voice | ModulatorOnly difference, dB | CarrierOnly difference, dB | Full difference, dB |
| --- | ---: | ---: | ---: |
| 64 wood bass 2 | -0.000001 | -0.116066 | -0.116067 |
| 65 bowed bass | +0.055765 | +0.156114 | +0.209059 |
| 66 banjo | -0.188732 | -0.000000 | -0.188732 |
| 93 human voice 1 | -0.001706 | -0.006522 | +0.030937 |
| 97 musical saw | +0.004394 | +0.062442 | +0.068930 |

The second table uses joint stereo band error. Both paths worsen the Bowed Bass window, with a larger carrier-only change. Their sum is +0.211879 dB; the actual full change is +0.209059 dB, leaving −0.002820 dB of error nonadditivity. These score differences should not be converted into additive physical contributions.

Human Voice 1 illustrates the limitation: each single-component score improves slightly, while both together worsen by +0.030937 dB. Its error nonadditivity is +0.039166 dB. FM, the performance mixture and the normalized spectral metric can interact. The more favorable all-100 result for one hybrid is not grounds for selecting it after observing this diagnostic.

## What the source review narrows down

All 100 event patches exactly match the factory bank's 33-byte payloads. Bowed Bass 65 decodes to modulator/carrier TL 18/19, LKS `0x07`/`0xb5`, multiplier 1/1 and feedback 5. All 17 of its note-ons and their eleven distinct notes are retained. The lookup receives the existing voice note; there is no hidden program transpose or accidental nibble swap. The 8π modulation scale, feedback path, velocity law, envelope coefficients and output processing are unchanged.

Under the *existing model's* 0.75 dB/TL conversion, the Bowed Bass modulator gain changes only below note 60 in this performance, by −0.25 to +0.3125 dB. Its carrier changes nonuniformly: +0.75 dB at note 48, about +1.44 dB at 77 and +1.42 dB at 84, while note 60 is unchanged. The JSON lists every played note. A single pair-level normalization cannot remove these changes in relative note/chord balance.

These are modeled coefficient differences, not measured hardware gains. The larger CarrierOnly score effect does **not** uniquely identify a DAC transfer problem, disprove the recovered commands, or establish or refute the 0.75 dB/TL transfer from source evidence alone. It narrows where this current renderer's regression enters. The remaining physical attenuation, envelope and output interactions are unresolved.

## Validation and preservation

Both new float WAVs are finite and total 142,907,368 bytes, below the frozen 170 MB limit. Their raw peaks are 2.177346 and 2.235662 because the research fixture uses unity gain without a limiter; float storage does not clip them. No third-party media is bundled in the report.

All 200 reused Legacy/full Firmware comparisons were independently recomputed from the raw unchanged-map audio: **all800 values across the four primary metrics matched exactly**. This also strengthens the main benchmark's unchanged-map evidence; it is not a new recording or a recomputation of its other three maps.

A separate validation script checked both exact one-call substitutions, every other copied source hash, all diagnostic arithmetic/aggregates/regression lists, pressure identity and the storage limit. It additionally checked the main report's 51 provenance bindings, 96 aggregate cells, 1,600 signed differences and 16 regression lists. All nine production DSP files still match the frozen b12 baseline.

The frozen protocol, runner, validation, pressure logs and full WAVs remain in ignored `build/key-level-b13-diagnostic-20261019`. The original main protocol, source and result were not changed. The concise report and numerical ledger are separate research artifacts; they authorize no source/default adoption.
