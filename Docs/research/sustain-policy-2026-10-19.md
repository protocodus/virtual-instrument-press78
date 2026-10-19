# Original Sustain command policy — 19 October 2026

Press78 now has an adopted core policy that uses Sustain to select the stored release rate and lets keyoff occur immediately. It corrects a recovered command-path mismatch while retaining the previous host-pedal behavior for older documents. The analytical envelope timing law is unchanged. This checkpoint covers adopted source and completed core/regression checks; native wrapper validation and b13 packaging remain pending.

## Evidence and precedence

The [original release-command investigation](opu-release-command-path-2026-10-19.md) executed both PSS-780 and PSS-680 firmware: every nonzero received CC64 value enables SRR, zero selects RR, and keyoff is still emitted. Later CC64 messages refresh matching cached slots, including voices already released. The command writes preserve D1L. They do not identify the OPU's envelope clock, exact rate law or instantaneous response to a live rate write.

This pass adds **224 original-program cases** covering factory/mode initialization, CC64 values 0/1/63/64/127, program changes and subsequent noteoff. Factory/program loading seeds Sustain from the selected patch flag; a later CC64 message replaces that state. The two inputs are not ORed. A separate implementation of the mirrored, read-only banked bus passes **64 independent transition cases**, including repeated same-program selections and already-released slots. Both investigations use constructed neutral RAM and original routines, not a complete machine boot or hardware audio measurement. Their source identities and compact results are retained in the [policy ledger](sustain-policy-2026-10-19.json).

The actual program paths differ. Mode00 replaces the shared working patch. A Mode99 received program change can keyoff a held old voice under its previous state, then seed the receiving channel's Sustain flag from the new preset; an already-released slot receives no program-change OPU writes in the tested path. Its cached patch remains the old patch. A subsequent CC64 message selects that cached patch's RR/SRR, rather than the new program's rates. The initial inference that Mode99 program changes retained CC state was false: it came from inspecting the lower-level cache loader instead of the complete serial program handler. The failing witness and original script remain preserved in ignored research artifacts.

## Implemented single-part policy

`Controls.sustainMode` selects **Legacy0** or **Original1**. The constructor and missing stored property use Legacy. New Init/factory patches explicitly store Original in hidden compatibility property **320**; this adds no new front-panel selector. The raw API `sustainController(int)` represents an actual message, clamps to0–127, and uses the Legacy threshold64 or Original nonzero rule. Existing `sustainPedal(bool)` calls map to127/0.

| Event | Original policy |
|---|---|
| Reset or allSoundOff | Clear sounding voices and seed runtime Sustain from the current patch flag. |
| `setPatch(p,false)` | Seed future voices from the program flag; leave existing voices' cached coefficients intact. |
| `setPatch(p,true)` | Apply live coefficient edits; preserve a CC override unless the authored Sustain flag actually changes. |
| CC64 or explicit live Sustain flag change | Replace runtime state and refresh active/releasing voices from each voice's own cached patch. |
| noteOff or allNotesOff | Release immediately using the voice's currently selected coefficient. |
| Requested policy change | Wait until sounding voices and steal fades are idle; `effectiveSustainMode()` reports the active policy. |

Future-only program loading is the existing plugin API's explicit boundary. It preserves old voices through their later keyoff instead of importing the keyboard's program-change killing or shared-patch retimbring. It is a modern adaptation, not full Mode00/99 program or allocator emulation. Actual CC64 still updates existing voices using their cached patch, as the firmware traces establish.

A rate refresh changes only the release coefficient. Oscillator phase, feedback history, envelope attenuation/stage/finished flags, note age and ticks survive. The existing48-tick steal fade is also refreshed without extending or restarting it. This fade is a plugin click guard, not evidence of an original hardware voice slot. The subsequent slope uses the existing approximate RR/SRR transfer; no new rate curve was fitted.

## Host boundary and beta limits

Reason's [official SDK5 scripting specification](https://developer.reasonstudios.com/documentation/rack-extension-sdk/5.0.0/jukebox-scripting-specification) defines the normalized pedal as on at values at least0.5. The native wrapper retains that contract; it does not reinterpret a small positive host value as raw CC64=1. Only the standalone raw-message API preserves that original distinction.

Host routing uses the **effective**, potentially deferred policy. Legacy coalesces pedal notifications within a frame to their final threshold state; Original preserves threshold edges. A fresh/reset snapshot forwards a held pedal, while a zero snapshot is not invented as a wire CC0. Repeated values and unrelated parameter edits must not overwrite the Original runtime state. Wrapper completion is tracked separately from the core checks below.

The front Sustain toggle represents the authored patch flag, not a live indicator of the controller override. CC0 can therefore disable runtime Sustain while the authored toggle remains on. Restoring the same authored value without an actual value change does not constitute a new control event. Likewise, a host property diff cannot uniquely identify a same-flag program reload or reconstruct repeated raw MIDI messages. These are explicit beta limits; no full MIDI-stream equivalence is claimed.

## Verification and unchanged behavior

The [core receipt](../../Tests/results/sustain-b13-core-validation.json) records17 new test groups and all7 CTest targets passing in Release and ASan/UBSan. Tests cover all128 raw values, coefficient-only continuity, already-released voices, factory overrides, program/live-edit separation, reset/allNotesOff, MIDI/CV ownership, allocation-free rendering and deferred switching through steal fades. A separately compiled b12 baseline and Legacy candidate produce exactly **39,321,600 audio bytes** across100 presets, both pitch laws and44.1/48/96kHz.

The [independent public-API review](../../Tests/results/sustain-b13-independent-review.json) passes11 groups in both Release and ASan/UBSan, including separate audio-equivalence and analytic rate-ratio checks. It does not reuse the candidate's internal test-access helper. Current canonical DSP hashes match the exact reviewed sources recorded in the ledger.

A further [frozen no-CC64 regression](../../Tests/results/sustain-b13-no-CC64-regression.json) passes all **eight complete-WAV comparisons**: Legacy and Original across the four existing event-timing maps each match their b12 baseline exactly. The fixture contains1,761 notes and3,622 events, with the same patches, timing, pitch law and output processing. No timing, gain, envelope or window parameter was fitted. This confirms unchanged recording-benchmark behavior when no pedal messages occur; it is not an original-hardware pedal audio test. The diagnostic float renders can exceed unity and are not evidence of output headroom.

The change adds no Reverb algorithm, new envelope-rate law, DAC transfer, aging fault model or additive noise. Existing historical receipts remain immutable, including their pre-adoption status wording. Source adoption does not itself certify a packaged b13 build or a live Reason test.
