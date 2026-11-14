// U4 parameter-extremes matrix over the plug-in processor, through the shared
// portfolio harness (Tests/ParameterMatrix.h is a byte-identical copy of the
// master; change it in reason-rack-extensions).
//
//   Press78ParameterMatrixTests [--jobs N] [--rotation] [--shard K/N]
//                               [--case LABEL] [--count] [--list]
//   Press78ParameterMatrixTests --reach [--jobs N] [--case PARAMETER]
//
// The shared command line (U9): --rotation runs each case at one rate and
// block size instead of all nine, --shard K/N runs the cases whose index
// modulo N is K (numbered from 0), --case runs only the case a FAIL line
// names, and --count and --list print the cases and parameters.

#include "PluginProcessor.h"
#include "ParameterMatrix.h"
#include "DSP/HardwareCharacter.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>
#include <map>
#include <string>
#include <vector>

namespace
{
using protocodus::matrix::Case;
using protocodus::matrix::Limits;

// The envelope law in Source/DSP/Press78Engine.cpp: an operator at rate r
// covers its 96 dB range in 48 * 2^(-r/4) seconds. Key rate scaling only
// speeds it up above middle C, which the matrix chord (60, 64, 67) starts on.
double fullRangeSeconds (double rate) { return 48.0 * std::pow (2.0, -rate / 4.0); }

class Press78Device final : public protocodus::matrix::JuceDevice
{
public:
    Press78Device() : JuceDevice (std::make_unique<Press78AudioProcessor>())
    {
        for (auto* parameter : processor->getParameters())
            if (parameter->isAutomatable())
                if (auto* ranged = dynamic_cast<juce::RangedAudioParameter*> (parameter))
                    columns[ranged->paramID.toStdString()] = { automatable++, ranged };
    }

    Limits LimitsFor (const Case& c) const override
    {
        Limits limits;
        double release = 0.0, gain = 0.0;
        bool limited = true, dcBlocked = true, louderRelease = false;
        // Automation ramps between the case and its base, so each limit takes
        // whichever of the two asks more of it.
        for (const auto* row : { &c.values, &c.base })
        {
            release = std::max (release, releaseSeconds (*row));
            gain = std::max (gain, value (*row, "masterGain"));
            limited = limited && value (*row, "outputLimit") >= 0.5;
            dcBlocked = dcBlocked && value (*row, "dcBlock") >= 0.5;
            louderRelease = louderRelease || tremolo (*row);
        }

        // Output protection bounds every sample to +/-1. Without it, three
        // voices (plus up to three stolen-voice tails) of carrier level 0.8,
        // a stereo width of up to 2 and the output circuit's gain stay below
        // this, scaled by the master gain.
        limits.ceiling = limited ? 1.0001f : static_cast<float> (std::max (1.0, 12.0 * gain));
        // Half-sine and squared waves carry DC that only the DC filter removes.
        if (! dcBlocked)
            limits.dcLimit = limits.ceiling;
        for (const auto* row : { &c.values, &c.base })
            if (silentWhileHeld (*row, limits.silenceFloor))
                limits.soundsWhileHeld = false;
        // An AM LFO can put the held window in a trough and the release on a
        // crest, so such a case waits for silence instead of comparing levels.
        constexpr double longTailSeconds = 6.0;
        limits.releaseSeconds = release <= longTailSeconds || louderRelease ? release : -1.0;
        return limits;
    }

