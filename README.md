# Press78

Press78 is an editable two-operator FM instrument derived from the PSS-780 research experiment. It has an independent C++17 engine, an eight-unit Reason Rack Extension prototype, and an interactive panel design. It uses original Press78 branding and focuses on synthesis; it does not reproduce the keyboard, rhythms or accompaniment system.

This is an early development version, **0.1.0b7**. It is a behavioral model, not a bit-exact YM3420 emulator. Commercial redistribution of the imported factory bank has not been cleared.

[Product metadata](SHOP.md) follows the same shop format as the other Protocodus synths. It is generated from the Rack adapter’s authored `SHOP.md`; its front, rear and thumbnail images show the current native panel.

Open [the interactive design preview](Design/index.html). Layout study 07 compacts the panel from twelve to eight rack units with consistent section padding and puts 35 main sound/performance controls on the front, with 30 detailed sound, calibration and configuration controls on the rear. It combines the canonical Protocodus logo, YouKnow's DIN lettering and recessed groups with charcoal ABS, cyan, lavender, coral and ivory inspired by the PSS-780 moodboard. Doubled pointer arrows remain clear of the knob number wells. The preview has editable operator controls and all 100 factory voices. It demonstrates layout and parameter relationships, without audio. [Design notes](Design/README.md) describe the front, rear and folded panels. Both native GUI asset sets and the native local/universal builds carry this styling. Level now increases clockwise while preserving the original raw attenuation values; clearer envelope/unit labels and value arcs improve editing.

## Repository layout

The layout follows the sibling Protocodus instrument repositories: portable engine code in `Source/DSP`, independent native contracts in `Tests`, standalone utilities in `Tools`, and parameter/preset data in `Resources`. The core has no JUCE or Jukebox dependency. No VST/AU wrapper is included in this initial Rack-focused port.

| Path | Purpose |
| --- | --- |
| `Source/DSP` | Fixed-storage polyphonic engine and generated circuit/preset tables |
| `Resources/controls.json` | Canonical 65-control Rack parameter contract |
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

`press78_render --raw <66 hexadecimal digits>` renders a decoded 33-byte voice. `--transparent` disables the output circuit, creative tone filter, DC removal and output protection and sets unity gain for reference comparisons. Other options include gain, chorus mix, drive, noise, clock offset and clock drift. See `Tools/NativeRender.cpp` for the complete bounded CLI.

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

Both operators expose ratio, fine/coarse detune, four waveform families, raw envelope rates, key scaling and AM. Additional controls cover feedback, velocity, LFO phase/depth/delay, twelve-voice allocation, pitch bend, mod wheel, clock variation, analog output, tone, drive, chorus, stereo width and noise. The Rack adapter adds separate MIDI/CV note ownership and Note/Gate/FM/Level CV inputs. All 65 controls have explicit Reason automation mappings, frozen in `Resources/rack-automation.json`; Volume/Tone retain MIDI CC7/74.

The port preserves the frozen Python raw-FM behavior. It adds fixed-storage voice management, short voice-stealing tails, continuous-control smoothing and host-rate conversion. The internal 48 kHz timebase, floating-point operators, envelope laws and detune mappings are modeling choices, not recovered chip internals. Nominal reconstruction latency is 32 internal samples, rounded up to host frames for reporting. Clock controls also scale that physical delay; upward clock shifts can alias near-Nyquist energy. Clock drift and noise are controllable scenarios, not measurements of aged hardware. Memory faults and random digital bit corruption are not introduced as normal vintage behavior.

A focused [Human Voice 1 release audit](Reference/Research/human-voice1-release-audit.md) confirms a tail deficit in the reused recording. At 150–220 ms after the clearest inferred note-off, its tracked carrier component falls about 16 dB in the recording versus 60 dB in the model. The preset import is correct and the baseline has no target-voice steals. The separate [Reverb performance effect](Reference/Research/reverb-release-evidence.md) is not modeled; its exact envelope behavior remains unidentified. The [release A/B report](build/release-analysis-20261018T0905/report.html) includes carrier-only RR6/RR5 experiments, with timing, overlap and allocation caveats. These are diagnostic candidates, not factory or DSP changes.

The enabled-by-default output circuit is the six-section small-signal transfer from the researched **PSS-480** circuit, used explicitly as a sibling surrogate. It is not a recovered PSS-780 board, a verified YM3420 DAC transfer, or a transistor-level model. Drive is a separate creative saturation control.

Two realtime chorus modes are available. **Studio** preserves the original creative delay effect. **Recorded** implements the frozen v3 effective stereo transfer from the PSS-780 recording: roughly 0.49–1.51 ms delay, a continuous 0.954647 Hz LFO, second-harmonic motion and direct mid leakage. It adds no whole-output latency. The rate and depth remain editable. This is a recording-derived approximation, not an identified MN3206 circuit. The offline v4 branch correction remains a reference because an exact causal port would need about 21.83 ms lookahead compensation at 48 kHz.

