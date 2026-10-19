// Bounded research probe. Protocol: design-frozen.json in this directory.
// Compile this file alone; it includes the unchanged engine to inspect the
// actual wave helper and uses its preexisting friend test seam. No patching,
// guessed OPU word widths, new noise, or production DSP change is involved.
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <vector>
#include "../../../Source/DSP/Press78Engine.cpp"

namespace {
constexpr double p = 3.14159265358979323846264338327950288;
constexpr double tp = 2 * p;
std::size_t assertions = 0;
void require(bool condition, const char* description) {
    ++assertions;
    if (!condition) {
        std::cerr << "FAILED: " << description << '\n';
        std::exit(1);
    }
}
double half(double phase) { return std::max(std::sin(phase), 0.0); }
press78::Controls isolated() {
    press78::Controls c;
    c.masterGain = 1;
    c.outputCircuit = false;
    c.toneCutoffHz = 0;
    c.outputLimit = false;
    c.chorusMix = 0;
    c.drive = 0;
    return c;
}
}

namespace press78 {
struct Press78SustainTestAccess {
    static double voiceEquationError() {
        double error = 0;
        const std::array<std::array<int, 2>, 4> ratios{{{{1, 1}}, {{1, 2}}, {{2, 1}}, {{3, 2}}}};
        for (int tl : {0, 17, 49}) for (int note : {36, 60, 84}) for (const auto& ratio : ratios) {
            Patch patch;
            patch.modulator.wave = 2;
            patch.modulator.tl = tl;
            patch.modulator.mul = ratio[1];
            patch.carrier.mul = ratio[0];
            Press78Engine::Voice voice;
            voice.configure(patch, note, 127, 0);
            const double gain = std::pow(10.0, -tl * .75 / 20.0);
            const auto c = isolated();
            for (int n = 0; n < 4800; ++n) {
                const double actual = voice.next(c, 1, 0);
                const double expected = .8 * std::sin(voice.carrierPhase + 8 * p * gain * half(voice.modPhase));
                error = std::max(error, std::abs(actual - expected));
                require(std::abs(actual - expected) <= 1e-12, "actual Voice phase-modulation equation");
            }
        }
        return error;
    }
    static double processOutput(Press78Engine& e, double x) {
        double left = 0, right = 0;
        e.output(x, left, right);
        require(left == right, "isolated output is mono");
        return left;
    }
};
}

