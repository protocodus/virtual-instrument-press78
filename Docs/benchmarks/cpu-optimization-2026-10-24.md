# Exact CPU reductions — 0.1.14 (2026-10-24)

Four engine changes cut the native engine's CPU time by 25–30 % with the
output unchanged bit for bit. This is a development-container measurement of
`Press78Engine` alone, not a Reason or plug-in host result and not a realtime
guarantee.

## Changes

| Commit | Change | Instructions | Process CPU time |
| --- | --- | --- | --- |
| `f7902ca` | Skip `std::pow` where the result is exact (x⁰ = 1, x¹ = x, 1ʸ = 1): the default Velocity to FM and Velocity to level exponents, a voice without vibrato or tremolo, an envelope at full level, a quiet amplifier swing; one tremolo gain for both operators | −16.4 % | −11.8 % (9 pairs) |
| `382b40b` | Shape the shared triangle LFO once per tick, not once per voice | −4.3 % | −2.3 % (15 pairs; a second set of 9: −2.2 %) |
| `25f5809` | Read the 64 resampler taps without per-tap history bounds tests when the window is retained (always, after the first ticks) | −7.2 % | −2.8 % (9 pairs) |
| `ca43d7f` | Wrap oscillator and LFO phases by one subtraction instead of `std::fmod` when they advanced by less than a turn | −1.4 % | −15.8 % (9 pairs) |

Each row is measured against the commit before it. GCC inlines `fmod` as an
x87 `fprem` loop, one slow instruction, which is why the last change saves
little in instructions and much in time. The resampler's sum must keep its
order, so its dependent add chain bounds what the third change can save.

Overall, 0.1.13 (`0b6d7bc`) against 0.1.14's engine:

| Workload | Phrases | Process CPU time, median of 7 paired runs |
| --- | --- | --- |
| Plug-in defaults, 48 kHz | 10 | 7.243 s → 5.228 s, −27.1 % |
| Engine legacy profile, 48 kHz | 10 | 6.756 s → 4.718 s, −30.0 % |
| Plug-in defaults, 96 kHz | 5 | 4.218 s → 3.193 s, −24.7 % |
| Plug-in defaults, 44.1 kHz | 5 | 3.033 s → 2.180 s, −27.4 % |

Instructions, plug-in defaults at 48 kHz, 3 phrases: 17,801,716,837 →
13,018,203,190 (−26.9 %).

## Exactness

Every change keeps the arithmetic each sample sees:

- `pow(x, ±0)` is 1 and `pow(1, y)` is 1 for every argument (C17 F.10.4.4).
  `pow(x, 1)` is x for a correctly rounded `pow`; glibc 2.39 returns x for
  every velocity level and every Mode 99 level and for 10⁸ random bases in
  [0, 4). A libm that does not would differ by at most one unit in the last
  place of a gain.
- `fmod` is exact, and so is x − 2π for 2π ≤ x < 4π (Sterbenz lemma), so the
  phase wrap returns `fmod`'s value; larger steps, negative and non-finite
  phases still call `fmod`.
- The LFO and resampler changes perform the same operations in the same
  order.

Each commit was rendered and compared sample by sample against 0.1.13: every
factory voice's demo phrase (`Docs/audio/midi`, 100 phrases) at 48 kHz with
the plug-in's default controls and with the engine's own defaults plus Studio
chorus 0.5 and drive 0.2 (legacy chip rate, ideal supply, Preamp), and every
third phrase at 44.1 and 96 kHz with the plug-in defaults, every third at
44.1 kHz and every fifth at 96 kHz in the legacy profile. All six sets, about
1.95 GB of float32 output per commit, were bit-identical.

The Rack instance budget is unchanged: no change adds engine state
(`Press78OutputBus` stays at 196,344 of 196,608 bytes). Two memoising
alternatives were rejected for that reason (below).

## Protocol

A scratch harness drove `Press78Engine` exactly as `Tools/RenderPresetDemos.cpp`
does: one demo phrase per factory voice, events on their own sample, blocks of
256 frames, the plug-in's default control values written with each voice's
patch. It was compiled as the Release build compiles the engine (g++ 13.3,
`-O3 -DNDEBUG`, C++20, no `-march`, no fast-math) from a frozen copy of each
commit's `Source/`, so baseline and candidate binaries differ only in the
engine. The timed region is the render loop only; it reports process CPU time
(`CLOCK_PROCESS_CPUTIME_ID`), because the four-core container was shared with
other builds at a load average of 14–18 and wall time was not repeatable.
Each comparison ran one warm-up of each binary, then alternated the order of
the pair on every repeat and took the median of the per-pair ratios. An
A/A run of two copies of one binary gave paired ratios between 0.975 and
1.053, so single-digit gains were accepted only when repeated sets agreed.
Instruction counts come from `valgrind --tool=callgrind` on phrases 1, 35
and 69 with the plug-in defaults at 48 kHz.

Machine: Intel Xeon @ 2.10 GHz, 4 vCPUs, Linux 6.18, glibc 2.39.

## Rejected

- **Memoising each voice's powers and envelope levels** (last argument and
  result per voice and envelope): bit-identical, but it grew the engine by
  about 2.9 kB and broke the Rack instance budget's `static_assert`, which
  had 264 bytes to spare.
- **Memoising only the envelope level**: the demo phrases rarely hold an
  envelope still, so it executed more instructions (13.40 G against
  13.21 G), and it too needed state.
- **Sharing the chorus LFO's sine between the Studio and recorded delays**:
  GCC already shares it; no change in instructions.
- **Skipping the modulator's sine while its level is zero**: only 4 % of
  voice ticks qualify, and it changes the sign of some zeros.

Remaining cost is mostly two `sin` and two `pow` per voice tick (the operator
waveforms and envelope levels) and the resampler's in-order 64-tap sum, none
of which can change without changing the output.

## Tests

On 0.1.14's engine, `build-dsp` (Release, tools and tests): all 23 CTest
tests pass, including `Press78.AudioDemos` (every demo rendered twice,
bit-identical) and `Press78.DspFuzz`; `Press78DSPCxx17` builds. The unit tier
also passed at each intermediate commit. The plug-in build's
`Press78.PluginProcessor`, `Press78.ParameterMatrix` and `Press78.EditorRender`
were not run: the container lacks JUCE's X11, ALSA and GTK development
packages.
