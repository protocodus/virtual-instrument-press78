#pragma once
#include <cmath>

namespace press78::research {

// Assumed shared output headroom, NOT an identified YM3420/DAC transfer.
// Constants are normalized audition choices; they are not circuit volts.
// No mutable state, excitation, quantization, noise, or startup DC is added.
class OutputHypothesis {
public:
    static constexpr double kHeadroom = 1.0;
    static constexpr double kBias = 0.14;
    static constexpr double kIllustrativeReferencePeak = 0.25;

    // A numerically stable zero-centered biased tanh with unity slope at zero:
    // H * (tanh(x/H+b)-tanh(b)) / (1-tanh(b)^2).
    // Its equivalent form below avoids subtracting nearby tanh values.
    static double process(double input) noexcept {
        const double t = std::tanh(input / kHeadroom);
        const double bias = std::tanh(kBias);
        return kHeadroom * t / (1.0 + bias * t);
    }

    static double positiveLimit() noexcept {
        return kHeadroom / (1.0 + std::tanh(kBias));
    }
    static double negativeLimit() noexcept {
        return -kHeadroom / (1.0 - std::tanh(kBias));
    }
};

} // namespace press78::research
