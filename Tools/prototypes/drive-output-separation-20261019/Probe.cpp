#include "Press78Engine.h"

#include <algorithm>
#include <array>
#include <cstdio>
#include <iostream>
#include <string>

int main() {
    static_assert(sizeof(float) == 4, "The frozen pipe format requires float32");
    std::string mode;
    int tl = 0, count = 0, a = 0, b = 0;
    double gain = 0.0;
    while (std::cin >> mode >> tl >> gain >> count >> a >> b) {
        if ((count != 1 && count != 2) || tl < 0 || tl > 127 || gain < 0 || gain > 2)
            return 2;
        press78::Press78Engine engine;
        engine.prepare(48000.0);
        auto patch = press78::initPatch();
        patch.carrier.tl = tl;
        if (mode == "fm0" || mode == "fm6") patch.modulator.tl = 24;
        patch.feedback = mode == "fm6" ? 6 : 0;
        press78::Controls controls;
        controls.masterGain = gain;
        controls.velocitySensitivity = 0;
        controls.outputCircuit = mode == "circuit";
        controls.drive = mode == "drive" ? 1.0 : 0.0;
        controls.outputLimit = mode == "limit";
        controls.toneCutoffHz = 0;
        controls.dcBlock = false;
        controls.chorusMix = 0;
        engine.setPatch(patch);
        engine.setControls(controls);
        engine.noteOn(a, 127);
        if (count == 2) engine.noteOn(b, 127);
        std::array<float, 64> left{}, right{};
        constexpr int frames = 28800;
        for (int position = 0; position < frames; position += 64) {
            const auto n = static_cast<std::size_t>(std::min(64, frames - position));
            engine.process(left.data(), right.data(), n);
            for (std::size_t index = 0; index < n; ++index)
                if (left[index] != right[index]) return 3;
            if (std::fwrite(left.data(), sizeof(float), n, stdout) != n) return 4;
        }
    }
    return std::ferror(stdout) ? 5 : 0;
}
