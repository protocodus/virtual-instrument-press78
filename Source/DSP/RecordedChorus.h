#pragma once
#include "RecordedChorusProfile.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>

namespace press78 {
// Causal v3 effective transfer. The input is a proposed recorded mid, not
// established raw chip voltage. This standalone fixture and the native engine
// use the same delay law. No nonlinearities or noise are attributed to hardware.
class RecordedChorus {
public:
    static constexpr std::size_t kDelaySize = 4096;
    static constexpr double kTau = 6.283185307179586476925286766559;
    void prepare(double sampleRate, double startSeconds = 0.0) noexcept {
        sampleRate_ = finiteClamp(sampleRate, 8000.0, 192000.0, 48000.0);
        reset(startSeconds);
    }
    void reset(double startSeconds = 0.0) noexcept {
        delay_.fill(0.0); write_ = 0; samples_ = 0;
        // A bounded capture coordinate; ordinary playback starts at0. Changing
        // rate after reset retains phase, matching a continuously running LFO.
        startSeconds = finiteClamp(startSeconds, -1e6, 1e6, 0.0);
        phase_ = std::fmod(kTau * rate_ * startSeconds, kTau);
        if (phase_ < 0) phase_ += kTau;
    }
    void setParameters(double rateHz, double fundamentalDepthMs) noexcept {
        rate_ = finiteClamp(rateHz, 0.05, 8.0, RecordedChorusProfile::rateHz);
        depth_ = finiteClamp(fundamentalDepthMs, 0.0, 8.0, RecordedChorusProfile::depthMs);
    }
    static double delayMilliseconds(double phase, double fundamentalDepthMs) noexcept {
        return delayMilliseconds(std::sin(phase), std::cos(phase), fundamentalDepthMs);
    }
    // The same law from sin(phase) and cos(phase), for a caller that already
    // holds the sine.
    static double delayMilliseconds(double s, double c, double fundamentalDepthMs) noexcept {
        using P = RecordedChorusProfile;
        const double scale = fundamentalDepthMs / P::depthMs;
        // Deep settings are a documented creative extension: increase the mean
        // enough to retain the profile's conservative positive-delay bound.
        // At/below reference depth the measured mean remains unchanged.
        const double mean = P::meanMs + std::max(0.0, scale - 1.0) * P::excursionBoundMs;
        return mean + scale * (P::sin1Ms*s + P::cos1Ms*c
                              + P::sin2Ms*(2.0*s*c) + P::cos2Ms*(c*c-s*s));
    }
    static double side(double mid, double wet) noexcept {
        return RecordedChorusProfile::wetGain * wet + RecordedChorusProfile::midLeakGain * mid;
    }
    void process(double input, double& left, double& right) noexcept {
        if (!std::isfinite(input)) input = 0.0;
        delay_[write_] = input;
        const double samples = delayMilliseconds(phase_, depth_) * 0.001 * sampleRate_;
        const auto whole = static_cast<std::size_t>(samples);
        const double fraction = samples - static_cast<double>(whole);
        const auto a = (write_ + kDelaySize - whole) % kDelaySize;
        const auto b = (a + kDelaySize - 1) % kDelaySize;
        const double wet = samples > static_cast<double>(samples_) ? 0.0
            : delay_[a] + fraction * (delay_[b] - delay_[a]);
        const double s = side(input, wet);
        left = input + s; right = input - s;
        write_ = (write_ + 1) % kDelaySize;
        ++samples_;
        phase_ = std::fmod(phase_ + kTau * rate_ / sampleRate_, kTau);
    }
private:
    static double finiteClamp(double x, double lo, double hi, double fallback) noexcept {
        return std::isfinite(x) ? std::clamp(x, lo, hi) : fallback;
    }
    std::array<double, kDelaySize> delay_{};
    std::size_t write_ = 0;
    std::size_t samples_ = 0;
    double sampleRate_ = 48000.0, phase_ = 0.0;
    double rate_ = RecordedChorusProfile::rateHz, depth_ = RecordedChorusProfile::depthMs;
};
} // namespace press78