    // U11. Parameters the default patch leaves silent (it plays the carrier
    // alone) are tested on the first factory voice that uses them, or here
    // with what makes them audible.
    protocodus::matrix::ReachRule ReachFor (std::size_t index, float) const override
    {
        using protocodus::matrix::Reach;
        std::vector<protocodus::matrix::Parameter> all = Parameters();
        for (const auto& p : EditorOnlyParameters())
            all.push_back (p);
        const auto at = [&] (const char* name)
        {
            for (std::size_t i = 0; i < all.size(); ++i)
                if (all[i].name == name)
                    return i;
            std::fprintf (stderr, "no parameter %s\n", name);
            std::abort();
        };
        const std::string& name = all[index].name;
        const auto is = [&] (std::initializer_list<const char*> names)
        {
            for (const char* n : names)
                if (name == n)
                    return true;
            return false;
        };
        // Envelope::configure keeps the segment a sounding operator is in, and
        // an operator whose decay 1 level is 0 starts in decay 2: the held
        // chord never goes back to decay 1. One that has a decay 1 level sits
        // in decay 1 while its rate is 0, so it follows a new rate. The
        // modulator is silent until its attenuation comes down.
        if (name == "Carrier Decay 1 level" || name == "Modulator Decay 1 level")
            return { Reach::NewNotes, "a decay 1 the held chord has finished" };
        if (name == "Carrier Decay 1 rate")
            return { Reach::Held, "", { { at ("Carrier Decay 1 level"), 0.5f } } };
        if (name == "Modulator Decay 1 rate")
            return { Reach::Held, "", { { at ("Modulator Attenuation"), 0.25f }, { at ("Modulator Decay 1 level"), 0.5f } } };
        // Key rate scaling speeds every segment, decay 2 included, so the held
        // chord follows it once decay 2 moves (rate 12.6: 96 dB in 5.6 s).
        if (name == "Modulator Key rate scaling")
            return { Reach::Held, "", { { at ("Modulator Attenuation"), 0.25f }, { at ("Modulator Decay 2 rate"), 0.2f } } };
        // Each waits for silence (Press78Engine::pitchIdle, allocationIdle).
        if (is ({ "Pitch model", "Chip sample rate" }))
            return { Reach::NewNotes, "applied once every note has ended" };
        // The default patch has no key level scaling for either law to shape,
        // and its quick release lets every note end before the probe. Most
        // settings give the probe's keys the same levels under both laws
        // (FirmwareLevel.h against level()); the steepest upper scaling and
        // the first lower one are where they part, by 1.5 dB on C5 and 2.3 dB
        // on G3.
        if (name == "Original key scaling")
            return { Reach::NewNotes, "applied once every note has ended",
                     { { at ("Carrier Upper key level"), 1.0f }, { at ("Carrier Lower key level"), 1.0f / 15.0f } } };
        // The voices sound alike, so a policy is heard only in which note it
        // steals, and on two voices both steal the probe's alike.
        if (name == "Original voice allocation")
            return { Reach::Exempt, "which voice each note takes; the voices sound alike (test_allocation checks it)" };
        // At velocities 80, 100 and 127 the original's steps sit within
        // 0.4 dB of the legacy curve.
        if (name == "Original velocity curve")
            return { Reach::Exempt, "within 0.4 dB of the legacy curve at the probes' velocities (test_dsp compares them)" };
        if (name == "Pitch bend range")
            return { Reach::NewNotes, "the range of the next bend; the held chord is not bent" };
        if (name == "Portamento")
            return { Reach::NewNotes, "a glide into each new note" };
        if (name == "Portamento speed")
            return { Reach::NewNotes, "a glide into each new note", { { at ("Portamento"), 1.0f } },
                     "each voice glides from wherever the glides before left it" };
        // The modulator sustains at full level unless it is silenced.
        if (name == "Feedback")
            return { Reach::Held, "", { { at ("Modulator Attenuation"), 0.25f } } };
        if (name == "Drift rate")
            return { Reach::Held, "", { { at ("Clock drift"), 1.0f } },
                     "the clock wanders in the phase its old rate left" };
        if (name == "Double spread")
            return { Reach::Held, "", { { at ("Double"), 1.0f } } };
        if (name == "Double detune")
            return { Reach::Held, "", { { at ("Double"), 1.0f } },
                     "the two units beat in the phase their old detune left" };
        if (name == "DC filter")
            return { Reach::Exempt, "removes only DC and subsonic offset, which are not heard" };
        if (name == "Output protection")
            return { Reach::Exempt, "a limit at full scale the phrase does not reach" };
        // The supply sags under a loud output.
        if (name == "Power circuit")
            return { Reach::Held, "", { { at ("Volume"), 1.0f } } };
        if (name == "Original release policy")
            return { Reach::Exempt, "what the sustain pedal does; the phrase does not press it" };
        if (name == "Wheel to vibrato")
            return { Reach::Exempt, "the mod wheel's vibrato depth; the phrase does not move the wheel" };
        // Press78Engine::sanitizeControls zeroes both: no noise path exists.
        if (name == "Noise level" || name == "Noise model")
            return { Reach::Exempt, "kept for saved sessions; the engine has no noise path" };
        return {};
    }

private:
    struct Column { std::size_t index; juce::RangedAudioParameter* parameter; };

    // A row's value of one parameter in its own units. A parameter the rows
    // leave out (not automatable) keeps the processor's current value.
    double value (const std::vector<float>& row, const std::string& id) const
    {
        const auto found = columns.find (id);
        if (found == columns.end())
            return 0.0;
        const auto& column = found->second;
        const float normalised = column.index < row.size() ? row[column.index] : column.parameter->getValue();
        return column.parameter->convertFrom0to1 (normalised);
    }
    int integer (const std::vector<float>& row, const std::string& id) const
    {
        return static_cast<int> (std::lround (value (row, id)));
    }

