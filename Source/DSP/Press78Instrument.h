#pragma once

#include "Press78OutputBus.h"

#include <cstddef>

// The playing layer every front end shares: the fixed 48 kHz output bus,
// the mod wheel's vibrato law, Double (a second, detuned unit) and Stage
// drive. Front ends map their own controls and note sources onto it; this
// file knows nothing about Reason or JUCE.
namespace press78 {

// Performance settings that are not engine Controls, in physical units.
struct Performance {
    double modWheel = 0.0;          // 0..1, the wheel's position.
    double modWheelDepth = 1.0;     // 0..4, vibrato depth at full wheel.
    bool doubleMode = false;        // A second unit, detuned and spread.
    double doubleSpread = 1.0;      // 0..1: mono to the units hard left/right.
    double doubleDetuneCents = 0.0; // 0..30 between the units, half each way.
    // 0..12 dB more level into the AUX/Phones amplifier, taken off again after
    // it, so the stage colours harder at the same output level. Preamp has no
    // amplifier and ignores it.
    double stageDriveDb = 0.0;
};

// The wheel adds vibrato: a patch without vibrato gets the patch's own depth
// scaled by the wheel, one with vibrato gets the wheel on top. Either way the
// patch's PMS is at least 3 (12.5 cents per unit depth) while the wheel is up.
void applyModWheel(double wheel, Patch& patch, Controls& controls) noexcept;

class Press78Instrument {
public:
    static constexpr std::size_t kMaxVoices = Press78Engine::kMaxVoices;

    void prepare(double sampleRate) noexcept;
    // Silences both units and forgets Double; call apply() again before the
    // next process().
    void reset() noexcept;
    // patchChanged retimbres held notes with the patch (and the wheel's
    // effect on it); otherwise only the controls change.
    void apply(Patch patch, Controls controls, const Performance& performance, bool patchChanged) noexcept;
    void noteOn(int note, int velocity, int source = 0) noexcept;
    void noteOff(int note, int source = 0) noexcept;
    void sustainPedal(bool down) noexcept;
    void sustainController(int rawValue) noexcept;
    void allNotesOff() noexcept;
    void allSoundOff() noexcept;
    void process(float* left, float* right, std::size_t frames) noexcept;

    std::size_t activeVoices() const noexcept;
    int latencySamples() const noexcept { return primary_.latencySamples(); }
    int effectiveSustainMode() const noexcept { return primary_.effectiveSustainMode(); }
    const Press78OutputBus& primary() const noexcept { return primary_; }
    // The Double unit; it plays only while secondActive().
    const Press78OutputBus& second() const noexcept { return second_; }
    bool secondActive() const noexcept { return secondReady_; }

private:
    static constexpr std::size_t kBlock = 64;
    void render(float* left, float* right, std::size_t frames) noexcept;
    Press78OutputBus primary_{}, second_{};
    double smoothing_ = 0.0;
    double doubleMix_ = 0.0, spread_ = 1.0, spreadTarget_ = 1.0;
    double compensation_ = 1.0, compensationTarget_ = 1.0;
    bool doubleTarget_ = false, secondReady_ = false, soundStarted_ = false;
};

} // namespace press78
