#include "Press78OutputBus.h"
#include "RecordedChorusProfile.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void u32(std::ostream& out, std::uint32_t x) {
    for (int i = 0; i < 4; ++i) out.put(static_cast<char>((x >> (8 * i)) & 255));
}
void u16(std::ostream& out, std::uint16_t x) {
    out.put(static_cast<char>(x & 255)); out.put(static_cast<char>(x >> 8));
}
void sample(std::ostream& out, float x) {
    std::uint32_t bits; std::memcpy(&bits, &x, sizeof(bits)); u32(out, bits);
}
void writeWav(const std::string& filename, const std::vector<float>& left,
              const std::vector<float>& right, int rate) {
    std::ofstream f(filename, std::ios::binary);
    if (!f) throw std::runtime_error("Cannot open output WAV");
    const auto bytes = static_cast<std::uint32_t>(left.size() * 8);
    f.write("RIFF", 4); u32(f, 36 + bytes); f.write("WAVEfmt ", 8); u32(f, 16);
    u16(f, 3); u16(f, 2); u32(f, static_cast<std::uint32_t>(rate));
    u32(f, static_cast<std::uint32_t>(rate * 8)); u16(f, 8); u16(f, 32);
    f.write("data", 4); u32(f, bytes);
    for (std::size_t i = 0; i < left.size(); ++i) { sample(f, left[i]); sample(f, right[i]); }
    if (!f) throw std::runtime_error("Cannot write output WAV");
}
std::array<std::uint8_t, 33> decodeHex(const std::string& hex) {
    if (hex.size() != 66) throw std::runtime_error("--raw requires 66 hexadecimal characters (33 decoded bytes)");
    const auto digit = [](char c) -> int {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        if (c >= 'A' && c <= 'F') return c - 'A' + 10;
        throw std::runtime_error("Invalid hexadecimal digit");
    };
    std::array<std::uint8_t, 33> bytes{};
    for (std::size_t i = 0; i < bytes.size(); ++i) bytes[i] = static_cast<std::uint8_t>((digit(hex[2*i]) << 4) | digit(hex[2*i+1]));
    return bytes;
}
} // namespace

