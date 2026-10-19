#pragma once

#include <JuceHeader.h>

#include "DSP/Press78Engine.h"
#include "ControlMapping.h"

#include <array>
#include <atomic>
#include <memory>

// JUCE front end over the canonical engine. It owns parameter mapping, MIDI,
// programs, state and latency; synthesis stays in Source/DSP.
class Press78AudioProcessor final : public juce::AudioProcessor
{
public:
    // Program 0 is the independently defined Init sine; 1..100 are the factory
    // voices in bank order, as the Rack patch list has them.
    static constexpr int kProgramCount = 101;

    Press78AudioProcessor();
    ~Press78AudioProcessor() override = default;

    void prepareToPlay (double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    void reset() override { engine->reset(); }
    bool isBusesLayoutSupported (const BusesLayout& layouts) const override;
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    using AudioProcessor::processBlock;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    const juce::String getName() const override { return JucePlugin_Name; }
    bool acceptsMidi() const override { return true; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    // The longest selectable release: RR or SRR 0 is envelope rate 2, which
    // covers 96 dB in 48 * 2^(-2/4) = 33.9 s (Envelope::configure()).
    double getTailLengthSeconds() const override { return 34.0; }

    int getNumPrograms() override { return kProgramCount; }
    int getCurrentProgram() override { return currentProgram.load(); }
    void setCurrentProgram (int index) override;
    const juce::String getProgramName (int index) override;
    void changeProgramName (int, const juce::String&) override {}

    void getStateInformation (juce::MemoryBlock& destData) override;
    void setStateInformation (const void* data, int sizeInBytes) override;

    juce::AudioProcessorValueTreeState& state() noexcept { return parameters; }

private:
    static juce::AudioProcessorValueTreeState::ParameterLayout createLayout();
    using Values = press78::ControlValues;
    Values readValues() const noexcept;
    // True when the message changed bend or wheel, which feed the engine controls.
    bool handleMidi (const juce::MidiMessage&) noexcept;
    void applyValues (const Values&) noexcept;

    juce::AudioProcessorValueTreeState parameters;
    std::array<std::atomic<float>*, press78::kPluginControls.size()> raw {};
    // About 150 kB of fixed tables and history: kept off the stack.
    std::unique_ptr<press78::Press78Engine> engine;
    Values applied {};
    bool appliedValid = false;
    int bend = press78::kBendCentre; // raw 14-bit wheel, from MIDI
    double wheel = 0.0;              // 0..1, from MIDI
    // Written on the host thread, polled by the editor timer.
    std::atomic<int> currentProgram { 0 };
};
