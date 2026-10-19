#pragma once
#include <algorithm>
#include <array>
#include <bitset>
#include <cstdint>

namespace press78 {

// Independently expressed normal Mode00 allocation command behavior. No ROM,
// patch data, chip timing, oscillator/reset law or rhythm engine is present.
// The second source namespace and first-N pool are explicit host extensions.
struct Mode00Allocator {
    struct Decision {
        bool edge = false;
        int slot = -1;
        std::array<std::uint8_t, 12> keys{};
        int keyCount = 0;
    };
    std::array<std::uint8_t, 12> ranks{};
    std::array<int, 12> notes{}, sources{};
    std::array<bool, 12> valid{}, keyed{};
    std::array<std::uint8_t, 12> pending{};
    std::array<std::bitset<128>, 2> held{};
    int pool = 12;

    Mode00Allocator() noexcept { reset(12); }
    static bool validSource(int source) noexcept { return source == 0 || source == 1; }
    void reset(int polyphony) noexcept {
        ranks.fill(0); notes.fill(0); sources.fill(0); valid.fill(true);
        keyed.fill(false); pending.fill(0);
        for (auto& h : held) h.reset();
        pool = 12;
        setPolyphony(polyphony);
    }
    void setPolyphony(int polyphony) noexcept {
        const int next = std::clamp(polyphony, 1, 12);
        if (next < pool) for (int i = next; i < 12; ++i) {
            ranks[i] = 0; valid[i] = false; keyed[i] = false; pending[i] = 0;
        }
        pool = next;
    }
    void age() noexcept {
        for (auto& rank : ranks) if (rank != 0 && rank != 128) --rank;
    }
    int find(int note, int source) const noexcept {
        for (int i = pool - 1; i >= 0; --i)
            if (valid[i] && notes[i] == note && sources[i] == source) return i;
        return -1;
    }
    std::uint8_t keyCommand(int slot) const noexcept {
        const int pair = slot / 2;
        return static_cast<std::uint8_t>(pair | (keyed[2 * pair] ? 24 : 0)
                                        | (keyed[2 * pair + 1] ? 96 : 0));
    }
    void releaseSlot(int slot, Decision& out) noexcept {
        ranks[slot] = 127; age(); pending[slot] = 0; keyed[slot] = false;
        out.keys[out.keyCount++] = keyCommand(slot);
    }
    Decision noteOn(int note, int source) noexcept {
        Decision out;
        if (!validSource(source) || note < 0 || note > 127 || held[source][note]) return out;
        held[source].set(static_cast<std::size_t>(note)); out.edge = true;
        int slot = find(note, source);
        if (slot < 0) {
            int smallest = 255;
            for (int i = 0; i < pool; ++i) if (ranks[i] < smallest) {
                smallest = ranks[i]; slot = i;
            }
        }
        if (slot < 0) return out;
        releaseSlot(slot, out);
        notes[slot] = note; sources[slot] = source; valid[slot] = true;
        pending[slot] = 1; ranks[slot] = 255; age(); out.slot = slot;
        return out;
    }
    Decision noteOff(int note, int source) noexcept {
        Decision out;
        if (!validSource(source) || note < 0 || note > 127 || !held[source][note]) return out;
        held[source].reset(static_cast<std::size_t>(note)); out.edge = true;
        out.slot = find(note, source);
        if (out.slot >= 0) releaseSlot(out.slot, out);
        return out;
    }
    // Explicit invocation counter for original command-fixture checks only.
    // The engine invokes one immediately after its existing immediate noteOn;
    // it does not invent or schedule a CPU service time in the audio process.
    Decision service(int invocations) noexcept {
        Decision out;
        for (int n = 0; n < invocations; ++n) for (int i = 0; i < pool; ++i) {
            if (pending[i] && --pending[i] == 0) {
                keyed[i] = true; out.keys[out.keyCount++] = keyCommand(i);
            }
        }
        return out;
    }
    void allNotesOff() noexcept {
        for (int source = 0; source < 2; ++source)
            for (int note = 0; note < 128; ++note)
                if (held[source][note]) (void)noteOff(note, source);
    }
};
} // namespace press78
