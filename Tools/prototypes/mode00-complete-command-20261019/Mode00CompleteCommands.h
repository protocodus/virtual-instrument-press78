#pragma once
#include "../mode00-native-command-20261019/Mode00ProgramCommands.h"
#include "../../../Source/DSP/FirmwarePitch.h"
#include "FirmwareLevel.h"
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>

namespace press78::research {

// Command-only research frontend: design-frozen.json binds the original program
// evidence and the precisely limited normal Mode00 domain. No DSP translation,
// firmware, timebase or physical boot is implemented. OPU0200..02ff only; other
// original peripheral/MIDI-output writes (notably0327) are explicitly excluded.
class Mode00CompleteCommands {
public:
    using Front = Mode00ProgramCommands;
    using Target = Front::Target;
    using WorkingPatch = Front::WorkingPatch;
    using RegisterWrite = Front::RegisterWrite;
    enum class Status { Ok, UnsupportedState, UnsupportedNote,
                        UnsupportedVelocity, UnsupportedController, UnsupportedPatch };
    struct Controllers {
        int volumeIndex = 0; // Original table0 exists; physical panel uses1..9.
        int bendHigh = 64, bendSpan = 2, fineSteps = 0;
    };
    struct Snapshot {
        Front::Snapshot front{};
        Controllers controllers{};
        std::array<std::uint8_t, 12> vibratoDelay{};
    };
    struct Plan {
        static constexpr std::size_t kCapacity = Front::ProgramPlan::kCapacity;
        Status status = Status::Ok;
        std::array<RegisterWrite, kCapacity> writes{};
        std::size_t count = 0;
        int slot = -1;
        bool edge = false;
    };

    Status restore(Target target, const Snapshot& state) noexcept {
        // Validate with a local prospective state. No authoritative state is
        // changed on rejection, including metadata, cached controls or delay.
        if (!controllersSupported(state.controllers)) return Status::UnsupportedController;
        if (!patchSupported(state.front.patch)) return Status::UnsupportedPatch;
        if (state.front.effects > 7) return Status::UnsupportedState;
        for (const auto value : state.vibratoDelay)
            if (value > 254) return Status::UnsupportedState;
        Front candidate;
        if (candidate.restore(target, state.front) != Front::Status::Ok)
            return Status::UnsupportedState;
        front_ = candidate;
        controllers_ = state.controllers;
        delay_ = state.vibratoDelay;
        ready_ = true;
        return Status::Ok;
    }
    Snapshot snapshot() const noexcept {
        return {front_.state(), controllers_, delay_};
    }
    const Front::Snapshot& state() const noexcept { return front_.state(); }
    const std::array<std::uint8_t, 12>& vibratoDelay() const noexcept { return delay_; }
    const auto& cachedByte21() const noexcept { return front_.cachedByte21(); }
    const auto& cachedByte15() const noexcept { return front_.cachedByte15(); }
    const auto& cachedByte22() const noexcept { return front_.cachedByte22(); }
    bool ready() const noexcept { return ready_; }

