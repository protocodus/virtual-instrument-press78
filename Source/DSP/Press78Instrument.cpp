#include "Press78Instrument.h"

#include <algorithm>
#include <cmath>

namespace press78 {

void applyModWheel(double wheel, Patch& patch, Controls& controls) noexcept {
    if (!(wheel > 0.0)) return;
    if (!patch.vibrato) controls.vibratoDepth *= wheel;
    else controls.vibratoDepth += wheel;
    patch.vibrato = true;
    patch.pms = std::max(patch.pms, 3);
}

void Press78Instrument::prepare(double sampleRate) noexcept {
    primary_.prepare(sampleRate);
    second_.prepare(sampleRate);
    // 5 ms smoothing for the Double blend, its spread and the drive's
    // compensation, so switching any of them never clicks.
    smoothing_ = 1.0 - std::exp(-1.0 / (0.005 * primary_.sampleRate()));
    reset();
}

void Press78Instrument::reset() noexcept {
    primary_.reset();
    second_.reset();
    secondReady_ = false;
    doubleMix_ = 0.0;
    soundStarted_ = false;
}

void Press78Instrument::apply(Patch patch, Controls controls, const Performance& performance,
                              bool patchChanged) noexcept {
    applyModWheel(performance.modWheel * performance.modWheelDepth, patch, controls);
    spreadTarget_ = performance.doubleSpread;
    const double detune = performance.doubleMode ? performance.doubleDetuneCents * 0.5 : 0.0;
    const double gain = controls.masterGain;
    const double factor = controls.outputJack == 0 ? 1.0 :
        std::min(std::pow(10.0, performance.stageDriveDb / 20.0), 2.0 / std::max(gain, 1.0e-12));
    controls.masterGain = gain * factor;
    compensationTarget_ = 1.0 / factor;
    if (!soundStarted_) {
        compensation_ = compensationTarget_;
        spread_ = spreadTarget_;
        doubleMix_ = performance.doubleMode ? 1.0 : 0.0;
    }
    auto secondControls = controls;
    controls.hostTuneCents -= detune;
    secondControls.hostTuneCents += detune;
    primary_.setControls(controls);
    if (performance.doubleMode && !secondReady_) {
        // A copy of the first unit's fixed-size state (held and pedal-held
        // voices, allocator, chorus and resampler history), so the second unit
        // joins mid-phrase without allocating or replaying an attack.
        second_ = primary_;
        second_.setControls(secondControls);
        secondReady_ = true;
    } else if (secondReady_) {
        second_.setControls(secondControls);
    }
    doubleTarget_ = performance.doubleMode;
    if (secondReady_ && patchChanged) second_.setPatch(patch, true);
    if (patchChanged) primary_.setPatch(patch, true);
}

void Press78Instrument::noteOn(int note, int velocity, int source) noexcept {
    primary_.noteOn(note, velocity, source);
    if (secondReady_) second_.noteOn(note, velocity, source);
}

void Press78Instrument::noteOff(int note, int source) noexcept {
    primary_.noteOff(note, source);
    if (secondReady_) second_.noteOff(note, source);
}

void Press78Instrument::sustainPedal(bool down) noexcept {
    primary_.sustainPedal(down);
    if (secondReady_) second_.sustainPedal(down);
}

void Press78Instrument::sustainController(int rawValue) noexcept {
    primary_.sustainController(rawValue);
    if (secondReady_) second_.sustainController(rawValue);
}

void Press78Instrument::allNotesOff() noexcept {
    primary_.allNotesOff();
    if (secondReady_) second_.allNotesOff();
}

void Press78Instrument::allSoundOff() noexcept {
    primary_.allSoundOff();
    if (secondReady_) second_.allSoundOff();
}

std::size_t Press78Instrument::activeVoices() const noexcept {
    return primary_.activeVoices() + (secondReady_ ? second_.activeVoices() : 0);
}

void Press78Instrument::process(float* left, float* right, std::size_t frames) noexcept {
    float scratchLeft[kBlock], scratchRight[kBlock];
    for (std::size_t done = 0; done < frames;) {
        const auto count = std::min(kBlock, frames - done);
        // The mix below needs both channels even when a caller passes null.
        float* l = left ? left + done : scratchLeft;
        float* r = right ? right + done : scratchRight;
        render(l, r, count);
        done += count;
    }
}

void Press78Instrument::render(float* left, float* right, std::size_t count) noexcept {
    primary_.process(left, right, count);
    float secondLeft[kBlock]{}, secondRight[kBlock]{};
    if (secondReady_) second_.process(secondLeft, secondRight, count);
    for (std::size_t i = 0; i < count; ++i) {
        compensation_ += (compensationTarget_ - compensation_) * smoothing_;
        spread_ += (spreadTarget_ - spread_) * smoothing_;
        doubleMix_ += ((doubleTarget_ ? 1.0 : 0.0) - doubleMix_) * smoothing_;
        if (secondReady_) {
            // Each unit folds to mono; the pair is spread as mid and side.
            const double a = 0.5 * (left[i] + right[i]), b = 0.5 * (secondLeft[i] + secondRight[i]);
            const double mid = 0.5 * (a + b), side = 0.5 * (a - b) * spread_;
            left[i] = static_cast<float>(left[i] + doubleMix_ * (mid + side - left[i]));
            right[i] = static_cast<float>(right[i] + doubleMix_ * (mid - side - right[i]));
        }
        if (compensation_ != 1.0) {
            left[i] = static_cast<float>(left[i] * compensation_);
            right[i] = static_cast<float>(right[i] * compensation_);
        }
    }
    // Once Double has faded out, the second unit stops costing anything.
    if (!doubleTarget_ && secondReady_ && doubleMix_ < 1.0e-6) {
        second_.reset();
        secondReady_ = false;
        doubleMix_ = 0.0;
    }
    soundStarted_ = true;
}

} // namespace press78