int main() {
    constexpr int quadrature = 262144;
    double mean = 0;
    std::array<double, 12> sine{}, cosine{};
    for (int n = 0; n < quadrature; ++n) {
        const double phase = tp * n / quadrature;
        const double value = press78::wave(phase, 2);
        require(value == half(phase), "current table2 equals analytic positive half sine");
        require(value >= 0 && value <= 1, "half-sine range");
        mean += value / quadrature;
        for (int k = 1; k <= 12; ++k) {
            sine[k - 1] += 2.0 * value * std::sin(k * phase) / quadrature;
            cosine[k - 1] += 2.0 * value * std::cos(k * phase) / quadrature;
        }
    }
    require(std::abs(mean - 1 / p) < 1e-9, "analytic half-sine mean");
    double coefficientError = 0;
    for (int k = 1; k <= 12; ++k) {
        const double expectedSine = k == 1 ? .5 : 0;
        const double expectedCosine = k % 2 ? 0 : -2.0 / (p * (k * k - 1));
        coefficientError = std::max({coefficientError, std::abs(sine[k - 1] - expectedSine),
                                      std::abs(cosine[k - 1] - expectedCosine)});
        require(std::abs(sine[k - 1] - expectedSine) < 1e-9, "analytic sine Fourier coefficient");
        require(std::abs(cosine[k - 1] - expectedCosine) < 1e-9, "analytic cosine Fourier coefficient");
    }

    const double voiceError = press78::Press78SustainTestAccess::voiceEquationError();
    auto c = isolated();
    press78::Press78Engine unipolar, centered;
    unipolar.setControls(c); centered.setControls(c);
    unipolar.reset(); centered.reset();
    const double pole = std::exp(-tp * 10 / 48000.0);
    double dcError = 0, dcFinal = 0;
    for (int n = 0; n < 48000; ++n) {
        const double signal = half(tp * 125 * n / 48000.0);
        const double a = press78::Press78SustainTestAccess::processOutput(unipolar, signal);
        const double b = press78::Press78SustainTestAccess::processOutput(centered, signal - 1 / p);
        const double expected = std::pow(pole, n) / p;
        dcError = std::max(dcError, std::abs(a - b - expected));
        dcFinal = a - b;
        require(std::abs(a - b - expected) <= 1e-10, "output-DC null pair closed form");
    }

    double phaseIdentityError = 0, derivativeError = 0, constantDerivative = 0;
    double previousDelta = 0, previousGain = 0;
    for (int n = 0; n < 48000; ++n) {
        const double time = n / 48000.0;
        const double gain = time < .1 ? 2 * time : time < .3 ? .2 : time < .4 ? .8 - 2 * time : 0;
        const double m = half(tp * 125 * time);
        const double carrier = tp * 125 * time;
        const double delta = (carrier + 8 * p * gain * m) - (carrier + 8 * p * gain * (m - 1 / p));
        phaseIdentityError = std::max(phaseIdentityError, std::abs(delta - 8 * gain));
        require(std::abs(delta - 8 * gain) <= 1e-11, "phase delta equals 8*g");
        if (n > 0) {
            const double measured = (delta - previousDelta) * 48000 / tp;
            const double expected = 4 / p * (gain - previousGain) * 48000;
            derivativeError = std::max(derivativeError, std::abs(measured - expected));
            require(std::abs(measured - expected) <= 1e-7, "phase-delta derivative identity");
            if (time > .11 && time < .29) constantDerivative = std::max(constantDerivative, std::abs(measured));
        }
        previousDelta = delta; previousGain = gain;
    }
    require(constantDerivative <= 1e-7, "constant modulator mean is not steady detuning");

    unipolar.reset(); centered.reset();
    double squaredDifference = 0, squaredBaseline = 0;
    for (int n = 0; n < 48000; ++n) {
        const double phase = tp * 125 * n / 48000.0;
        const double m = half(phase);
        const double a = press78::Press78SustainTestAccess::processOutput(unipolar, std::sin(phase + 8 * p * .2 * m));
        const double b = press78::Press78SustainTestAccess::processOutput(centered, std::sin(phase + 8 * p * .2 * (m - 1 / p)));
        if (n >= 24000) { squaredDifference += (a - b) * (a - b); squaredBaseline += a * a; }
    }
    const double postDcDifference = std::sqrt(squaredDifference / squaredBaseline);
    require(postDcDifference > 1e-3, "post-carrier DC filter is not operator-mean subtraction");

    std::cout << std::setprecision(17)
      << "{\"passed\":true,\"assertions\":" << assertions
      << ",\"quadrature_samples\":" << quadrature
      << ",\"half_sine_mean\":" << mean
      << ",\"mean_abs_error\":" << std::abs(mean - 1 / p)
      << ",\"fourier_coefficient_max_abs_error\":" << coefficientError
      << ",\"native_voice_equation_max_abs_error\":" << voiceError
      << ",\"native_voice_cases\":36,\"native_voice_ticks_per_case\":4800"
      << ",\"output_dc_null_pair_max_abs_error\":" << dcError
      << ",\"output_dc_null_pair_final_abs_difference\":" << std::abs(dcFinal)
      << ",\"phase_identity_max_abs_error\":" << phaseIdentityError
      << ",\"phase_derivative_max_abs_error_hz\":" << derivativeError
      << ",\"constant_mean_max_steady_delta_hz\":" << constantDerivative
      << ",\"post_dc_centered_vs_unipolar_relative_rms\":" << postDcDifference
      << ",\"scope\":\"mathematical/current-source verification only, not OPU DC-bias identification\"}\n";
}
