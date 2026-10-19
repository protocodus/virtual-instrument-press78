#include "Mode00CompleteCommands.h"
#include <cstdlib>
#include <iostream>
using F = press78::research::Mode00CompleteCommands;
static std::size_t checks = 0;
static void require(bool pass, const char* message) {
    ++checks;
    if (!pass) { std::cerr << message << '\n'; std::exit(1); }
}
static bool same(const F::Snapshot& a, const F::Snapshot& b) {
    const auto& x = a.front; const auto& y = b.front;
    return x.patch.bytes == y.patch.bytes && x.program == y.program && x.effects == y.effects
        && x.cachedPrograms == y.cachedPrograms && x.allocator.ranks == y.allocator.ranks
        && x.allocator.notes == y.allocator.notes && x.allocator.sources == y.allocator.sources
        && x.allocator.valid == y.allocator.valid && x.allocator.keyed == y.allocator.keyed
        && x.allocator.pending == y.allocator.pending && x.allocator.held == y.allocator.held
        && x.allocator.pool == y.allocator.pool && a.vibratoDelay == b.vibratoDelay
        && a.controllers.volumeIndex == b.controllers.volumeIndex
        && a.controllers.bendHigh == b.controllers.bendHigh
        && a.controllers.bendSpan == b.controllers.bendSpan
        && a.controllers.fineSteps == b.controllers.fineSteps;
}
static void word(const F::Plan& p, std::size_t at, int address, int value) {
    require(at < p.count && p.writes[at].address == address && p.writes[at].value == value, "ordered command mismatch");
}
static F::Snapshot sample() {
    F::Snapshot s;
    auto& p = s.front.patch.bytes;
    p[2] = 31; p[3] = 37; p[4] = 0x11; p[5] = 0xb9;
    p[12] = 0x23; p[13] = 0x47; p[19] = 1; p[20] = 5;
    p[15] = 0x73; p[21] = 11; s.front.effects = 7;
    return s;
}
int main() {
    F f;
    for (const auto& p : {f.noteOn(60), f.noteOff(60), f.serviceKeyOn(), f.serviceVibrato(), f.sustainController(1)})
        require(p.status == F::Status::UnsupportedState && p.count == 0, "unrestored state accepted");
    const auto seed = sample();
    require(f.restore(F::Target::PSS780, seed) == F::Status::Ok, "valid snapshot rejected");
    (void)f.noteOn(60); (void)f.serviceKeyOn();
    const auto populated = f.snapshot();
    for (int index = 0; index < 21; ++index) {
        auto bad = populated; auto target = F::Target::PSS780;
        switch (index) {
            case 0: bad.front.effects = 8; break;
            case 1: bad.controllers.volumeIndex = -1; break;
            case 2: bad.controllers.volumeIndex = 10; break;
            case 3: bad.controllers.bendHigh = -1; break;
            case 4: bad.controllers.bendHigh = 128; break;
            case 5: bad.controllers.bendSpan = 0; break;
            case 6: bad.controllers.bendSpan = -13; break;
            case 7: bad.controllers.bendSpan = 13; break;
            case 8: bad.controllers.fineSteps = -17; break;
            case 9: bad.controllers.fineSteps = 17; break;
            case 10: bad.vibratoDelay[0] = 255; break;
            case 11: bad.front.patch.bytes[2] = 128; break;
            case 12: bad.front.patch.bytes[3] = 255; break;
            case 13: bad.front.allocator.pool = 11; break;
            case 14: bad.front.allocator.held[1].set(60); break;
            case 15: bad.front.allocator.sources[0] = 1; break;
            case 16: bad.front.allocator.valid[0] = false; break;
            case 17: bad.front.cachedPrograms[0] = 0; break;
            case 18: bad.front.allocator.notes[0] = 35; break;
            case 19: bad.front.allocator.pending[0] = 2; break;
            case 20: target = static_cast<F::Target>(255); break;
        }
        require(f.restore(target, bad) != F::Status::Ok, "unsupported snapshot accepted");
        require(same(populated, f.snapshot()), "failed restore mutated state");
    }
    for (int n : {-1,0,35,97,127,128}) {
        require(f.noteOn(n).status != F::Status::Ok, "unsupported note-on accepted");
        require(f.noteOff(n).status != F::Status::Ok, "unsupported note-off accepted");
        require(same(populated, f.snapshot()), "bad note mutated state");
    }
    for (int v : {-1,128}) {
        require(f.noteOn(64, v).status != F::Status::Ok, "bad velocity accepted");
        require(f.sustainController(v).status != F::Status::Ok, "bad CC64 accepted");
        require(same(populated, f.snapshot()), "bad controller mutated state");
    }
    auto badPatch = seed.front.patch; badPatch.bytes[2] = 128;
    require(f.selectProgram(badPatch, 3).status == F::Status::UnsupportedPatch, "bad program patch accepted");
    require(same(populated, f.snapshot()), "rejected program mutated state");
    // Domain-bound arithmetic independent of the production output transfer.
    for (int span = -12; span <= 12; ++span) if (span) for (int high = 0; high < 128; ++high)
        for (int fine = -16; fine <= 16; ++fine) {
            F::Controllers c; c.bendSpan = span; c.bendHigh = high; c.fineSteps = fine;
            int h = high;
            if (span < 0) h = high == 0 ? 127 : high == 127 ? 0 : 128 - high;
            if (h == 62) h = 61; else if (h == 127) h = 128;
            const int numerator = std::abs(span) * (h - 64);
            const int expected = (numerator < 0 ? -((-numerator) / 2) : numerator / 2) + fine;
            require(F::controllersSupported(c), "supported controller rejected");
            require(F::pitchSteps(c) == expected, "signed bend/fine composition mismatch");
            require(36 * 32 + expected >= 0 && 96 * 32 + expected <= 4095, "supported coordinate escapes converter range");
        }
    // Actual plans compose exact TL commands before carrier-only volume/Reverb.
    for (int n = 36; n <= 96; ++n) for (int volume = 0; volume <= 9; ++volume) for (int rv : {0,4}) {
        auto s = seed; s.controllers.volumeIndex = volume; s.front.effects = static_cast<std::uint8_t>(rv);
        require(f.restore(F::Target::PSS780, s) == F::Status::Ok, "plan test restore");
        const auto p = f.noteOn(n);
        require(p.status == F::Status::Ok && p.count == 9 && p.slot == 0, "nine-word plan missing");
        word(p,0,0x2e0,0x23); word(p,1,0x2e8,0x47); word(p,2,0x208,0);
        constexpr int addends[10] = {32,32,28,24,20,16,12,8,4,0};
        const int mod = press78::firmware_level::command(31,n,0x11);
        const int car = press78::firmware_level::command(37,n,0xb9);
        word(p,3,0x260,mod + (rv ? 128 : 0));
        word(p,4,0x268,std::min(127,car + addends[volume]) + (rv ? 128 : 0));
        const auto pitch = press78::firmware_pitch::commands(n,0,0);
        for (int i=0;i<3;++i) word(p,5+static_cast<std::size_t>(i),pitch[i].address,pitch[i].value);
        word(p,8,0x2e8,0x4f);
    }
    // All raw nonzero Mode00 velocities are the same functional key edge.
    F reference; require(reference.restore(F::Target::PSS780, seed) == F::Status::Ok, "velocity reference");
    const auto expected = reference.noteOn(60,127);
    for (int velocity=1;velocity<128;++velocity) {
        require(f.restore(F::Target::PSS780,seed)==F::Status::Ok,"velocity restore");
        const auto p=f.noteOn(60,velocity); require(p.count==expected.count,"velocity changed word count");
        for(std::size_t i=0;i<p.count;++i) word(p,i,expected.writes[i].address,expected.writes[i].value);
        require(same(f.snapshot(),reference.snapshot()),"velocity changed state");
    }
    require(f.noteOn(60,0).count==3,"velocity zero does not release");
    // Every CC64 value refreshes every normal cache, even on a repeated value.
    for(int value=0;value<128;++value) {
        const auto before=f.snapshot(); const auto p=f.sustainController(value);
        require(p.status==F::Status::Ok && p.count==24,"CC64 refresh count");
        require(f.state().effects==((before.front.effects&~2)|(value?2:0)),"CC64 state");
        require(f.vibratoDelay()==before.vibratoDelay,"CC64 changed independent delay");
        require(f.state().allocator.ranks==before.front.allocator.ranks && f.state().allocator.keyed==before.front.allocator.keyed,"CC64 changed allocator");
        for(int slot=0;slot<12;++slot) {
            const int delta=slot/2+16*(slot%2);
            word(p,2*static_cast<std::size_t>(slot),0x2e0+delta,value?0x21:0x23);
            word(p,2*static_cast<std::size_t>(slot)+1,0x2e8+delta,value?0x45:0x47);
        }
    }
    // Structural maxima, deliberately restored rather than inferred from corpus.
    auto full=seed;
    for(int i=0;i<12;++i) {
        full.front.allocator.notes[i]=36+i; full.front.allocator.pending[i]=1;
        full.front.allocator.held[0].set(static_cast<std::size_t>(36+i));
    }
    require(f.restore(F::Target::PSS780,full)==F::Status::Ok,"max-key restore");
    require(f.serviceKeyOn().count==36,"max-key plan capacity");
    require(f.serviceKeyOn().count==0,"pending key starts twice");
    auto expiring=f.snapshot(); expiring.vibratoDelay.fill(1);
    require(f.restore(F::Target::PSS780,expiring)==F::Status::Ok,"max-vib restore");
    require(f.serviceVibrato().count==12,"max-vib plan capacity");
    require(f.serviceVibrato().count==0,"delay expires twice");
    const auto beforeProgram=f.snapshot(); auto next=seed.front.patch; next.bytes[23]=0;
    const auto load=f.selectProgram(next,11);
    require(load.count==204,"max-program plan capacity");
    require(f.vibratoDelay()==beforeProgram.vibratoDelay,"program changed active delay");
    require(f.state().effects==4,"program failed single-owner effect replacement");
    require(f.state().allocator.notes==beforeProgram.front.allocator.notes,"program discarded note cache");
    for(int d : {0,1,2,11,63,127}) for(int enabled : {0,1}) {
        auto s=seed; s.front.patch.bytes[21]=static_cast<std::uint8_t>(d);s.front.effects=static_cast<std::uint8_t>(enabled);
        require(f.restore(F::Target::PSS780,s)==F::Status::Ok,"VDT restore");
        (void)f.noteOn(60);const auto start=f.serviceKeyOn();
        word(start,0,0x218,d||!enabled?3:0x73);
        require(f.vibratoDelay()[0]==2*d,"VDT count initializer");
        (void)f.noteOff(60);
        int writes=0;
        for(int i=0;i<255;++i) writes+=static_cast<int>(f.serviceVibrato().count);
        require(writes==(d&&enabled?1:0),"postoff VDT expiry count");
        require(f.vibratoDelay()[0]==0,"VDT counter did not settle");
    }
    std::cout << "{\"passed\":true,\"assertions\":" << checks
              << ",\"frontend_bytes\":" << sizeof(F) << ",\"snapshot_bytes\":" << sizeof(F::Snapshot)
              << ",\"plan_bytes\":" << sizeof(F::Plan) << ",\"plan_capacity\":" << F::Plan::kCapacity << "}\n";
}
