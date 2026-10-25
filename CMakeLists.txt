cmake_minimum_required(VERSION 3.22)

if(POLICY CMP0135)
    cmake_policy(SET CMP0135 NEW)
endif()

option(PRESS78_BUILD_UNIVERSAL "Build arm64 and x86_64 slices on macOS" ON)

# These must be established before project() so CMake's compiler checks use the
# same deployment target and architectures as the final plug-in.
if(CMAKE_HOST_SYSTEM_NAME STREQUAL "Darwin")
    if(NOT DEFINED CMAKE_OSX_DEPLOYMENT_TARGET)
        set(CMAKE_OSX_DEPLOYMENT_TARGET "11.0" CACHE STRING
            "Minimum supported macOS version")
    endif()

    if(PRESS78_BUILD_UNIVERSAL AND NOT DEFINED CMAKE_OSX_ARCHITECTURES)
        set(CMAKE_OSX_ARCHITECTURES "arm64;x86_64" CACHE STRING
            "macOS architectures")
    endif()
endif()

# C is required in addition to C++: JUCE's macOS plug-in wrappers (AU and
# Standalone) compile C/Objective-C sources with non-Xcode generators too.
project(Press78 VERSION 0.1.13 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

option(PRESS78_BUILD_PLUGIN "Build the JUCE plug-in and standalone app" ON)
option(PRESS78_BUILD_CLAP "Build the CLAP format through clap-juce-extensions" ON)
option(PRESS78_BUILD_TOOLS "Build native audio tools" ON)
set(PRESS78_JUCE_PATH "" CACHE PATH
    "Optional path to a local JUCE 8.0.14 checkout (avoids downloading JUCE)")
set(PRESS78_CLAP_JUCE_EXTENSIONS_PATH "" CACHE PATH
    "Optional path to a local clap-juce-extensions checkout with submodules")

include(CTest)

option(PRESS78_ENABLE_SANITIZERS "Instrument development builds with ASan and UBSan" OFF)
option(PRESS78_BUILD_LIBFUZZER "Build Press78DspFuzz as a Clang libFuzzer target" OFF)
if(PRESS78_ENABLE_SANITIZERS)
    if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
        message(FATAL_ERROR "PRESS78_ENABLE_SANITIZERS requires Clang or GCC")
    endif()
    add_compile_options(-fsanitize=address,undefined,float-cast-overflow
                        -fno-sanitize-recover=all -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address,undefined,float-cast-overflow)
endif()

set(PRESS78_DSP_SOURCES Source/DSP/Press78Engine.cpp)

add_library(Press78DSP STATIC ${PRESS78_DSP_SOURCES})
target_include_directories(Press78DSP PUBLIC Source Source/DSP)
set_target_properties(Press78DSP PROPERTIES POSITION_INDEPENDENT_CODE ON)
if(MSVC)
    target_compile_options(Press78DSP PRIVATE /W4 /permissive-)
else()
    target_compile_options(Press78DSP PRIVATE -Wall -Wextra -Wpedantic)
endif()

# The Rack Extension toolchain is C++17. Compiling the engine at that standard
# here keeps Source/DSP portable for the Rack adapter.
if(NOT MSVC)
    add_library(Press78DSPCxx17 OBJECT ${PRESS78_DSP_SOURCES})
    target_include_directories(Press78DSPCxx17 PRIVATE Source Source/DSP)
    set_target_properties(Press78DSPCxx17 PROPERTIES
        CXX_STANDARD 17
        CXX_STANDARD_REQUIRED ON
        CXX_EXTENSIONS OFF)
    target_compile_options(Press78DSPCxx17 PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(PRESS78_BUILD_PLUGIN)
    if(PRESS78_JUCE_PATH)
        if(NOT EXISTS "${PRESS78_JUCE_PATH}/CMakeLists.txt")
            message(FATAL_ERROR
                "PRESS78_JUCE_PATH does not contain a JUCE CMakeLists.txt: ${PRESS78_JUCE_PATH}")
        endif()
        add_subdirectory("${PRESS78_JUCE_PATH}"
                         "${CMAKE_CURRENT_BINARY_DIR}/JUCE" EXCLUDE_FROM_ALL)
    else()
        include(FetchContent)
        FetchContent_Declare(
            JUCE
            # JUCE 8.0.14, pinned to its immutable release commit and archive
            # checksum so automated release builds cannot follow a moved tag.
            URL https://github.com/juce-framework/JUCE/archive/2cdfca8feb300fb424002ba2c2751569e5bacb64.tar.gz
            URL_HASH SHA256=814019716960a16f8f850a1593eeb56e2f21910aff2d673f7d3513b4ebaf251d)
        FetchContent_MakeAvailable(JUCE)
    endif()

    if(PRESS78_BUILD_CLAP)
        if(PRESS78_CLAP_JUCE_EXTENSIONS_PATH)
            foreach(required_file IN ITEMS CMakeLists.txt
                    clap-libs/clap/CMakeLists.txt
                    clap-libs/clap-helpers/CMakeLists.txt)
                if(NOT EXISTS "${PRESS78_CLAP_JUCE_EXTENSIONS_PATH}/${required_file}")
                    message(FATAL_ERROR
                        "PRESS78_CLAP_JUCE_EXTENSIONS_PATH is missing ${required_file}; "
                        "use a checkout with git submodule update --init --recursive")
                endif()
            endforeach()
            add_subdirectory("${PRESS78_CLAP_JUCE_EXTENSIONS_PATH}"
                             "${CMAKE_CURRENT_BINARY_DIR}/clap-juce-extensions"
                             EXCLUDE_FROM_ALL)
        else()
            include(FetchContent)
            FetchContent_Declare(
                clap_juce_extensions
                GIT_REPOSITORY https://github.com/free-audio/clap-juce-extensions.git
                GIT_TAG c1a5ad025f95d01e03267857fa8276ebeed16500
                # Archive downloads omit these gitlinks. Fetch both dependencies
                # at the immutable revisions recorded by the wrapper commit.
                GIT_SUBMODULES clap-libs/clap clap-libs/clap-helpers
                GIT_SUBMODULES_RECURSE TRUE)
            FetchContent_MakeAvailable(clap_juce_extensions)
        endif()
    endif()

    if(APPLE)
        set(PRESS78_PLUGIN_FORMATS VST3 AU Standalone)
    else()
        set(PRESS78_PLUGIN_FORMATS VST3 Standalone)
    endif()

    juce_add_plugin(Press78
        VERSION ${PROJECT_VERSION}
        COMPANY_NAME "Protocodus"
        COMPANY_WEBSITE "https://protocodus.cz"
        COMPANY_EMAIL "protocodus@proton.me"
        COMPANY_COPYRIGHT "Copyright (c) 2026 Protocodus"
        BUNDLE_ID "cz.protocodus.press78"
        PLUGIN_MANUFACTURER_CODE Pr78
        PLUGIN_CODE P781
        PRODUCT_NAME "Press78"
        DESCRIPTION "Press78 two-operator FM synthesizer"
        FORMATS ${PRESS78_PLUGIN_FORMATS}
        VST3_CATEGORIES Instrument Synth
        AU_MAIN_TYPE kAudioUnitType_MusicDevice
        IS_SYNTH TRUE
        NEEDS_MIDI_INPUT TRUE
        NEEDS_MIDI_OUTPUT FALSE
        IS_MIDI_EFFECT FALSE
        EDITOR_WANTS_KEYBOARD_FOCUS FALSE
        AU_SANDBOX_SAFE TRUE
        COPY_PLUGIN_AFTER_BUILD FALSE)

    if(PRESS78_BUILD_CLAP)
        # CLAP is supplied by the JUCE extension, outside JUCE's FORMATS list.
        clap_juce_extensions_plugin(TARGET Press78
            CLAP_ID "cz.protocodus.press78"
            CLAP_FEATURES instrument synthesizer stereo)
    endif()

    juce_generate_juce_header(Press78)

    target_sources(Press78 PRIVATE
        Source/PluginControls.h
        Source/PluginProcessor.cpp
        Source/PluginProcessor.h
        Source/PluginEditor.cpp
        Source/PluginEditor.h)

    target_link_libraries(Press78
        PRIVATE
            Press78DSP
            juce::juce_audio_utils
        PUBLIC
            juce::juce_recommended_config_flags
            juce::juce_recommended_lto_flags
            juce::juce_recommended_warning_flags)

    # The About box names the package this binary ships in, with the build
    # number read the way scripts/release_metadata.py reads it.
    if(NOT "$ENV{BUILD_NUMBER}" STREQUAL "")
        set(PRESS78_BUILD_NUMBER "$ENV{BUILD_NUMBER}")
    elseif(NOT "$ENV{GITHUB_RUN_NUMBER}" STREQUAL "")
        set(PRESS78_BUILD_NUMBER "$ENV{GITHUB_RUN_NUMBER}")
    else()
        set(PRESS78_BUILD_NUMBER "local")
    endif()

    target_compile_definitions(Press78
        PUBLIC
            JUCE_WEB_BROWSER=0
            JUCE_USE_CURL=0
            JUCE_VST3_CAN_REPLACE_VST2=0
        PRIVATE
            PRESS78_BUILD_IDENTITY="${PROJECT_VERSION}-build.${PRESS78_BUILD_NUMBER}")
endif()

if(PRESS78_BUILD_TOOLS)
    add_executable(press78_render Tools/NativeRender.cpp)
    target_link_libraries(press78_render PRIVATE Press78DSP)
    add_executable(press78_analog_probe Tools/AnalogProbe.cpp)
    target_link_libraries(press78_analog_probe PRIVATE Press78DSP)
    add_executable(press78_analog_oversampled_probe Tools/OversampledAnalogProbe.cpp)
    target_include_directories(press78_analog_oversampled_probe PRIVATE Source/DSP)
    add_executable(press78_chorus_probe Tools/ChorusProbe.cpp)
    target_link_libraries(press78_chorus_probe PRIVATE Press78DSP)
    add_executable(press78_circuit_noise_probe Tools/CircuitNoiseProbe.cpp)
    target_link_libraries(press78_circuit_noise_probe PRIVATE Press78DSP)
    add_executable(press78_performance_probe Tools/PerformanceProbe.cpp)
    target_link_libraries(press78_performance_probe PRIVATE Press78DSP)
    # Instruction-count and output-parity workload; protocol at its head.
    add_executable(press78_cpu_bench Tools/CpuParityBench.cpp)
    target_link_libraries(press78_cpu_bench PRIVATE Press78DSP)

    # One README demo per factory voice from Docs/audio/midi (Tools/
    # PresetDemoRenderer.h is the shared portfolio copy; do not edit it here).
    add_executable(RenderPress78PresetDemos Tools/RenderPresetDemos.cpp)
    find_package(Threads REQUIRED)
    target_link_libraries(RenderPress78PresetDemos PRIVATE Press78DSP Threads::Threads)
    if(MSVC)
        target_compile_options(RenderPress78PresetDemos PRIVATE /W4 /permissive-)
    else()
        target_compile_options(RenderPress78PresetDemos PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endif()

if(BUILD_TESTING)
    add_executable(Press78DSPTests Tests/test_dsp.cpp)
    target_link_libraries(Press78DSPTests PRIVATE Press78DSP)
    add_test(NAME Press78.DSP COMMAND Press78DSPTests)
    add_executable(Press78ModulationTests Tests/test_modulation.cpp)
    target_link_libraries(Press78ModulationTests PRIVATE Press78DSP)
    add_test(NAME Press78.Modulation COMMAND Press78ModulationTests)
    add_executable(Press78SustainTests Tests/test_sustain.cpp)
    target_link_libraries(Press78SustainTests PRIVATE Press78DSP)
    add_test(NAME Press78.Sustain COMMAND Press78SustainTests)
    add_executable(Press78OutputBusTests Tests/test_output_bus.cpp)
    target_link_libraries(Press78OutputBusTests PRIVATE Press78DSP)
    add_test(NAME Press78.OutputBus COMMAND Press78OutputBusTests)
    add_executable(Press78PitchTests Tests/test_pitch.cpp)
    target_link_libraries(Press78PitchTests PRIVATE Press78DSP)
    add_test(NAME Press78.Pitch COMMAND Press78PitchTests)
    add_executable(Press78PortamentoTests Tests/test_portamento.cpp)
    target_link_libraries(Press78PortamentoTests PRIVATE Press78DSP)
    add_test(NAME Press78.Portamento COMMAND Press78PortamentoTests)
    add_executable(Press78KeyLevelTests Tests/test_key_level.cpp)
    target_link_libraries(Press78KeyLevelTests PRIVATE Press78DSP)
    add_test(NAME Press78.KeyLevel COMMAND Press78KeyLevelTests)
    add_executable(Press78AllocationTests Tests/test_allocation.cpp)
    target_link_libraries(Press78AllocationTests PRIVATE Press78DSP)
    add_test(NAME Press78.Allocation COMMAND Press78AllocationTests)
    add_executable(Press78ChorusCircuitTests Tests/test_chorus_circuit.cpp)
    target_link_libraries(Press78ChorusCircuitTests PRIVATE Press78DSP)
    add_test(NAME Press78.ChorusCircuit COMMAND Press78ChorusCircuitTests)
    add_executable(Press78AmplifierCircuitTests Tests/test_amplifier_circuit.cpp)
    target_link_libraries(Press78AmplifierCircuitTests PRIVATE Press78DSP)
    add_test(NAME Press78.AmplifierCircuit COMMAND Press78AmplifierCircuitTests)
    add_executable(Press78ChipRateTests Tests/test_chip_rate.cpp)
    target_link_libraries(Press78ChipRateTests PRIVATE Press78DSP)
    add_test(NAME Press78.ChipRate COMMAND Press78ChipRateTests)
    add_executable(Press78HardwareCharacterTests Tests/test_hardware_character.cpp)
    target_link_libraries(Press78HardwareCharacterTests PRIVATE Press78DSP)
    add_test(NAME Press78.HardwareCharacter COMMAND Press78HardwareCharacterTests)

    # U4 input fuzzing. With PRESS78_BUILD_LIBFUZZER (Clang) it is a libFuzzer
    # target over coverage-instrumented DSP; otherwise FuzzHarness.h supplies
    # a main that replays Tests/fuzz-regressions/ and then seeded inputs.
    add_executable(Press78DspFuzz Tests/DspFuzz.cpp)
    target_include_directories(Press78DspFuzz PRIVATE Source Source/DSP)
    if(PRESS78_BUILD_LIBFUZZER)
        if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang")
            message(FATAL_ERROR "PRESS78_BUILD_LIBFUZZER requires Clang")
        endif()
        target_sources(Press78DspFuzz PRIVATE ${PRESS78_DSP_SOURCES})
        target_compile_options(Press78DspFuzz PRIVATE
            -fsanitize=fuzzer,address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer)
        target_link_options(Press78DspFuzz PRIVATE -fsanitize=fuzzer,address,undefined)
    else()
        target_link_libraries(Press78DspFuzz PRIVATE Press78DSP)
        target_compile_definitions(Press78DspFuzz PRIVATE PROTOCODUS_FUZZ_MAIN)
    endif()
    file(GLOB PRESS78_FUZZ_REGRESSIONS CONFIGURE_DEPENDS
         "${CMAKE_CURRENT_SOURCE_DIR}/Tests/fuzz-regressions/*")
    add_test(NAME Press78.DspFuzz
             COMMAND Press78DspFuzz -seed=1 -runs=300 ${PRESS78_FUZZ_REGRESSIONS})
    set_tests_properties(Press78.DspFuzz PROPERTIES TIMEOUT 600 LABELS fuzz)

    if(PRESS78_BUILD_TOOLS)
        # Every preset demo renders finite, audible, under the ceiling, 10-20 s
        # long and bit-identical on a second render.
        add_test(NAME Press78.AudioDemos
                 COMMAND RenderPress78PresetDemos --jobs 4 --check
                         "${CMAKE_CURRENT_SOURCE_DIR}/Docs/audio/midi")
        set_tests_properties(Press78.AudioDemos PROPERTIES TIMEOUT 900 LABELS audio)
    endif()

    find_package(Python3 COMPONENTS Interpreter)
    if(Python3_Interpreter_FOUND)
        add_test(NAME Press78.ModernFactoryBank COMMAND ${Python3_EXECUTABLE}
            ${CMAKE_CURRENT_SOURCE_DIR}/Tools/modern_bank.py)
        add_test(NAME Press78.OutputKernel COMMAND ${Python3_EXECUTABLE}
            ${CMAKE_CURRENT_SOURCE_DIR}/Tools/generate_output_kernel.py --check)
        add_test(NAME Press78.FactoryBank COMMAND ${Python3_EXECUTABLE}
            ${CMAKE_CURRENT_SOURCE_DIR}/Tools/generate_factory.py --check)
        add_test(NAME Press78.ChorusProfile COMMAND ${Python3_EXECUTABLE}
            ${CMAKE_CURRENT_SOURCE_DIR}/Tools/generate_chorus_profile.py --check)
        add_test(NAME Press78.FirmwareLevel COMMAND ${Python3_EXECUTABLE}
            ${CMAKE_CURRENT_SOURCE_DIR}/Tools/generate_firmware_level.py --check)
        add_test(NAME Press78.FirmwarePitch COMMAND ${Python3_EXECUTABLE}
            ${CMAKE_CURRENT_SOURCE_DIR}/Tools/generate_firmware_pitch.py --check)
        add_test(NAME Press78.LocalSupply COMMAND ${Python3_EXECUTABLE}
            ${CMAKE_CURRENT_SOURCE_DIR}/Tools/check_supply.py)
        add_test(NAME Press78.PluginControls COMMAND ${Python3_EXECUTABLE}
            ${CMAKE_CURRENT_SOURCE_DIR}/Tools/generate_plugin_controls.py --check)
        add_test(NAME Press78.DemoMidiSources COMMAND ${Python3_EXECUTABLE}
            ${CMAKE_CURRENT_SOURCE_DIR}/Tools/write_preset_midi.py --check)
    endif()

    if(PRESS78_BUILD_PLUGIN)
        foreach(suite IN ITEMS PluginProcessor ParameterMatrix)
            add_executable(Press78${suite}Tests Tests/${suite}Tests.cpp)
            target_link_libraries(Press78${suite}Tests PRIVATE Press78)
            target_include_directories(Press78${suite}Tests PRIVATE
                "${CMAKE_CURRENT_SOURCE_DIR}/Source"
                "$<TARGET_PROPERTY:Press78,JUCE_GENERATED_SOURCES_DIRECTORY>"
                "$<TARGET_PROPERTY:Press78,INCLUDE_DIRECTORIES>")
        endforeach()

        add_test(NAME Press78.PluginProcessor COMMAND Press78PluginProcessorTests)
        set_tests_properties(Press78.PluginProcessor PROPERTIES TIMEOUT 300)

        # A fixed sample of the U4 matrix at one rate and block size per case;
        # the main build's nightly shards cover every case at all nine.
        add_test(NAME Press78.ParameterMatrix
                 COMMAND Press78ParameterMatrixTests --rotation --shard 1/50 --jobs 4)
        set_tests_properties(Press78.ParameterMatrix PROPERTIES TIMEOUT 1800 LABELS fuzz)

        if(Python3_Interpreter_FOUND)
            add_test(NAME Press78.EditorRender
                     COMMAND "${Python3_EXECUTABLE}" -B
                             "${CMAKE_CURRENT_SOURCE_DIR}/Tests/EditorRenderTests.py"
                             --processor-tests "$<TARGET_FILE:Press78PluginProcessorTests>")
            set_tests_properties(Press78.EditorRender PROPERTIES TIMEOUT 600 LABELS render)
        endif()
    endif()

    # Every test carries exactly one tier label so CI selects tiers with
    # `ctest -L`; tests not labelled above are unit contracts.
    get_property(PRESS78_TESTS DIRECTORY PROPERTY TESTS)
    foreach(test IN LISTS PRESS78_TESTS)
        get_test_property(${test} LABELS test_labels)
        if(NOT test_labels)
            set_tests_properties(${test} PROPERTIES LABELS unit)
        endif()
    endforeach()
endif()