int main(int argc, char** argv) {
    try {
        press78::Patch patch = press78::initPatch();
        press78::Controls controls;
        int rate = 48000, note = 60, velocity = 100;
        double duration = 3.0, gate = 1.5;
        std::string output;
        for (int i = 1; i < argc; ++i) {
            const std::string arg = argv[i];
            if (arg == "--real") {
                controls.pitchModel = 1; controls.sustainMode = 1; controls.keyLevelModel = 1;
                controls.allocationModel = 1; controls.chorusCircuit = 1; controls.outputJack = 1;
                controls.chipRate = 1; controls.powerSupply = 1;
                controls.clockOffsetPpm = 0; controls.clockDriftPpm = 20;
                controls.clockDriftRateHz = 0.1; controls.outputCircuit = true;
                controls.envelopeReverb = true;
                controls.chorusMode = 1; controls.chorusMix = 1;
                controls.chorusRateHz = press78::RecordedChorusProfile::rateHz;
                controls.chorusDepthMs = press78::RecordedChorusProfile::depthMs;
                controls.drive = 0;
                continue;
            }
            if (arg == "--transparent") {
                controls.masterGain = 1.0; controls.toneCutoffHz = 0.0;
                controls.dcBlock = false; controls.outputLimit = false; controls.outputCircuit = false;
                controls.envelopeReverb = false;
                continue;
            }
            if (i + 1 >= argc) throw std::runtime_error("Missing value for " + arg);
            const std::string value = argv[++i];
            if (arg == "--raw") patch = press78::decodeVoice(decodeHex(value));
            else if (arg == "--output") output = value;
            else if (arg == "--rate") rate = std::stoi(value);
            else if (arg == "--note") note = std::stoi(value);
            else if (arg == "--velocity") velocity = std::stoi(value);
            else if (arg == "--seconds") duration = std::stod(value);
            else if (arg == "--gate") gate = std::stod(value);
            else if (arg == "--gain") controls.masterGain = std::stod(value);
            else if (arg == "--sustain-mode") {
                if (value == "legacy" || value == "0") controls.sustainMode = 0;
                else if (value == "original" || value == "1") controls.sustainMode = 1;
                else throw std::runtime_error("--sustain-mode requires legacy|original|0|1");
            }
            else if (arg == "--pitch-model") {
                if (value == "equal" || value == "0") controls.pitchModel = 0;
                else if (value == "original" || value == "1") controls.pitchModel = 1;
                else throw std::runtime_error("--pitch-model requires equal|original|0|1");
            }
            else if (arg == "--key-level-model") {
                if (value == "legacy" || value == "0") controls.keyLevelModel = 0;
                else if (value == "original" || value == "1") controls.keyLevelModel = 1;
                else throw std::runtime_error("--key-level-model requires legacy|original|0|1");
            }
            else if (arg == "--allocation-model") {
                if (value == "legacy" || value == "0") controls.allocationModel = 0;
                else if (value == "original" || value == "1") controls.allocationModel = 1;
                else throw std::runtime_error("--allocation-model requires legacy|original|0|1");
            }
            else if (arg == "--chorus-circuit") {
                if (value == "legacy" || value == "0") controls.chorusCircuit = 0;
                else if (value == "pss270" || value == "1") controls.chorusCircuit = 1;
                else throw std::runtime_error("--chorus-circuit requires legacy|pss270|0|1");
            }
            else if (arg == "--output-jack") {
                if (value == "preamp" || value == "0") controls.outputJack = 0;
                else if (value == "aux" || value == "1") controls.outputJack = 1;
                else if (value == "phones" || value == "2") controls.outputJack = 2;
                else throw std::runtime_error("--output-jack requires preamp|aux|phones|0|1|2");
            }
            else if (arg == "--power") {
                controls.powerSupply = value == "ideal" ? 0 : 1;
                if (value == "batteries") controls.power = 100;
                else if (value == "adaptor" || value == "ac") controls.power = 101;
                else if (value != "ideal") {
                    std::size_t used = 0;
                    controls.power = std::stoi(value, &used);
                    if (used != value.size() || controls.power < 1 || controls.power > 101)
                        throw std::runtime_error("--power requires ideal|batteries|adaptor|ac|1..101");
                }
            }
            else if (arg == "--chip-rate") {
                if (value == "legacy" || value == "0") controls.chipRate = 0;
                else if (value == "ym3420" || value == "1") controls.chipRate = 1;
                else throw std::runtime_error("--chip-rate requires legacy|ym3420|0|1");
            }
            else if (arg == "--bend") controls.pitchBendSemitones = std::stod(value);
            else if (arg == "--midi-bend") controls.midiPitchBend = std::stoi(value);
            else if (arg == "--bend-range") controls.midiBendRange = std::stoi(value);
            else if (arg == "--fine-cents") controls.masterTuneCents = std::stod(value);
            else if (arg == "--host-tune-cents") controls.hostTuneCents = std::stod(value);
            else if (arg == "--clock-ppm") controls.clockOffsetPpm = std::stod(value);
            else if (arg == "--drift-ppm") controls.clockDriftPpm = std::stod(value);
            else if (arg == "--chorus") controls.chorusMix = std::stod(value);
            else if (arg == "--chorus-mode") controls.chorusMode = std::stoi(value);
            else if (arg == "--chorus-rate") controls.chorusRateHz = std::stod(value);
            else if (arg == "--chorus-depth") controls.chorusDepthMs = std::stod(value);
            else if (arg == "--drive") controls.drive = std::stod(value);
            else if (arg == "--envelope-reverb") {
                if (value != "0" && value != "1") throw std::runtime_error("--envelope-reverb requires 0|1");
                controls.envelopeReverb = value == "1";
            }
            else throw std::runtime_error("Unknown option " + arg);
        }
        if (output.empty() || rate < 8000 || rate > 192000 || !std::isfinite(duration) || duration <= 0 || duration > 120
            || !std::isfinite(gate) || gate < 0 || note < 0 || note > 127 || velocity < 0 || velocity > 127)
            throw std::runtime_error("Usage: press78_render --output file.wav [--raw 66hex] [--real] [--transparent] [--rate 48000] [--note 60] [--velocity 100] [--seconds 3] [--gate 1.5] [--pitch-model equal|original] [--sustain-mode legacy|original] [--key-level-model legacy|original] [--allocation-model legacy|original] [--chorus-circuit legacy|pss270] [--output-jack preamp|aux|phones] [--power ideal|batteries|adaptor|1..101] [--bend semitones] [--midi-bend -1..16383] [--bend-range 0..24] [--fine-cents cents] [--host-tune-cents cents] [--envelope-reverb 0|1]");
        const auto frames = static_cast<std::size_t>(std::llround(duration * rate));
        if (!frames) throw std::runtime_error("Duration rounds to zero samples");
        const auto gateFrame = gate >= duration ? frames : static_cast<std::size_t>(std::llround(gate * rate));
        std::vector<float> left(frames), right(frames);
        auto engine = std::make_unique<press78::Press78OutputBus>();
        engine->prepare(rate); engine->setPatch(patch); engine->setControls(controls);
        if (gateFrame > 0) engine->noteOn(note, velocity);
        std::size_t cursor = 0;
        while (cursor < frames) {
            if (cursor == gateFrame) engine->noteOff(note);
            const auto boundary = cursor < gateFrame ? std::min(frames, gateFrame) : frames;
            const auto count = std::min<std::size_t>(128, boundary - cursor);
            engine->process(left.data() + cursor, right.data() + cursor, count);
            cursor += count;
        }
        writeWav(output, left, right, rate);
        double peak = 0.0, energy = 0.0;
        for (std::size_t i = 0; i < frames; ++i) {
            peak = std::max(peak, std::max(std::abs(static_cast<double>(left[i])), std::abs(static_cast<double>(right[i]))));
            energy += (static_cast<double>(left[i]) * left[i] + static_cast<double>(right[i]) * right[i]) * 0.5;
        }
        std::cout << "{\"frames\":" << frames << ",\"rate\":" << rate << ",\"latency_samples\":" << engine->latencySamples()
                  << ",\"nominal_latency_seconds\":" << engine->nominalLatencySeconds()
                  << ",\"clipped_channel_samples\":" << engine->clippedChannels()
                  << ",\"maximum_clip_delta\":" << engine->maximumClipDelta()
                  << ",\"pitch_model\":" << engine->effectivePitchModel()
                  << ",\"sustain_mode\":" << engine->effectiveSustainMode()
                  << ",\"key_level_model\":" << engine->effectiveKeyLevelModel()
                  << ",\"allocation_model\":" << engine->effectiveAllocationModel()
                  << ",\"peak\":" << peak << ",\"rms\":" << std::sqrt(energy / frames) << "}\n";
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
