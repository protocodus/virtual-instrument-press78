#include "PluginEditor.h"

namespace
{
constexpr int kMargin = 12, kHeader = 44, kSectionTitle = 18, kCell = 64, kRow = 96;

// Sections and their parameter ids, in panel order; together they cover every
// control in Assets/controls.json once, except the ones hidden from the Rack
// panel: the inert noise ids and the Original release policy.
const std::vector<std::pair<juce::String, juce::StringArray>>& layout()
{
    static const std::vector<std::pair<juce::String, juce::StringArray>> sections {
        { "Modulator", { "mod_mul", "mod_dt1", "mod_tl", "mod_wave", "mod_ar", "mod_d1r", "mod_d1l", "mod_d2r",
                         "mod_rr", "mod_srr", "mod_lksHi", "mod_lksLo", "mod_rks", "mod_amEnable", "mod_dt2" } },
        { "Carrier", { "car_mul", "car_dt1", "car_tl", "car_wave", "car_ar", "car_d1r", "car_d1l", "car_d2r",
                       "car_rr", "car_srr", "car_lksHi", "car_lksLo", "car_rks", "car_amEnable", "car_dt2" } },
        { "Voice", { "feedback", "pms", "ams", "vibratoDelay", "vibrato", "sustain", "velocitySensitivity",
                     "velocityToModulation", "modulationAmount", "polyphony", "masterTuneCents", "bendRange",
                     "modWheelDepth", "pitchModel", "portamento", "portamentoSpeed" } },
        { "LFO and clock", { "lfoRateHz", "vibratoDepth", "tremoloDepth", "lfoDelayScale", "triangleLfo",
                             "globalLfo", "clockOffsetPpm", "clockDriftPpm", "clockDriftRateHz" } },
        { "Output", { "toneCutoffHz", "drive", "chorusMode", "chorusMix", "chorusRateHz", "chorusDepthMs",
                      "stereoWidth", "outputCircuit", "outputJack", "powerSupply", "dcBlock", "outputLimit",
                      "masterGain" } },
    };
    return sections;
}

const juce::Colour kPanel { 0xff24262b }, kInk { 0xffe9e4d4 }, kAccent { 0xff5fd0d8 };
} // namespace

Press78AudioProcessorEditor::Press78AudioProcessorEditor (Press78AudioProcessor& p)
    : AudioProcessorEditor (p), audioProcessor (p)
{
    auto& state = audioProcessor.state();

    title.setText ("PRESS78", juce::dontSendNotification);
    title.setFont (juce::Font (juce::FontOptions (22.0f, juce::Font::bold)));
    title.setColour (juce::Label::textColourId, kInk);
    title.setTooltip ("About Press78 " + getBuildIdentity());
    addAndMakeVisible (title);

    for (int i = 0; i < audioProcessor.getNumPrograms(); ++i)
        programs.addItem (audioProcessor.getProgramName (i), i + 1);
    programs.setSelectedId (audioProcessor.getCurrentProgram() + 1, juce::dontSendNotification);
    programs.onChange = [this] { audioProcessor.setCurrentProgram (programs.getSelectedId() - 1); };
    addAndMakeVisible (programs);
    startTimerHz (10);

    for (const auto& [name, ids] : layout())
    {
        Section section { name, {} };
        for (const auto& id : ids)
        {
            auto* parameter = state.getParameter (id);
            jassert (parameter != nullptr);
            const auto name = parameter->getName (64);
            auto control = std::make_unique<Control>();
            if (dynamic_cast<juce::AudioParameterBool*> (parameter) != nullptr)
            {
                auto button = std::make_unique<juce::ToggleButton>();
                button->setTooltip (name);
                control->button = std::make_unique<juce::AudioProcessorValueTreeState::ButtonAttachment> (state, id, *button);
                control->widget = std::move (button);
            }
            else if (auto* choice = dynamic_cast<juce::AudioParameterChoice*> (parameter))
            {
                auto box = std::make_unique<juce::ComboBox>();
                box->setTooltip (name);
                box->addItemList (choice->choices, 1);
                control->choice = std::make_unique<juce::AudioProcessorValueTreeState::ComboBoxAttachment> (state, id, *box);
                control->widget = std::move (box);
            }
            else
            {
                auto slider = std::make_unique<juce::Slider> (juce::Slider::RotaryHorizontalVerticalDrag,
                                                              juce::Slider::TextBoxBelow);
                slider->setTooltip (name);
                slider->setTextBoxStyle (juce::Slider::TextBoxBelow, false, kCell - 4, 16);
                slider->setColour (juce::Slider::rotarySliderFillColourId, kAccent);
                slider->setColour (juce::Slider::textBoxOutlineColourId, juce::Colours::transparentBlack);
                control->slider = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (state, id, *slider);
                control->widget = std::move (slider);
            }
            // Captions drop the section name the row title already shows.
            auto caption = name;
            for (const auto* prefix : { "Modulator ", "Carrier " })
                caption = caption.startsWith (prefix) ? caption.fromFirstOccurrenceOf (prefix, false, false) : caption;
            control->caption.setText (caption, juce::dontSendNotification);
            control->caption.setFont (juce::Font (juce::FontOptions (11.0f)));
            control->caption.setJustificationType (juce::Justification::centred);
            control->caption.setColour (juce::Label::textColourId, kInk);
            control->caption.setMinimumHorizontalScale (0.7f);
            addAndMakeVisible (*control->widget);
            addAndMakeVisible (control->caption);
            section.controls.push_back (std::move (control));
        }
        sections.push_back (std::move (section));
    }

    setSize (2 * kMargin + 15 * kCell, kHeader + static_cast<int> (sections.size()) * (kSectionTitle + kRow) + kMargin);
}

void Press78AudioProcessorEditor::paint (juce::Graphics& g)
{
    g.fillAll (kPanel);
    g.setFont (juce::Font (juce::FontOptions (12.0f, juce::Font::bold)));
    int y = kHeader;
    for (const auto& section : sections)
    {
        g.setColour (kAccent);
        g.drawText (section.title.toUpperCase(), kMargin, y, 300, kSectionTitle, juce::Justification::centredLeft);
        g.fillRect (kMargin, y + kSectionTitle - 2, getWidth() - 2 * kMargin, 1);
        y += kSectionTitle + kRow;
    }
}

void Press78AudioProcessorEditor::resized()
{
    title.setBounds (kMargin, 8, 200, 28);
    programs.setBounds (getWidth() - kMargin - 260, 10, 260, 24);
    int y = kHeader + kSectionTitle;
    for (auto& section : sections)
    {
        int x = kMargin;
        for (auto& control : section.controls)
        {
            control->caption.setBounds (x, y + 2, kCell, 14);
            const auto area = juce::Rectangle<int> (x + 2, y + 18, kCell - 4, kRow - 22);
            if (dynamic_cast<juce::Slider*> (control->widget.get()) != nullptr)
                control->widget->setBounds (area);
            else
                control->widget->setBounds (area.withSizeKeepingCentre (kCell - 4, 24));
            x += kCell;
        }
        y += kSectionTitle + kRow;
    }
}

void Press78AudioProcessorEditor::timerCallback()
{
    const int selected = audioProcessor.getCurrentProgram() + 1;
    if (programs.getSelectedId() != selected)
        programs.setSelectedId (selected, juce::dontSendNotification);
}

juce::String Press78AudioProcessorEditor::getBuildIdentity()
{
    return PRESS78_BUILD_IDENTITY;
}
