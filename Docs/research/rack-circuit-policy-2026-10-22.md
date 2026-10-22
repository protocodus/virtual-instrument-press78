# Rack circuit policy — 2026-10-22

The owner reported unwanted coloration on the Reason Init sound and other
presets at ordinary velocity, asking whether it was authentic and requesting
a fix. The current Rack adapter uses the preamp output and Ideal power; its
battery amplifier is bypassed. The added shared biased-tanh character is the
ear-selected B assumption recorded in `Docs/decisions.md`, not an identified
Yamaha transfer. The previous Rack headroom adjustment reduced, but did not
remove, that character.

Yamaha's [PSS-780 owner's manual](https://www.nurykabe.com/dump/docs/PSS/manuals/PSS-780_00.pdf),
printed pages 11 and 29, warns about distortion at high voice level and maximum
melody volume, especially chords. It does not establish a distortion amount
for an ordinary Init note. The [AN7148 manufacturer data](https://datasheet.octopart.com/AN7148-Panasonic-datasheet-180974205.pdf),
page 2, specifies 0.20% typical THD at 9 V, 4 ohms, 3 mV input and 1 kHz;
that amplifier condition does not calibrate the upstream shared preamp curve.

The portable API now separates `circuitSaturation` from `outputCircuit`.
Its default is true, preserving the existing native character and old callers.
Rack can select false while retaining the complete linear sibling filter.
The transition uses the existing 5 ms smoothing and snaps on startup/reset.
The separate battery/adaptor amplifier, Drive, output protection and release
model retain their behavior. `circuitHeadroom` also makes the previously local
Rack gain-staging policy a canonical, bounded host option instead of requiring
a dirty submodule patch. Both options are internal host policy, not new native
plug-in parameters or calibrated hardware controls.

All 21 native unit suites pass in normal and ASan/UBSan builds, including the
new linearity/filter-retention and live/reset policy witnesses. C++17 compiles.
A 108-case render comparison against canonical `4e56f44` is byte-identical with
legacy defaults across four patches, all output jacks, all supplies and three
velocities, including two-note playing and release. The Rack adapter separately
validates its intended changed sound and preset headroom. No new target or
actual-host playback is claimed by these native checks.