The Rack Init and all 100 factory patches now use the **Real** startup profile: related-hardware output circuit on, Recorded chorus at its captured rate/depth and full reference side level, Circuit noise at 0.002 before master gain, and a slow ±20 ppm clock excursion at 0.1 Hz (about ±0.035 cents). Clock offset stays zero. Noise amplitude and clock excursion are explicit modeling choices, not recovered PSS-780 calibration. The creative Drive control remains zero. All values stay editable and persist with patches; existing saved songs retain their stored values. The portable engine constructor retains its earlier defaults for reference-tool compatibility. Model selectors and fine calibration are on the rear.

The optional **Circuit** noise mode uses the PSS-480 resistor/opamp network and its stereo covariance: 300 K resistor thermal noise and independent 10 nV/√Hz white opamp input sources, represented by twelve states and fourteen sources. Noise level scales output relative to one fixed 11.96866768 µVrms continuous 20–20 kHz reference, before master volume. Bilinear discretization retains its high-frequency warping: at 48 kHz the predicted 20–20 kHz level is about 0.9228 times that reference, with no per-rate or per-clip normalization. It is a sibling-circuit scenario; absolute PSS-780 noise in dBFS is not known. White noise remains available. Rack Real defaults to Circuit noise at 0.002; the portable engine constructor keeps zero added noise. Neither mode claims recovered YM3420 conversion noise, BBD noise, capacitor aging or memory corruption.

Init is an independently defined sine patch. The public development bank contains the 100 original parameter presets as `PSS 00 …` through `PSS 99 …`. Loading/editing a Rack patch retimbres held voices while preserving their oscillator/envelope state. The standalone engine also offers future-voices-only program snapshots.

## Evidence and release status

The recorded native run passed 42 contracts with address/undefined-behavior sanitizers. All 100 raw-FM presets matched the frozen Python renderer at 48 kHz, with worst absolute float-output error below `1.5e-8` after nominal delay alignment. The compiled analog circuit matched independent Python MNA impulses at six sample rates with maximum absolute error below `2.7e-12`. These establish implementation agreement with a model, not agreement with Yamaha hardware.

The current recording comparison is in [the hardware benchmark note](Reference/Research/native-hardware-benchmark.md) and `Tests/results/hardware-recorded-chorus.json`. On the reused recording, the three target voices improve from 5.573 to 5.110 dB mean joint stereo band error with Recorded chorus; their log-STFT score slightly worsens from 3.614 to 3.643 dB. All 100 presets improve on the joint-band metric. The observed-mid→side diagnostic improves from 1.583 to 0.404 NRMSE; this isolates the effect and does not validate the synthesized source. No new fit or independent holdout was used. The frozen baseline/candidate sources, local audition WAVs and [playable report](build/hardware-benchmarks/recorded-20261018T084000Z/report.html) are retained under ignored `build/hardware-benchmarks`. The final noise-integrated source renders byte-identical raw, dry and Recorded full performances with noise disabled; see `Tests/results/final-hardware-compatibility.json`. Separate [synthetic circuit-noise auditions](build/noise-demos/report.html) compare fixed-level notes and noise alone. Reproduce them with `Tools/render_noise_demos.py`, then `Tools/build_noise_report.py`.

The native performance report identifies its compiler, source hashes and six workloads. It excludes Rack scheduling, target translation and actual Reason CPU use. Consult the Rack adapter's build evidence for device-specific results; native tests alone do not establish host compatibility or release readiness.

The unchanged DSP/wrapper retains its earlier 16 passing host-mock contracts in normal and sanitizer builds. The b6 Rack prototype passes 8,526 GUI checks (including 315 pointer-frame checks), 33,445 independent Lua Level-control assertions across 256 draw states and 322 gesture cases, local45 builds for Intel/Apple Silicon and universal45 packaging. The final archive contains all 101 patches and the four SDK Testing/Deployment, 32/64-bit translation inputs; archive integrity and source-aligned installed payload checks pass. The Real native performance run at 48/96 kHz recorded no block-deadline misses in its six workloads; this is not a Reason CPU measurement. Fresh b6 protected Recon 14.0.2d7 (build 20275) CLI validation passed three device creations, native arm64 module loading and nonlinear data-conversion tests with exit 0; all 15 containment probes and the 4,817-file production comparison passed. The production profile and original test scratch were restored unchanged. This proves those CLI stages; native GUI gestures, named default-patch loading, interactive playback, song persistence and Reason CPU behavior remain unverified. The reviewed receipt and historical failed attempts are retained separately in the Rack checkout.

The preset source is recorded in [bank provenance](Resources/FactoryBank/provenance.json). Public availability of a SysEx archive and the editor project's license do not establish permission to distribute Yamaha's factory bank commercially. No research videos, recordings, manual scans or executable Yamaha firmware are shipped in this repository. `Press78` has not received trademark clearance; development names and source availability are not legal clearance.
