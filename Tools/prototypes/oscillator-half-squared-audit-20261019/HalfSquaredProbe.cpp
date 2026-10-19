// Research only: exactly the adjacent design-frozen.json, no signal render.
// Including the implementation checks its actual private wave helper without
// changing production visibility or hypothesizing OPU arithmetic precision.
#include <array>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include "../../../Source/DSP/Press78Engine.cpp"

namespace {
constexpr double p = 3.14159265358979323846264338327950288;
std::size_t checks = 0;
void require(bool condition, const char* description) {
    ++checks;
    if (!condition) {
        std::cerr << "FAILED: " << description << '\n';
        std::exit(1);
    }
}
}

int main() {
    constexpr int count = 65536;
    double mean = 0, maxIdentityError = 0;
    std::array<double, 12> sine{}, cosine{};
    for (int n = 0; n < count; ++n) {
        const double phase = 2 * p * n / count;
        const double s = press78::wave(phase, 0);
        const double q = press78::wave(phase, 1);
        const double h = press78::wave(phase, 2);
        const double r = press78::wave(phase, 3);
        const double identityError = std::abs(r - .5 * (s * s + q));
        maxIdentityError = std::max(maxIdentityError, identityError);
        require(r >= 0 && r <= 1, "HALF squared range");
        require(std::abs(r - h * h) <= 1e-15, "actual HALF squared equals HALF times HALF");
        require(identityError <= 1e-15, "actual HALF squared equals (sine squared plus signed square)/2");
        require(r == (s < 0 ? 0 : q), "actual gated signed-square identity");
        mean += r / count;
        for (int harmonic = 1; harmonic <= 12; ++harmonic) {
            sine[harmonic - 1] += 2 * r * std::sin(harmonic * phase) / count;
            cosine[harmonic - 1] += 2 * r * std::cos(harmonic * phase) / count;
        }
    }
    require(std::abs(mean - .25) <= 1e-9, "HALF squared mean is one quarter");
    double maximumCoefficientError = 0;
    for (int n = 1; n <= 12; ++n) {
        const double targetSine = n % 2 ? -4.0 / (p * n * (n * n - 4)) : 0;
        const double targetCosine = n == 2 ? -.25 : 0;
        maximumCoefficientError = std::max(maximumCoefficientError,
            std::max(std::abs(sine[n - 1] - targetSine), std::abs(cosine[n - 1] - targetCosine)));
        require(std::abs(sine[n - 1] - targetSine) <= 1e-9, "HALF squared analytic sine coefficient");
        require(std::abs(cosine[n - 1] - targetCosine) <= 1e-9, "HALF squared analytic cosine coefficient");
    }
    std::cout << std::setprecision(17)
              << "{\"passed\":true,\"assertions\":" << checks
              << ",\"period_points\":" << count << ",\"mean\":" << mean
              << ",\"maximum_pointwise_identity_error\":" << maxIdentityError
              << ",\"maximum_fourier_coefficient_error\":" << maximumCoefficientError
              << ",\"sine_coefficients\":[";
    for (int n = 0; n < 12; ++n) std::cout << (n ? "," : "") << sine[n];
    std::cout << "],\"cosine_coefficients\":[";
    for (int n = 0; n < 12; ++n) std::cout << (n ? "," : "") << cosine[n];
    std::cout << "]}\n";
}
