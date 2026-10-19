# Press78

Press78 is an editable two-operator FM instrument derived from the PSS-780 research experiment. It has an independent C++17 engine, an eight-unit Reason Rack Extension prototype, and an interactive panel design. It uses original Press78 branding and focuses on synthesis; it does not reproduce the keyboard, rhythms or accompaniment system.

This is an early development version, **0.1.0b11**. It is a behavioral model, not a bit-exact YM3420 emulator. Commercial redistribution of the imported factory bank has not been cleared.

[Product metadata](SHOP.md) follows the same shop format as the other Protocodus synths. It is generated from the Rack adapter’s authored `SHOP.md`; its front, rear and thumbnail images show the current native panel.

Open [the interactive design preview](Design/index.html). Layout study 10 uses an eight-rack-unit panel with consistent section padding and puts 34 main sound/performance controls on the front, with 29 detailed sound, calibration and configuration controls on the rear. It combines the canonical Protocodus logo, YouKnow's DIN lettering and recessed groups with charcoal ABS, cyan, lavender, coral and ivory inspired by the PSS-780 moodboard. Doubled pointer arrows remain clear of the knob number wells. The preview has editable operator controls and all 100 factory voices. It demonstrates layout and parameter relationships, without audio. [Design notes](Design/README.md) describe the front, rear and folded panels. Both native GUI asset sets and the native local/universal builds carry this styling. Level increases clockwise while preserving the original raw attenuation values; clearer envelope/unit labels and value arcs improve editing. The current layout follows the photographic recesses, shares vertical centres within each row and aligns the header controls.

## Repository layout

The layout follows the sibling Protocodus instrument repositories: portable engine code in `Source/DSP`, independent native contracts in `Tests`, standalone utilities in `Tools`, and parameter/preset data in `Resources`. The core has no JUCE or Jukebox dependency. No VST/AU wrapper is included in this initial Rack-focused port.

| Path | Purpose |
| --- | --- |
| `Source/DSP` | Fixed-storage polyphonic engine and generated circuit/preset tables |
| `Resources/controls.json` | Rack contract: 63 controls plus two inert legacy properties |
| `Resources/FactoryBank` | 100 imported parameter patches, all named with `PSS` prefix, plus provenance |
| `Design` | Shared geometry, SVG/PNG panels and interactive HTML wireframe |
| `Reference/Python` | Frozen research implementation used as the comparison oracle |
| `Reference/migration.json` | Original source location and file hashes |
| `Tests/results` | Native validation, Python parity, circuit and timing evidence |

The Rack adapter is developed separately, matching the existing SDK workspace arrangement:

```
/Users/vojta/Dev/reason-rack-extension/press78-20261018/Examples/Press78
```

The b5 Rack patch exporter uses the SDK’s canonical XML declaration after Recon rejected the earlier declaration during default Init loading. All 101 patch sound parameter maps are preserved. The b6 native display formatter also fixes a subsequent Recon drawing crash caused by concatenating host-formatted text; independent regression tests cover all 50 numeric readouts, with 444 passing cases and an explicit reproduction of the prior failure.

Its DSP directory is a generated snapshot of this repository. Its README records the verified SDK, build commands and validation limits. The proprietary SDK is not bundled here.