    // The harness restores the case row by the first block at/after 0.75 s
    // (at most 512/44100 s later), before note-off at 0.8 s. Thus release
    // uses a restored endpoint, not a mixture of rate/sustain/clock rows.
    // Start at 0 dB attenuation, the longest possible remaining release.
    // The selected model uses the ordinary RR/SRR until the 18 dB knee,
    // then the slower of that rate and native RR4. RKS cannot slow either
    // segment for this harness's chord (60, 64, 67).
    double releaseSeconds (const std::vector<float>& row) const
    {
        const int code = integer (row, "sustain") != 0 ? integer (row, "car_srr") : integer (row, "car_rr");
        const double ordinary = fullRangeSeconds (4 * code + 2);
        const double rr4 = fullRangeSeconds (4 * 4 + 2);
        constexpr double kneeFraction = press78::hardware_character::kReleaseKneeDb / 96.0;
        const double envelope = kneeFraction * ordinary
            + (1.0 - kneeFraction) * std::max (ordinary, rr4);
        // Bound the entire reconstruction support (twice its nominal
        // latency), plus two ticks for envelope/tick endpoint rounding.
        constexpr double reconstruction = (2.0 * press78::Press78Engine::kResamplerDelay + 2.0)
            / press78::Press78Engine::kInternalRate;
        const double slowestClock = 1.0
            + (value (row, "clockOffsetPpm") - value (row, "clockDriftPpm")) * 1.0e-6;
        // Keep the existing chorus, 10 Hz DC filter and output-circuit
        // settling allowance; the absolute silence threshold is unchanged.
        return (envelope + reconstruction) / slowestClock + 0.3;
    }

    bool tremolo (const std::vector<float>& row) const
    {
        return integer (row, "ams") > 0 && value (row, "tremoloDepth") > 0.0
            && (integer (row, "car_amEnable") != 0 || integer (row, "mod_amEnable") != 0);
    }

    // The held chord may be silent before note-off by design: a carrier that
    // never attacks, or one whose level, less what its envelope has decayed
    // by the start of the held window, is within twice the silence floor. The
    // loudest voice is the chord's last note (67 at velocity 127, so a level
    // factor of 1), 0.45 s after its note-on when the window opens. Level is
    // 0.8 at TL 0, 0.75 dB per TL step, times master gain. The envelope
    // follows Envelope::next(): attack from 96 dB, exponential in dB, to
    // 1/1000 in 8 * 2^(-AR/4) s; D1 at d1r down to D1L * 3 dB (D1L 15 is
    // 93 dB); then D2 at d2r. Key scaling, which is small a fifth above
    // middle C, is left out.
    bool silentWhileHeld (const std::vector<float>& row, float silenceFloor) const
    {
        const int tl = integer (row, "car_tl"), ar = integer (row, "car_ar");
        if (tl >= 99 || ar == 0)
            return true;
        constexpr double sinceNoteOn = 0.45;
        const double attackSeconds = ar >= 63 ? 0.0 : 8.0 * std::pow (2.0, -ar / 4.0);
        double attenuation = 0.0;
        if (sinceNoteOn < attackSeconds)
            attenuation = 96.0 * std::pow (1000.0, -sinceNoteOn / attackSeconds);
        else
        {
            const double t = sinceNoteOn - attackSeconds;
            const auto dbPerSecond = [] (int rate) { return rate == 0 ? 0.0 : 96.0 / fullRangeSeconds (rate); };
            const int d1l = integer (row, "car_d1l");
            const double target = d1l == 15 ? 93.0 : 3.0 * d1l;
            const double d1 = dbPerSecond (integer (row, "car_d1r")), d2 = dbPerSecond (integer (row, "car_d2r"));
            if (target == 0.0)
                attenuation = d2 * t;
            else if (d1 > 0.0)
                attenuation = d1 * t <= target ? d1 * t : target + d2 * (t - target / d1);
        }
        const double levelDb = 20.0 * std::log10 (0.8 * std::max (value (row, "masterGain"), 1.0e-9)) - 0.75 * tl;
        return attenuation >= 96.0 || levelDb - attenuation < 20.0 * std::log10 (2.0 * silenceFloor);
    }

    std::size_t automatable = 0;
    std::map<std::string, Column> columns;
};
} // namespace

int main (int argc, char** argv)
{
    juce::ScopedJuceInitialiser_GUI juce;
    return protocodus::matrix::Main (argc, argv, [] { return std::make_unique<Press78Device>(); });
}
