# CPU: exact shortcuts in the engine — 2026-10-25

Press78 0.1.14 runs the same engine with about 32 % fewer instructions. The
float32 output of the regression stream is byte-identical to 0.1.13's on all
100 factory voices, in both control profiles, in the Rack-like build and in the
host build. Every mechanism is graded *exact*. None needed a null test or a
listening test.

Baseline: `0b6d7bc` (0.1.13). The commits are on `claude/cool-turing-1yhk67`.

## Protocol

The protocol also sits at the head of
[`Tools/CpuParityBench.cpp`](../../Tools/CpuParityBench.cpp), the tool that
runs it.

- **Build.** No Jukebox SDK was available, so this is the Rack-like build:
  Ubuntu clang 18.1.3, `-std=c++17 -O3 -fno-builtin -DNDEBUG`, with no
  fast-math and no FMA flags. The engine has no embedded define. The host build
  is GCC 13.3 with `-std=c++20 -O3 -DNDEBUG`. Both builds link the same glibc
  libm. Every binary that a figure depends on was rebuilt from its own tree
  before it was measured.
- **Stream.** For each factory voice, the tool plays the committed demo phrase
  `Docs/audio/midi/<NNN>-<slug>.mid`:
  - 48 kHz, in 64-frame blocks (the Rack's batch size);
  - each MIDI event lands on its own sample;
  - every voice starts from a fresh engine.

  There are two profiles:
  - **plug-in**: the plug-in's default controls, the Real startup profile.
    That means YM3420 chip rate, Original pitch, key-level and allocation laws,
    the Recorded chorus through the PSS-270 wet path, AUX, and fresh batteries.
  - **Rack**: the Reason adapter's fixed overrides on top of the plug-in
    defaults. That means legacy 48 kHz chip rate, legacy key-level and
    allocation laws, Circuit saturation off at +12 dB headroom, and 25 % power.
- **Parity.** All 100 factory voices, the first 6 s of each phrase (600 s of
  audio per profile). The interleaved float32 output is compared byte for byte
  (`cmp`) against the 0.1.13 build.
- **Instructions.** `valgrind --tool=callgrind` total Ir for the first 3 s of
  ten voices: PSS 00, 12, 13, 22, 30, 53, 59, 77, 84 and 92 (piano, tremolo and
  jazz organ, trumpet, brass, rock guitar, bass, strings, tubular bells, human
  chorus). Ir is the primary metric, because the machine was shared with five
  other builds and wall-clock times there are not reproducible.

## Per-commit cumulative instruction counts (Rack-like build)

| Commit | Mechanism | Plug-in Ir | Step | Total | Rack Ir | Step | Total | Grade |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `0b6d7bc` | baseline 0.1.13 | 14,043,734,815 | | | 13,119,199,765 | | | |
| `b0e4558` | pack voice state (memory only) | 14,043,721,341 | −0.0 % | −0.0 % | 13,119,186,259 | −0.0 % | −0.0 % | exact |
| `ed038c4` | cache velocity powers by exponent | 12,514,649,257 | −10.9 % | −10.9 % | 11,695,073,947 | −10.9 % | −10.9 % | exact |
| `606a704` | reuse envelope level while attenuation holds | 12,008,069,451 | −4.0 % | −14.5 % | 11,263,327,004 | −3.7 % | −14.1 % | exact |
| `764cde2` | shape shared LFO once per tick | 11,448,649,618 | −4.7 % | −18.5 % | 10,733,518,473 | −4.7 % | −18.2 % | exact |
| `b0bcc21` | skip zero-exponent vibrato/tremolo powers | 11,075,910,077 | −3.3 % | −21.1 % | 10,397,257,341 | −3.1 % | −20.7 % | exact |
| `203559c` | phase wrap without fmod | 10,796,489,302 | −2.5 % | −23.1 % | 10,139,067,424 | −2.5 % | −22.7 % | exact |
| `ee37bdc` | resampler taps without bounds tests | 9,850,773,575 | −8.8 % | −29.9 % | 9,193,384,987 | −9.3 % | −29.9 % | exact |
| `ffc29bf` | share chorus LFO sine | 9,716,964,425 | −1.4 % | −30.8 % | 9,059,575,837 | −1.5 % | −30.9 % | exact |
| `3b23d19` | skip amplifier swing power at exactly 1 | 9,508,604,870 | −2.1 % | −32.3 % | 8,905,004,073 | −1.7 % | −32.1 % | exact |

On the host build (GCC, plug-in profile, same ten voices), the count went from
14,220,949,333 to 9,784,766,591 Ir, which is −31.2 %.

## The mechanisms and why each is exact

- **Velocity powers.** Every tick, each voice computed
  `pow(velocity, velocityToModulation)` and
  `pow(velocityLevel, velocitySensitivity)`. The base is fixed for the note,
  and the smoothed exponent settles. `ExponentCachedPow` returns the last
  result while the exponent compares equal. Equal operands give the same IEEE
  result, and +0 and −0 both give 1.
- **Envelope level.** `pow(10, -att/20)` is reused while the attenuation has
  the same value it had before the step: a held D2R-0 sustain, or a finished
  attack. `next()` is the attenuation's only writer.
- **Shared LFO.** With the global LFO, every voice applied `asin` to the same
  sine. The shaped value is now computed once per tick and passed to
  `Voice::tick`.
- **Zero exponents.** `pow(b, ±0)` is exactly 1, so it is skipped:
  - for the pitch, when the patch has no vibrato or is still inside the
    vibrato delay;
  - for the tremolo, when the AM depth is zero.

  When both operators have tremolo, its gain is computed once. The vibrato
  delay is rounded only for patches that have vibrato.
- **Phase wrap.** `wrapPhase(x)` returns:
  - `x` for x in [0, τ);
  - `x − τ` for x in [τ, 2τ), which is exact by Sterbenz's lemma;
  - `fmod` for everything else.

  A sweep of 2·10⁸ values, plus the boundaries, signed zero, infinity and NaN,
  found no difference from `std::fmod`.
- **Resampler.** The window is entirely retained history after the first 64
  ticks. While that holds, the taps are read through the ring mask and do not
  go through `historyAt`'s three bounds tests. The samples, the coefficients
  and the summation order are all the same. `floor` is now taken once.
- **Chorus sine.** The Studio chorus and the recorded delay law each took
  `sin(chorusPhase_)`. A `delayMilliseconds(sin, cos, depth)` overload now
  shares one sine between them.
- **Amplifier swing.** `(1 + u¹⁰)^-0.1` equals 1 exactly once `1 + u¹⁰`
  rounds to 1, which happens below about 2.5 % of the limit. In that case the
  call is skipped.

The **instance budget** forced the first commit. The output bus must stay
within 196,608 bytes (`Press78OutputBus.h`), and 0.1.13 left only 288 bytes
free. The caches add 48 bytes to each of the 24 voice and tail copies. To make
room, each voice now holds a `VoicePatch`: every patch field except the 33
provenance bytes it never reads, with its members ordered so the struct has no
padding holes. That frees 40 bytes per copy. The final engine is 180,072
bytes, and the bus is 196,512 bytes, 96 under the budget.

## Parity evidence

After each commit, `cmp` of the 600 s float32 render against the 0.1.13
render gave **identical** for both profiles in the Rack-like build. On the
final tree the host build was identical too.

## Tests

| Tests | Result |
| --- | --- |
| `ctest -L unit` (21 tests), after every commit | all passed |
| `ctest -L fuzz` (`Press78.DspFuzz`), final tree | passed |
| `Press78DSPCxx17`, final tree | built |

The `audio` tier (`Press78.AudioDemos`, every demo rendered twice) was not run
in this round. The byte-identical render of the same 100 phrases covers what it
would show for sound. The plug-in build, with `ParameterMatrix` and
`EditorRender`, was not built, because the change is confined to
`Source/DSP/`.

## Candidates not shipped

- The decaying envelopes' `pow(10, -att/20)` as a running product, and
  Cephes-style `sin` kernels for the operators. These would change the last
  bits of the FM index and feedback path, so they need the one-ulp probe and,
  most likely, a listening decision. They are not exact.
- Skipping the Phones path's swing powers while the jack is AUX would leave
  that filter's memory stale when the jack is switched. That makes the change
  audible, and it needs a listening test.
- A doubled history ring, for a contiguous tap window, would need 1 KiB that
  the instance budget does not have.
