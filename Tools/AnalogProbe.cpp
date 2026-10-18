#include "AnalogOutput.h"
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

int main(int argc, char** argv) {
    try {
        if (argc != 4) throw std::runtime_error("Usage: press78_analog_probe sample_rate frame_count output.f64");
        const double rate = std::stod(argv[1]);
        const int frames = std::stoi(argv[2]);
        if (!std::isfinite(rate) || rate < 8000 || rate > 192000 || frames < 1 || frames > 1920000)
            throw std::runtime_error("Invalid probe rate or length");
        press78::AnalogOutput filter;
        filter.prepare(rate);
        std::ofstream f(argv[3], std::ios::binary);
        if (!f) throw std::runtime_error("Cannot create impulse output");
        for (int i = 0; i < frames; ++i) {
            const double y = filter.process(i == 0 ? 1.0 : 0.0);
            f.write(reinterpret_cast<const char*>(&y), sizeof(y));
        }
        if (!f) throw std::runtime_error("Cannot write impulse output");
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
