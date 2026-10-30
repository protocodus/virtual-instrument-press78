#pragma once
#include <array>
#include <cmath>
#include <cstddef>
#include "FastMath.h"

namespace press78 {
// One small linear circuit stage, b(s)/a(s) with coefficients in ascending
// powers of s, discretised by the bilinear transform. The transform is
// prewarped at matchHz (kept below Nyquist), where the digital response then
// equals the analog one; DC is always exact.
template <std::size_t N>
class AnalogFilter {
public:
    using Coefficients = std::array<double, N + 1>;
    void design(const Coefficients& b, const Coefficients& a, double sampleRate, double matchHz) noexcept {
        const double pi = 3.14159265358979323846;
        const double f = std::fmin(matchHz, 0.45 * sampleRate);
        const double k = 2.0 * pi * f / std::tan(pi * f / sampleRate);
        Coefficients num{}, den{};
        double power = 1.0;
        for (std::size_t i = 0; i <= N; ++i) {
            // (1 - x)^i (1 + x)^(N - i), x = z^-1, in ascending powers of x.
            Coefficients term{}; term[0] = power;
            for (std::size_t j = 0; j < N; ++j) {
                const double sign = j < i ? -1.0 : 1.0;
                for (std::size_t m = j + 1; m > 0; --m) term[m] += sign * term[m - 1];
            }
            for (std::size_t m = 0; m <= N; ++m) { num[m] += b[i] * term[m]; den[m] += a[i] * term[m]; }
            power *= k;
        }
        for (std::size_t m = 0; m <= N; ++m) b_[m] = num[m] / den[0];
        for (std::size_t m = 1; m <= N; ++m) a_[m - 1] = den[m] / den[0];
        reset();
    }
    void reset() noexcept { state_.fill(0.0); }
    bool settled() const noexcept {
        for (const double s : state_) if (!fast_math::settled(s)) return false;
        return true;
    }
    void copyStateFrom(const AnalogFilter& other) noexcept { state_ = other.state_; }
    double process(double x) noexcept {
        if (x == 0.0 && settled()) state_.fill(0.0);
        const double y = b_[0] * x + state_[0];
        for (std::size_t m = 1; m < N; ++m) state_[m - 1] = b_[m] * x - a_[m - 1] * y + state_[m];
        state_[N - 1] = b_[N] * x - a_[N - 1] * y;
        return y;
    }

private:
    Coefficients b_{};
    std::array<double, N> a_{}, state_{};
};
} // namespace press78
