#pragma once

#include <cmath>

namespace press78::hardware_character {

// User-selected B audition, 2026-10-19; see Docs/decisions.md and the frozen
// assumed-hardware-auditions report. These are chosen modeling assumptions,
// not recovered YM3420 values. No additive noise or electrical excitation.
constexpr double kReleaseKneeDb = 18.0;
constexpr double kHeadroom = 1.0;
constexpr double kBias = 0.14;
// tanh(.14), rounded to binary64; immutable for the SDK's -fno-builtin build.
constexpr double kBiasTanh = 0.13909244787845804;

// Shared zero-centered biased soft headroom, upstream of the sibling filter.
// y = H*tanh(x/H)/(1+tanh(b)*tanh(x/H)); unity small-signal slope, asymmetric
// limits. H/b and placement were chosen by ear, not calibrated in volts.
// Runs at the existing output rate: no claim of identified ASIC aliasing.
inline double output(double input) noexcept {
    const double t = std::tanh(input / kHeadroom);
    return kHeadroom * t / (1.0 + kBiasTanh * t);
}

} // namespace press78::hardware_character