    Plan noteOn(int note, int velocity = 127) noexcept {
        if (!ready_) return rejected(Status::UnsupportedState);
        if (note < 36 || note > 96) return rejected(Status::UnsupportedNote);
        if (velocity < 0 || velocity > 127) return rejected(Status::UnsupportedVelocity);
        if (velocity == 0) return noteOff(note);
        Plan out;
        const auto event = front_.noteOn(note);
        assert(event.status == Front::Status::Ok);
        out.edge = event.allocation.edge;
        out.slot = event.allocation.slot;
        if (out.slot < 0) return out; // Coalesced edge or no eligible rank.
        const int slot = out.slot, delta = slot / 2 + 16 * (slot % 2);
        release(out, slot);
        assert(event.allocation.keyCount == 1);
        append(out, 0x208, event.allocation.keys[0]);
        const auto& p = state().patch.bytes;
        const int reverb = (state().effects & 4) ? 128 : 0;
        const int mod = firmware_level::command(p[2], note, p[4]);
        const int car = firmware_level::command(p[3], note, p[5]);
        constexpr std::array<int, 10> volume{{32,32,28,24,20,16,12,8,4,0}};
        append(out, 0x260 + delta, mod + reverb);
        append(out, 0x268 + delta, std::min(127, car + volume[static_cast<std::size_t>(controllers_.volumeIndex)]) + reverb);
        const int coordinate = note * 32 + pitchSteps(controllers_);
        for (const auto word : firmware_pitch::commands(coordinate / 32, coordinate % 32, slot))
            append(out, word.address, word.value);
        append(out, 0x2e8 + delta, (p[13] & 0xf0) | 15);
        return out;
    }
    Plan noteOff(int note) noexcept {
        if (!ready_) return rejected(Status::UnsupportedState);
        if (note < 36 || note > 96) return rejected(Status::UnsupportedNote);
        Plan out;
        const auto event = front_.noteOff(note);
        assert(event.status == Front::Status::Ok);
        out.edge = event.allocation.edge;
        out.slot = event.allocation.slot;
        if (out.slot < 0) return out;
        release(out, out.slot);
        assert(event.allocation.keyCount == 1);
        append(out, 0x208, event.allocation.keys[0]);
        return out;
    }
    Plan serviceKeyOn() noexcept {
        if (!ready_) return rejected(Status::UnsupportedState);
        Plan out;
        const auto pending = state().allocator.pending;
        const auto event = front_.service(1);
        assert(event.status == Front::Status::Ok);
        int key = 0;
        for (int slot = 0; slot < 12; ++slot) {
            if (!pending[slot]) continue;
            // Original C866 initialises the independent delay even when
            // Vibrato is off. C944 and43b7 are separate service invocations.
            delay_[slot] = static_cast<std::uint8_t>(2 * front_.cachedByte21()[slot]);
            int control = front_.cachedByte15()[slot];
            if (delay_[slot] || !(state().effects & 1)) control &= 15;
            append(out, 0x218 + slot / 2, control | ((slot & 1) ? 128 : 0));
            const int delta = slot / 2 + 16 * (slot % 2);
            append(out, 0x2e8 + delta, state().patch.bytes[13]); // Raw RR, not SRR.
            assert(key < event.allocation.keyCount);
            append(out, 0x208, event.allocation.keys[key++]);
        }
        assert(key == event.allocation.keyCount);
        return out;
    }
    Plan serviceVibrato() noexcept {
        if (!ready_) return rejected(Status::UnsupportedState);
        Plan out;
        for (int slot = 0; slot < 12; ++slot) {
            if (delay_[slot] && --delay_[slot] == 0 && (state().effects & 1))
                append(out, 0x218 + slot / 2, front_.cachedByte15()[slot] | ((slot & 1) ? 128 : 0));
        }
        return out;
    }
    Plan sustainController(int rawValue) noexcept {
        if (!ready_) return rejected(Status::UnsupportedState);
        if (rawValue < 0 || rawValue > 127) return rejected(Status::UnsupportedController);
        auto next = state();
        next.effects = static_cast<std::uint8_t>((next.effects & ~2) | (rawValue ? 2 : 0));
        // Reuse the same authoritative state owner. This is not a second
        // effect snapshot and does not change allocator or independent delay.
        const auto status = front_.restore(front_.target(), next);
        assert(status == Front::Status::Ok);
        (void)status;
        Plan out;
        for (int slot = 0; slot < 12; ++slot) release(out, slot);
        return out;
    }
    Plan selectProgram(const WorkingPatch& patch, std::uint8_t program) noexcept {
        if (!ready_) return rejected(Status::UnsupportedState);
        if (!patchSupported(patch)) return rejected(Status::UnsupportedPatch);
        const auto plan = front_.selectProgram(patch, program);
        assert(plan.status == Front::Status::Ok);
        Plan out;
        out.count = plan.count;
        out.writes = plan.writes;
        // The original reload updates cached controls, not active248e delays.
        return out;
    }
    static bool controllersSupported(const Controllers& c) noexcept {
        return c.volumeIndex >= 0 && c.volumeIndex <= 9 && c.bendHigh >= 0 && c.bendHigh <= 127
            && c.bendSpan >= -12 && c.bendSpan <= 12 && c.bendSpan != 0
            && c.fineSteps >= -16 && c.fineSteps <= 16;
    }
    static int pitchSteps(const Controllers& c) noexcept {
        int high = c.bendHigh, span = c.bendSpan;
        if (span < 0) {
            high = high == 0 ? 127 : high == 127 ? 0 : 128 - high;
            span = -span;
        }
        return firmware_pitch::bendSteps(high, span) + c.fineSteps;
    }
private:
    Front front_{}; // The only allocator/effects/program/cache owner.
    Controllers controllers_{};
    std::array<std::uint8_t, 12> delay_{};
    bool ready_ = false;
    static bool patchSupported(const WorkingPatch& p) noexcept {
        return p.bytes[2] < 128 && p.bytes[3] < 128;
    }
    static Plan rejected(Status status) noexcept { Plan out; out.status = status; return out; }
    static void append(Plan& plan, int address, int value) noexcept {
        // Structural maxima:9ordinary,36keyservice,12delayservice,24CC64,
        // or204program. No accepted operation can return a truncated prefix.
        assert(plan.count < plan.writes.size());
        plan.writes[plan.count++] = {static_cast<std::uint16_t>(address), static_cast<std::uint8_t>(value)};
    }
    void release(Plan& out, int slot) const noexcept {
        const auto& p = state().patch.bytes;
        const int delta = slot / 2 + 16 * (slot % 2);
        for (int op = 0; op < 2; ++op) {
            const auto base = p[12 + op];
            const auto rate = (state().effects & 2) ? p[19 + op] : base;
            append(out, 0x2e0 + delta + 8 * op, (base & 0xf0) | (rate & 15));
        }
    }
};
} // namespace press78::research
