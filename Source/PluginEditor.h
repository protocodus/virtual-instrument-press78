#pragma once

#include <JuceHeader.h>

#include "PluginProcessor.h"

#include <memory>
#include <vector>

// One control per parameter, grouped in rows by section. The Rack panel in
// Assets/Design is the device's designed face; this editor is the plug-in's
// working one until a matching design is ported.
class Press78AudioProcessorEditor final : public juce::AudioProcessorEditor
{
public:
    explicit Press78AudioProcessorEditor (Press78AudioProcessor&);
    ~Press78AudioProcessorEditor() override = default;

    void paint (juce::Graphics&) override;
    void resized() override;

    static juce::String getBuildIdentity() { return PRESS78_BUILD_IDENTITY; }

private:
    struct Control
    {
        std::unique_ptr<juce::Component> widget;
        juce::Label caption;
        std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> slider;
        std::unique_ptr<juce::AudioProcessorValueTreeState::ButtonAttachment> button;
        std::unique_ptr<juce::AudioProcessorValueTreeState::ComboBoxAttachment> choice;
    };
    struct Section
    {
        juce::String title;
        std::vector<std::unique_ptr<Control>> controls;
    };

    Press78AudioProcessor& audioProcessor;
    juce::Label title;
    juce::ComboBox programs;
    std::vector<Section> sections;
};
