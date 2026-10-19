#pragma once
#include "FirmwareAllocation.h"
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>

namespace press78::research {

// Command-only normal Mode00 frontend. No oscillator, envelope, output circuit,
// original CPU, factory bank, host source extension or timebase is implemented.
class Mode00ProgramCommands {
public:
    enum class Target : std::uint8_t { PSS680, PSS780 };
    enum class Status : std::uint8_t { Ok, UnsupportedState, UnsupportedNote, UnsupportedService };
    struct WorkingPatch {
        // Already resolved shared-working bytes. Byte23 includes the separate
        // factory effect flags; raw bank data alone is not the input contract.
        std::array<std::uint8_t, 32> bytes{};
    };
    struct RegisterWrite {
        std::uint16_t address = 0;
        std::uint8_t value = 0;
    };
    struct Snapshot {
        Mode00Allocator allocator{};
        WorkingPatch patch{};
        std::array<std::uint8_t, 12> cachedPrograms{};
        std::uint8_t program = 0, effects = 0;
        Snapshot() noexcept { cachedPrograms.fill(255); }
    };
    struct Event {
        Status status = Status::Ok;
        // Selected slot / paired key commands only, not complete note-on IO.
        Mode00Allocator::Decision allocation{};
    };
    struct ProgramPlan {
        static constexpr std::size_t kCapacity = 12 * 3 + 12 * 14;
        Status status = Status::Ok;
        std::array<RegisterWrite, kCapacity> writes{};
        std::size_t count = 0;
        std::array<std::uint8_t, 12> releasedSlots{};
        std::size_t releasedCount = 0;
    };

    // Empty logical state only, not an emulated original boot or a sound patch.
    Mode00ProgramCommands() noexcept = default;

    // Explicit fixture/state boundary. Rejection leaves every existing state
    // value untouched. Partial pools, CV and unsupported pending branches are
    // deliberately rejected, not converted to an invented keyboard policy.
    Status restore(Target target, const Snapshot& snapshot) noexcept {
        if (!supported(target, snapshot)) return Status::UnsupportedState;
        state_ = snapshot;
        target_ = target;
        refreshCaches();
        return Status::Ok;
    }

    Event noteOn(int note) noexcept {
        if (!normalNote(note)) return {Status::UnsupportedNote, {}};
        return {Status::Ok, state_.allocator.noteOn(note, 0)};
    }
    Event noteOff(int note) noexcept {
        if (!normalNote(note)) return {Status::UnsupportedNote, {}};
        return {Status::Ok, state_.allocator.noteOff(note, 0)};
    }
    Event service(int invocations = 1) noexcept {
        if (invocations < 0 || invocations > 65535)
            return {Status::UnsupportedService, {}};
        // No implicit service in noteOn. This is an invocation count, not a
        // recovered millisecond period. Other service IO is outside this view.
        return {Status::Ok, state_.allocator.service(invocations)};
    }

    ProgramPlan selectProgram(const WorkingPatch& patch, std::uint8_t program) noexcept {
        ProgramPlan plan;
        if (target_ == Target::PSS780) {
            // Verified musical-key order, NOT helper.allNotesOff()'s ascending
            // host loop. An uncached stolen input clears without a new slot.
            for (int note = 96; note >= 36; --note) {
                if (!state_.allocator.held[0][static_cast<std::size_t>(note)]) continue;
                const auto decision = state_.allocator.noteOff(note, 0);
                if (decision.slot < 0) continue;
                const int slot = decision.slot;
                plan.releasedSlots[plan.releasedCount++] = static_cast<std::uint8_t>(slot);
                const int delta = slot / 2 + 16 * (slot % 2);
                for (int op = 0; op < 2; ++op) {
                    const auto base = state_.patch.bytes[12 + op];
                    const auto rate = (state_.effects & 2) ? state_.patch.bytes[19 + op] : base;
                    append(plan, 0x2e0 + delta + 8 * op, (base & 0xf0) | (rate & 15));
                }
                assert(decision.keyCount == 1);
                append(plan, 0x208, decision.keys[0]);
            }
        }
        // Old RR/SRR and state were consumed before replacing shared metadata.
        state_.patch = patch;
        state_.program = program;
        state_.effects = static_cast<std::uint8_t>((state_.effects & 0xfc)
            | ((patch.bytes[23] & 128) ? 1 : 0) | ((patch.bytes[23] & 64) ? 2 : 0));
        state_.cachedPrograms.fill(255);
        refreshCaches();
        for (int slot = 0; slot < 12; ++slot) reloadSlot(plan, slot);
        return plan;
    }

    const Snapshot& state() const noexcept { return state_; }
    Target target() const noexcept { return target_; }
    const std::array<std::uint8_t, 12>& cachedByte21() const noexcept { return byte21_; }
    const std::array<std::uint8_t, 12>& cachedByte15() const noexcept { return byte15_; }
    const std::array<std::uint8_t, 12>& cachedByte22() const noexcept { return byte22_; }

private:
    Target target_ = Target::PSS780;
    Snapshot state_{};
    std::array<std::uint8_t, 12> byte21_{}, byte15_{}, byte22_{};

    static bool normalNote(int note) noexcept { return note >= 36 && note <= 96; }
    static bool supported(Target target, const Snapshot& s) noexcept {
        if (target != Target::PSS680 && target != Target::PSS780) return false;
        const auto& a = s.allocator;
        if (a.pool != 12 || a.held[1].any()) return false;
        for (int note = 0; note < 128; ++note)
            if (!normalNote(note) && a.held[0][static_cast<std::size_t>(note)]) return false;
        for (int i = 0; i < 12; ++i) {
            if (!a.valid[i] || a.sources[i] != 0 || a.pending[i] > 1 || s.cachedPrograms[i] != 255)
                return false;
            if (a.notes[i] != 0 && !normalNote(a.notes[i])) return false;
        }
        return true;
    }
    static void append(ProgramPlan& plan, int address, int value) noexcept {
        // Distinct held pitches can match at most twelve cached slots. Thus
        // release prefixes <=36 words and the suffix is exactly168 words.
        assert(plan.count < plan.writes.size());
        plan.writes[plan.count++] = {static_cast<std::uint16_t>(address), static_cast<std::uint8_t>(value)};
    }
    void refreshCaches() noexcept {
        byte21_.fill(state_.patch.bytes[21] & 0x7f);
        byte15_.fill(state_.patch.bytes[15] & 0x73);
        byte22_.fill(state_.patch.bytes[22]);
    }
    void reloadSlot(ProgramPlan& plan, int slot) const noexcept {
        const int delta = slot / 2 + 16 * (slot % 2);
        const int pair = slot / 2, odd = (slot % 2) ? 0x80 : 0;
        const auto& p = state_.patch.bytes;
        append(plan, 0x260 + delta, 127);
        append(plan, 0x268 + delta, 127);
        append(plan, 0x220 + pair, (p[14] & 0x38) | 0x40 | odd);
        constexpr std::array<int, 5> fields{{0, 6, 8, 10, 12}};
        constexpr std::array<int, 5> bases{{0x240, 0x280, 0x2a0, 0x2c0, 0x2e0}};
        for (std::size_t i = 0; i < fields.size(); ++i) {
            append(plan, bases[i] + delta, p[fields[i]]);
            append(plan, bases[i] + delta + 8, p[fields[i] + 1]);
        }
        append(plan, 0x218 + pair, (p[15] & 0x73) | odd);
    }
};
} // namespace press78::research
