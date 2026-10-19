#include "Mode00ProgramCommands.h"
#include <cstdlib>
#include <iostream>

using F = press78::research::Mode00ProgramCommands;
static unsigned checks = 0;
static void require(bool condition, int line) {
    ++checks;
    if (!condition) { std::cerr << "FAILED line " << line << '\n'; std::exit(1); }
}
#define CHECK(x) require((x), __LINE__)
static bool same(const F::Snapshot& a, const F::Snapshot& b) {
    return a.patch.bytes == b.patch.bytes && a.program == b.program && a.effects == b.effects
        && a.cachedPrograms == b.cachedPrograms && a.allocator.ranks == b.allocator.ranks
        && a.allocator.notes == b.allocator.notes && a.allocator.sources == b.allocator.sources
        && a.allocator.valid == b.allocator.valid && a.allocator.keyed == b.allocator.keyed
        && a.allocator.pending == b.allocator.pending && a.allocator.held == b.allocator.held
        && a.allocator.pool == b.allocator.pool;
}
static F::Snapshot initial() {
    F::Snapshot s;
    for (std::size_t i = 0; i < s.patch.bytes.size(); ++i)
        s.patch.bytes[i] = static_cast<std::uint8_t>((17 + 37 * i) % 256);
    return s;
}
int main() {
    for (int target = 0; target < 2; ++target) {
        F f; auto s = initial(); s.effects = 6;
        s.patch.bytes[12] = 0xa2; s.patch.bytes[13] = 0x34;
        s.patch.bytes[19] = 0xf1; s.patch.bytes[20] = 0xe5;
        CHECK(f.restore(static_cast<F::Target>(target), s) == F::Status::Ok);
        for (int n : {48, 96, 60}) { CHECK(f.noteOn(n).allocation.edge); CHECK(f.service().allocation.keyCount == 1); }
        const auto before = f.state();
        F::WorkingPatch next; next.bytes[23] = 128;
        const auto plan = f.selectProgram(next, 29);
        CHECK(plan.count == (target == 1 ? 177u : 168u));
        CHECK(f.state().effects == 5); CHECK(f.state().allocator.notes == before.allocator.notes);
        CHECK(f.state().cachedPrograms == before.cachedPrograms);
        if (target == 1) {
            constexpr int addresses[]{752,760,520,737,745,520,736,744,520};
            constexpr int values[]{161,53,24,161,53,1,161,53,0};
            for (int i = 0; i < 9; ++i) { CHECK(plan.writes[i].address == addresses[i]); CHECK(plan.writes[i].value == values[i]); }
            CHECK(plan.releasedSlots[0] == 1 && plan.releasedSlots[1] == 2 && plan.releasedSlots[2] == 0);
            CHECK(f.state().allocator.ranks[0] == 126 && f.state().allocator.ranks[1] == 124 && f.state().allocator.ranks[2] == 125);
            CHECK(f.state().allocator.held[0].none());
        } else {
            CHECK(f.state().allocator.ranks == before.allocator.ranks);
            CHECK(f.state().allocator.held == before.allocator.held);
            CHECK(f.state().allocator.keyed == before.allocator.keyed);
        }
        CHECK(f.selectProgram(next, 29).count == 168);
        CHECK(f.restore(static_cast<F::Target>(target), s) == F::Status::Ok);
        CHECK(f.noteOn(60).allocation.keyCount == 1);
        CHECK(!f.state().allocator.keyed[0]); // No implicit key service.
        (void)f.selectProgram(next, 29);
        CHECK(f.service(65535).allocation.keyCount == (target == 1 ? 0 : 1));
        CHECK(f.noteOn(60).allocation.edge == (target == 1));
    }
    // Every control-byte value with different raw operator data, all slots.
    for (int value = 0; value < 256; ++value) {
        F f; auto s = initial(); auto p = s.patch;
        p.bytes[14] = p.bytes[15] = static_cast<std::uint8_t>(value);
        const auto plan = f.selectProgram(p, 17);
        CHECK(plan.count == 168);
        for (int slot = 0; slot < 12; ++slot) {
            const auto start = static_cast<std::size_t>(14 * slot);
            const int delta = slot / 2 + 16 * (slot % 2), odd = 128 * (slot % 2);
            CHECK(plan.writes[start].address == 608 + delta && plan.writes[start].value == 127);
            CHECK(plan.writes[start+1].address == 616 + delta && plan.writes[start+1].value == 127);
            CHECK(plan.writes[start+2].address == 544 + slot / 2);
            CHECK(plan.writes[start+2].value == 64 + odd + (value & 8) + (value & 16) + (value & 32));
            CHECK(plan.writes[start+13].address == 536 + slot / 2);
            CHECK(plan.writes[start+13].value == odd + (value & 1) + (value & 2) + (value & 16) + (value & 32) + (value & 64));
            constexpr int fields[]{0,1,6,7,8,9,10,11,12,13};
            constexpr int addresses[]{576,584,640,648,672,680,704,712,736,744};
            for (int i = 0; i < 10; ++i) {
                CHECK(plan.writes[start+3+static_cast<std::size_t>(i)].value == p.bytes[fields[i]]);
                CHECK(plan.writes[start+3+static_cast<std::size_t>(i)].address == addresses[i] + delta);
            }
        }
    }
    F f;
    for (int n = 48; n <= 60; ++n) { (void)f.noteOn(n); (void)f.service(); }
    CHECK(f.state().allocator.held[0].count() == 13);
    const auto plan = f.selectProgram({}, 0);
    CHECK(plan.count == F::ProgramPlan::kCapacity && plan.releasedCount == 12);
    CHECK(f.state().allocator.held[0].none());
    // Scope guards: every unsupported source bit/cache/pending branch rejects
    // without mutating the existing snapshot or control caches.
    const auto before = f.state();
    auto reject = [&](const F::Snapshot& s, F::Target target = F::Target::PSS780) {
        const auto byte15 = f.cachedByte15(), byte21 = f.cachedByte21(), byte22 = f.cachedByte22();
        CHECK(f.restore(target, s) == F::Status::UnsupportedState);
        CHECK(same(before, f.state()));
        CHECK(byte15 == f.cachedByte15() && byte21 == f.cachedByte21() && byte22 == f.cachedByte22());
    };
    for (int n = 0; n < 128; ++n) {
        auto s = initial(); s.allocator.held[1].set(static_cast<std::size_t>(n)); reject(s);
        if (n < 36 || n > 96) { s = initial(); s.allocator.held[0].set(static_cast<std::size_t>(n)); reject(s); }
    }
    for (int i = 0; i < 12; ++i) {
        for (int source : {-1,1,2,127}) { auto s = initial(); s.allocator.sources[i] = source; reject(s); }
        for (int pending : {2,7,255}) { auto s = initial(); s.allocator.pending[i] = static_cast<std::uint8_t>(pending); reject(s); }
        for (int note : {-1,1,35,97,127,128}) { auto s = initial(); s.allocator.notes[i] = note; reject(s); }
        auto s = initial(); s.allocator.valid[i] = false; reject(s);
        s = initial(); s.cachedPrograms[i] = 99; reject(s);
    }
    for (int pool : {-1,0,1,11,13,255}) { auto s = initial(); s.allocator.pool = pool; reject(s); }
    reject(initial(), static_cast<F::Target>(2));
    for (int note : {-1,0,35,97,127,128}) {
        CHECK(f.noteOn(note).status == F::Status::UnsupportedNote);
        CHECK(f.noteOff(note).status == F::Status::UnsupportedNote);
        CHECK(same(before, f.state()));
    }
    CHECK(f.service(-1).status == F::Status::UnsupportedService);
    CHECK(f.service(65536).status == F::Status::UnsupportedService);
    CHECK(same(before, f.state()));
    CHECK(f.noteOn(36).status == F::Status::Ok); CHECK(f.noteOn(96).status == F::Status::Ok);
    // All twelve pending slots fit the unchanged allocator's Decision capacity.
    auto s = initial(); s.allocator.pending.fill(1);
    CHECK(f.restore(F::Target::PSS680, s) == F::Status::Ok);
    CHECK(f.service(65535).allocation.keyCount == 12);
    CHECK(f.service().allocation.keyCount == 0);
    std::cout << "{\"passed\":true,\"assertions\":" << checks
              << ",\"frontend_bytes\":" << sizeof(F)
              << ",\"snapshot_bytes\":" << sizeof(F::Snapshot)
              << ",\"plan_bytes\":" << sizeof(F::ProgramPlan)
              << ",\"allocator_bytes\":" << sizeof(press78::Mode00Allocator) << "}\n";
}
