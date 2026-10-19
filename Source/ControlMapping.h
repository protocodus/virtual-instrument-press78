#pragma once

// The plug-in's control values (one per Assets/controls.json entry, in its
// units) to and from the engine's Patch and Controls. JUCE-free, so the demo
// renderer plays the factory voices exactly as the plug-in does.

#include "DSP/Press78Engine.h"
#include "PluginControls.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace press78 {

using ControlValues = std::array<double, kPluginControls.size()>;

// Patch controls come first in controls.json; everything from Volume on is a
// performance or output control a program change leaves alone.
inline constexpr std::size_t kFirstNonPatchControl = controlIndex("masterGain");

namespace detail {
// Each operator's 15 controls, mod_mul..mod_dt2 and car_mul..car_dt2, are
// these integer fields in this order, then amEnable and dt2.
template <typename Op>
auto integerFields(Op& op) noexcept {
    return std::array{&op.mul, &op.dt1, &op.tl, &op.wave, &op.ar, &op.d1r, &op.d1l, &op.d2r,
                      &op.rr, &op.srr, &op.lksHi, &op.lksLo, &op.rks};
}
inline constexpr std::size_t kModulator = controlIndex("mod_mul");
inline constexpr std::size_t kCarrier = controlIndex("car_mul");
static_assert(controlIndex("mod_dt2") == kModulator + 14 && controlIndex("car_dt2") == kCarrier + 14);

inline void readOperator(Operator& op, const double* v) noexcept {
    const auto fields = integerFields(op);
    for (std::size_t i = 0; i < fields.size(); ++i) *fields[i] = static_cast<int>(std::lround(v[i]));
    op.amEnable = v[fields.size()] >= 0.5;
    op.dt2 = v[fields.size() + 1] >= 0.5;
}

inline void writeOperator(const Operator& op, double* v) noexcept {
    const auto fields = integerFields(op);
    for (std::size_t i = 0; i < fields.size(); ++i) v[i] = *fields[i];
    v[fields.size()] = op.amEnable ? 1.0 : 0.0;
    v[fields.size() + 1] = op.dt2 ? 1.0 : 0.0;
}
} // namespace detail

inline ControlValues defaultControlValues() noexcept {
    ControlValues v{};
    for (std::size_t i = 0; i < v.size(); ++i) v[i] = kPluginControls[i].defaultValue;
    return v;
}

inline Patch patchFromValues(const ControlValues& v) noexcept {
    Patch p;
    detail::readOperator(p.modulator, v.data() + detail::kModulator);
    detail::readOperator(p.carrier, v.data() + detail::kCarrier);
    const auto integer = [&v](std::string_view id) { return static_cast<int>(std::lround(v[controlIndex(id)])); };
    p.feedback = integer("feedback");
    p.pms = integer("pms");
    p.ams = integer("ams");
    p.vibratoDelay = integer("vibratoDelay");
    p.vibrato = integer("vibrato") != 0;
    p.sustain = integer("sustain") != 0;
    return sanitizePatch(p);
}

// Writes a patch's fields into the patch controls, leaving the others as they are.
inline void writePatchValues(const Patch& p, ControlValues& v) noexcept {
    detail::writeOperator(p.modulator, v.data() + detail::kModulator);
    detail::writeOperator(p.carrier, v.data() + detail::kCarrier);
    v[controlIndex("feedback")] = p.feedback;
    v[controlIndex("pms")] = p.pms;
    v[controlIndex("ams")] = p.ams;
    v[controlIndex("vibratoDelay")] = p.vibratoDelay;
    v[controlIndex("vibrato")] = p.vibrato ? 1.0 : 0.0;
    v[controlIndex("sustain")] = p.sustain ? 1.0 : 0.0;
}

inline constexpr int kBendCentre = 8192;

// bend is the raw 14-bit pitch wheel (0..16383) and wheel the mod wheel (0..1).
inline Controls controlsFromValues(const ControlValues& v, int bend, double wheel) noexcept {
    const auto value = [&v](std::string_view id) { return v[controlIndex(id)]; };
    const auto integer = [&value](std::string_view id) { return static_cast<int>(std::lround(value(id))); };
    Controls c;
    c.masterGain = value("masterGain");
    c.masterTuneCents = value("masterTuneCents");
    c.velocitySensitivity = value("velocitySensitivity");
    c.velocityToModulation = value("velocityToModulation");
    c.modulationAmount = value("modulationAmount");
    c.polyphony = integer("polyphony");
    c.sustainMode = integer("sustainMode");
    c.lfoRateHz = value("lfoRateHz");
    // The mod wheel adds Wheel to vibrato times its position to Pitch depth.
    c.vibratoDepth = std::min(4.0, value("vibratoDepth") + wheel * value("modWheelDepth"));
    c.tremoloDepth = value("tremoloDepth");
    c.lfoDelayScale = value("lfoDelayScale");
    c.triangleLfo = integer("triangleLfo") != 0;
    c.globalLfo = integer("globalLfo") != 0;
    c.clockOffsetPpm = value("clockOffsetPpm");
    c.clockDriftPpm = value("clockDriftPpm");
    c.clockDriftRateHz = value("clockDriftRateHz");
    c.toneCutoffHz = value("toneCutoffHz");
    c.drive = value("drive");
    c.chorusMix = value("chorusMix");
    c.chorusMode = integer("chorusMode");
    c.chorusRateHz = value("chorusRateHz");
    c.chorusDepthMs = value("chorusDepthMs");
    c.stereoWidth = value("stereoWidth");
    c.outputCircuit = integer("outputCircuit") != 0;
    c.dcBlock = integer("dcBlock") != 0;
    c.outputLimit = integer("outputLimit") != 0;
    c.pitchModel = integer("pitchModel");
    // Equal bends continuously; Original quantises the raw wheel as the
    // firmware does, so it gets the 14-bit value and range too.
    c.pitchBendSemitones = (bend - kBendCentre) / double(kBendCentre) * integer("bendRange");
    c.midiPitchBend = bend;
    c.midiBendRange = integer("bendRange");
    return c;
}

} // namespace press78