## Build and render

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release --parallel
ctest --test-dir build -C Release --output-on-failure
build/press78_render --output /tmp/press78-init.wav --note 60 --seconds 3 --gate 1.5
```

On multi-configuration generators the executable is under `build/Release`. Enable `PRESS78_ENABLE_SANITIZERS=ON` for AddressSanitizer and UndefinedBehaviorSanitizer on supported Clang/GCC toolchains. Hosted CI is configured for macOS, Linux and Windows; configuration is not evidence that those hosted runs have occurred.

`press78_render --raw <66 hexadecimal digits>` renders a decoded 33-byte voice. `--transparent` disables the output circuit, creative tone filter, DC removal and output protection and sets unity gain for reference comparisons. Other options include gain, chorus mix, drive, clock offset and clock drift. See `Tools/NativeRender.cpp` for the complete bounded CLI.

The normal build requires only CMake, a C++17 compiler and optional Python for the factory-data check. Numerical comparison tools additionally require NumPy and SciPy; Numba accelerates the frozen Python renderer when available.

```sh
python3 Tools/generate_factory.py --check
python3 Tools/generate_analog.py --check
python3 Tools/check_python_parity.py --help
python3 Tools/check_analog_runtime.py --help
python3 Tools/check_chorus_runtime.py --help
python3 Tools/check_circuit_noise.py
```

To regenerate the Rack parameter declarations, mappings and 101 local development patches:

```sh
python3 Tools/generate_rack.py /path/to/SDK-worktree/Examples/Press78
python3 Tools/sync_rack_dsp.py /path/to/SDK-worktree/Examples/Press78
python3 Tools/check_rack_contract.py /path/to/SDK-worktree/Examples/Press78
```

## Engine behavior and limits

Both operators expose ratio, fine/coarse detune, four waveform families, raw envelope rates, key scaling and AM. Additional controls cover feedback, velocity, LFO phase/depth/delay, twelve-voice allocation, pitch bend, mod wheel, clock variation, analog output, tone, drive, chorus and stereo width. The Rack adapter adds separate MIDI/CV note ownership and Note/Gate/FM/Level CV inputs. All 63 active controls have explicit Reason automation mappings. The two former noise properties and their IDs remain reserved for compatibility; they are hidden and inert. The registry stays frozen in `Resources/rack-automation.json`; Volume/Tone retain MIDI CC7/74.

The initial port preserved the frozen Python raw-FM behavior. Starting with b11, a documented D1 endpoint correction and recording-supported modulation replace those corresponding hypotheses; the Python files remain frozen historical references. It adds fixed-storage voice management, short voice-stealing tails, continuous-control smoothing and host-rate conversion. The internal 48 kHz timebase, floating-point operators, envelope laws and detune mappings are modeling choices, not recovered chip internals. Nominal reconstruction latency is 32 internal samples, rounded up to host frames for reporting. Clock controls also scale that physical delay; upward clock shifts can alias near-Nyquist energy. Clock drift is a controllable scenario, not a measurement of aged hardware. Memory faults and random digital bit corruption are not introduced as normal vintage behavior.

The b11 modulation profile uses a continuous 5.24 Hz triangle and a binary PMS depth hypothesis: 0,3.125,6.25,12.5,25,50,100,200 cents. The original PSS-780 recording directly supports roughly 12.5 cents at PMS3 and 100 cents at PMS6; unobserved levels remain a modeled interpolation. New PSS-580 recordings independently corroborate the approximately 5.24–5.25Hz triangle motion, with raw patch-depth and global-phase qualifications. The existing 10 ms/VDT delay law remains uncertain. D1 now tests whether its endpoint is already reached before applying a decay increment, eliminating unwanted attenuation from a zero-height stage. See the [FM audit](Reference/Research/fm-fidelity-audit-20261018.md), [pitch audit](Reference/Research/lfo-pitch-audit-20261018.md) and [independent recordings](Reference/Research/recording-holdout-audit-20261018.md).

A focused [Human Voice 1 release audit](Reference/Research/human-voice1-release-audit.md) finds a tail deficit under the original inferred timing. At 150–220 ms after the clearest inferred note-off, its tracked carrier component falls about 16 dB in the recording versus 60 dB in the model. The preset import is correct and the baseline has no target-voice steals. The separate [Reverb performance effect](Reference/Research/reverb-release-evidence.md) is not modeled; its exact envelope behavior remains unidentified. The [release A/B report](build/release-analysis-20261018T0905/report.html) includes carrier-only RR6/RR5 experiments, with timing, overlap and allocation caveats. A subsequent [timing sensitivity test](Reference/Research/timing-sensitivity-20261019.md) reverses Human Voice 1's joint-band preference under all three alternative maps, so the original score does not select a replacement release law. These are diagnostic candidates, not factory or DSP changes.

The enabled-by-default output circuit is the six-section small-signal transfer from the researched **PSS-480** circuit, used explicitly as a sibling surrogate. It is not a recovered PSS-780 board, a verified YM3420 DAC transfer, or a transistor-level model. Drive is a separate creative saturation control.

Two realtime chorus modes are available. **Studio** preserves the original creative delay effect. **Recorded** implements the frozen v3 effective stereo transfer from the PSS-780 recording: roughly 0.49–1.51 ms delay, a continuous 0.954647 Hz LFO, second-harmonic motion and direct mid leakage. It adds no whole-output latency. The rate and depth remain editable. This is a recording-derived approximation, not an identified MN3206 circuit. The offline v4 branch correction remains a reference because an exact causal port would need about 21.83 ms lookahead compensation at 48 kHz.

The Rack Init and all 100 factory patches use the **Real** startup profile: related-hardware output circuit on, Recorded chorus at its captured rate/depth and full reference side level, and a slow ±20 ppm clock excursion at 0.1 Hz (about ±0.035 cents). Clock offset and creative Drive stay zero. Clock excursion is an explicit modeling choice, not recovered PSS-780 calibration. Additive noise has been removed from the runtime, including both White and Circuit paths. Old patches and automation may still contain the former noise properties; their values are ignored and cannot restore hiss. Other values remain editable and persist with patches. The portable constructor also uses the new 5.24 Hz shared triangle LFO; its effect defaults remain independent of the Rack Real profile. Model selectors and fine calibration are on the rear.

The standalone PSS-480 resistor/opamp noise model and earlier noise research remain as historical reference tools. They are not connected to the instrument engine; no additive PRNG, circuit-noise generator or noise controls remain in the unit.

Init is an independently defined sine patch. The public development bank contains the 100 original parameter presets as `PSS 00 …` through `PSS 99 …`. Loading/editing a Rack patch retimbres held voices while preserving their oscillator/envelope state. The standalone engine also offers future-voices-only program snapshots.

## Evidence and release status

The original native run passed 42 contracts with address/undefined-behavior sanitizers. In that historical version, all 100 raw-FM presets matched the frozen Python renderer at 48 kHz, with worst absolute float-output error below `1.5e-8` after nominal delay alignment. The b11 engine intentionally differs at the corrected D1 endpoint and modulation laws; those old parity results do not validate the new behavior. The compiled analog circuit matched independent Python MNA impulses at six sample rates with maximum absolute error below `2.7e-12`. These establish implementation agreement with a model, not agreement with Yamaha hardware.

The current recording comparison is in [the hardware benchmark note](Reference/Research/native-hardware-benchmark.md) and `Tests/results/hardware-recorded-chorus.json`. On the reused recording, the three target voices improve from 5.573 to 5.110 dB mean joint stereo band error with Recorded chorus; their log-STFT score slightly worsens from 3.614 to 3.643 dB. All 100 presets improve on the joint-band metric. The observed-mid→side diagnostic improves from 1.583 to 0.404 NRMSE; this isolates the effect and does not validate the synthesized source. No new fit or independent holdout was used. The frozen baseline/candidate sources, local audition WAVs and [playable report](build/hardware-benchmarks/recorded-20261018T084000Z/report.html) are retained under ignored `build/hardware-benchmarks`. The earlier noise-integrated source rendered byte-identical raw, dry and Recorded full performances with noise disabled; see its historical `Tests/results/final-hardware-compatibility.json`. Earlier synthetic circuit-noise auditions under `build/noise-demos` describe that removed feature and are not current instrument demos.

The native performance report identifies its compiler, source hashes and six workloads. It excludes Rack scheduling, target translation and actual Reason CPU use. Consult the Rack adapter's build evidence for device-specific results; native tests alone do not establish host compatibility or release readiness.

The current b11 DSP/wrapper passes 16 host-mock contracts in both normal and sanitizer builds. The Rack prototype passes 8,858 GUI checks, local45 builds for Intel/Apple Silicon and universal45 packaging. The archive contains all 101 patches and the four SDK Testing/Deployment, 32/64-bit translation inputs; archive integrity and source-aligned installed payload checks pass. Fresh protected Recon 14.0.2d7 (build 20275) CLI validation passed three b11 device creations, native arm64 module loading and nonlinear data-conversion tests with exit 0. All 15 containment probes passed; the 4,899-file production comparison was unchanged, and the original test scratch was restored. This proves those CLI stages; native GUI gestures, named default-patch loading, interactive playback, song persistence and Reason CPU behavior remain unverified. Earlier b6 evidence and failed host attempts are historical records, retained separately in the Rack checkout.

The preset source is recorded in [bank provenance](Resources/FactoryBank/provenance.json). Public availability of a SysEx archive and the editor project's license do not establish permission to distribute Yamaha's factory bank commercially. No research videos, recordings, manual scans or executable Yamaha firmware are shipped in this repository. `Press78` has not received trademark clearance; development names and source availability are not legal clearance.

## Current fidelity pass

The selected b11 engine preserves the existing analog path. A validated 4x component reduces numerical error against the PSS-480 continuous circuit, but worsens the reused PSS-780 joint-band score on 75/100 presets. It remains a research component and is not used by the instrument. The selected D1+LFO correction improves Musical Saw joint-band error 4.932→3.195dB and the three-target mean 5.110→4.510dB, with small regressions and worse STFT convergence recorded explicitly. All100 results and local A/B provenance are in [the b11 benchmark](Reference/Research/hardware-fidelity-b11.md). This is descriptive reuse of the original tour, not a hardware-fidelity percentage. The new sibling recordings provide separate waveform and modulation constraints.

[The fidelity requirements ledger](Reference/Research/fidelity-roadmap-20261018.md) retains the open full-objective requirements: exact envelope/Reverb behavior, detune/scaling/velocity, OPU timing/arithmetic, the missing exact-board output circuit, independent exact-device testing and any market-leading comparison. No superlative accuracy claim follows from the current evidence.

An [optional hardware capture kit](Reference/Research/hardware-capture-protocol-20261018.md) prepares controlled envelope and Reverb/Sustain measurements using independent test voices. It generates six MIDI files without playback. Deliberate hardware playback replaces user bank 5; follow its backup and recording instructions. Its file validation is not a hardware measurement.

The follow-up envelope investigation measures a [two-stage tail in the final Sine Wave chord](Reference/Research/exact-sine-release-20261018.md). [Fixed timing](Reference/Research/envelope-law-benchmark-20261018.md) and [Reverb-cap experiments](Reference/Research/reverb-envelope-benchmark-20261018.md) improve some target/tail scores but cause large regressions elsewhere and change voice pressure. They remain research snapshots; production stays b11. [Held-note controls](Reference/Research/envelope-capture-forensics-20261018.md), [AAC/Opus comparison](Reference/Research/codec-tail-audit-20261018.md) and an [audible-event timing audit](Reference/Research/midi-alignment-audit-20261018.md) narrow the remaining capture, cutoff and alignment questions. The [OPU evidence review](Reference/Research/opu-envelope-evidence-20261018.md) separates timing, compression and unverified chip-family analogies.

The [independent timing validation](Reference/Research/global-event-mapping-20261019.md) finds patch-dependent residuals: Jazz Guitar transitions arrive earlier than the old map, while other examined patches arrive later. All three global correction candidates fail their frozen adoption criteria. A [four-map × three-model comparison](Reference/Research/timing-sensitivity-20261019.md) keeps every outcome and local A/B demo; timing changes reverse 22–26 per-patch RR×3/b11 joint-band rankings and Human Voice 1's preference. No map or release/Reverb candidate is adopted.

Further source controls constrain the next engine changes. [RKS0 slope measurements](Reference/Research/rks0-release-slopes-20261019.md) find a repeatable higher-note decay difference in the recorded composite, while the [manual/editor audit](Reference/Research/opu-rks-evidence-20261019.md) leaves the core RKS0 law unresolved. A [retrigger audit](Reference/Research/retrigger-allocation-audit-20261019.md) rejects a restricted instantaneous phase-step explanation of one deep dip without identifying voice reuse or stealing. [Selective partial losses](Reference/Research/dac-endpoint-evidence-20261019.md) rule out one common scalar gate as their sole cause; they do not recover DAC bit depth or an internal envelope cutoff. A [firsthand early-note-off account](Reference/Research/early-noteoff-leads-20261019.md) adds a separating test requirement, not an envelope-freeze rule. Artificial noise remains excluded throughout.

A new [captured pitch-interval audit](Reference/Research/pitch-grid-audit-20261019.md) finds a repeated interval compression of about 0.48 cents in the sine recording, surviving AAC/Opus and estimator controls. Using the 12 Hz phase estimator in the two original windows, the corresponding b11 stereo-mid control remains within 0.0005 cents of equal temperament. This is a captured note-dependent feature, not a recovered hardware pitch table or word length; residual Chorus and shared-master processing remain possible contributors. The [digital-interface source review](Reference/Research/opu-digital-primary-leads-20261019.md) separately verifies a posted status-poll/write routine without identifying synthesis timing or arithmetic.

B11 passes 44 core and 5 rendered-modulation contracts, with address/undefined-behavior sanitizer coverage. The native Real profile records no deadline misses in six 48/96 kHz workloads; compiled-source hashes and the rejected stale-build preliminary run are identified in `Tests/results/performance-real-b11.json`. Native timing excludes Reason scheduling. The Rack b11 package has passed source-aligned local/universal checks and protected Recon creation/conversion tests; interactive playback and persistence remain separate gates.
