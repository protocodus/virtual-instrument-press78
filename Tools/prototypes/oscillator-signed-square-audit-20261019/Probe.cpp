// Research only. Include the unchanged production translation unit so this
// probes its actual anonymous-namespace wave(), not a copied approximation.
#include "Press78Engine.cpp"
#include <cstdio>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    constexpr int n = 65536;
    constexpr double tauProbe = 6.283185307179586476925286766559;
    double error = 0, mean = 0, pmError = 0;
    for (int i = 0; i < n; ++i) {
        const double p = tauProbe * i / n;
        const double s = std::sin(p);
        const double v = press78::wave(p, 1);
        error = std::max(error, std::abs(v - s * std::abs(s)));
        mean += v / n;
        // No DC/shape operation may precede the carrier's PM addition in this
        // software implementation. This checks actual wave() for four fixed
        // PM indices, not an identified hardware PM numerical law.
        for (const double beta : {0.0, 0.25, 1.0, 4.0}) {
            const double phase = p + beta * std::sin(2.0 * p + 0.37);
            const double z = std::sin(phase);
            pmError = std::max(pmError, std::abs(press78::wave(phase, 1) - z * std::abs(z)));
        }
    }
    std::cout << std::setprecision(17)
              << "{\"sample_count\":" << n << ",\"identity_max_error\":" << error
              << ",\"coherent_mean\":" << mean
              << ",\"pm_identity_max_error\":" << pmError << "}\n";
    const double hz = 523.0676963516906;
    for (const bool circuit : {false, true}) {
        press78::Press78Engine engine;
        engine.prepare(48000.0);
        auto p = press78::initPatch();
        p.carrier.wave = 1;
        auto c = engine.controls();
        c.masterGain = 1.0;
        c.masterTuneCents = 1200.0 * std::log2(hz / (440.0 * std::pow(2.0, 3.0 / 12.0)));
        c.velocitySensitivity = 0;
        c.outputCircuit = circuit;
        c.toneCutoffHz = 0;
        c.chorusMix = 0;
        c.drive = 0;
        c.outputLimit = false;
        c.dcBlock = false;
        c.clockOffsetPpm = c.clockDriftPpm = 0;
        engine.setControls(c);
        engine.setPatch(p);
        engine.noteOn(72, 127);
        std::vector<float> left(48000), right(48000);
        engine.process(left.data(), right.data(), left.size());
        const std::string path = std::string(argv[1]) + (circuit ? "/circuit.f32" : "/dry.f32");
        std::ofstream f(path, std::ios::binary);
        f.write(reinterpret_cast<const char*>(left.data()), left.size() * sizeof(float));
        if (!f) return 3;
    }
}
