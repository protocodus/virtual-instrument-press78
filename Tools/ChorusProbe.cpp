#include "RecordedChorus.h"
#include <array>
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

// Raw native-endian IEEE float64 mono input -> interleaved float64 stereo.
// Scientific fixture, no normalization. Standalone effect excludes FM/output.
int main(int argc, char** argv) {
    try {
        if (argc < 5 || argc > 7) throw std::runtime_error("Usage: chorus_probe rate start_seconds input.f64 output.f64 [lfo_rate depth_ms]");
        const double sr = std::stod(argv[1]), start = std::stod(argv[2]);
        if (!std::isfinite(sr) || sr < 8000 || sr > 192000 || !std::isfinite(start) || std::abs(start) > 1e6)
            throw std::runtime_error("Invalid sample rate or capture epoch");
        press78::RecordedChorus effect;
        if (argc == 7) effect.setParameters(std::stod(argv[5]), std::stod(argv[6]));
        effect.prepare(sr, start);
        std::ifstream in(argv[3], std::ios::binary);
        std::ofstream out(argv[4], std::ios::binary);
        if (!in || !out) throw std::runtime_error("Cannot open fixture files");
        std::size_t frames = 0;
        double x;
        while (in.read(reinterpret_cast<char*>(&x), sizeof(x))) {
            if (!std::isfinite(x)) throw std::runtime_error("Nonfinite fixture input");
            std::array<double, 2> y{}; effect.process(x, y[0], y[1]);
            out.write(reinterpret_cast<const char*>(y.data()), sizeof(y)); ++frames;
        }
        if (in.gcount() || !out) throw std::runtime_error("Truncated input or output write failure");
        std::cout << "frames=" << frames << '\n';
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
