#include "Mode00CompleteCommands.h"
#include <cstdlib>
#include <iostream>
#include <new>
#include <string>
#include <vector>
using Front = press78::research::Mode00CompleteCommands;
static bool counting = false;
static std::size_t allocations = 0;
void* operator new(std::size_t size) {
    if (counting) ++allocations;
    if (void* p = std::malloc(size ? size : 1)) return p;
    throw std::bad_alloc();
}
void* operator new[](std::size_t size) { return ::operator new(size); }
void operator delete(void* p) noexcept { std::free(p); }
void operator delete[](void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }
void operator delete[](void* p, std::size_t) noexcept { std::free(p); }
static int number(int low = 0, int high = 255) {
    int x = 0;
    if (!(std::cin >> x) || x < low || x > high) std::exit(2);
    return x;
}
template<class A> void array(const A& a) {
    std::cout << '[';
    bool first = true;
    for (auto x : a) { if (!first) std::cout << ','; first = false; std::cout << static_cast<int>(x); }
    std::cout << ']';
}
static Front::WorkingPatch patch() {
    Front::WorkingPatch p;
    for (auto& x : p.bytes) x = static_cast<std::uint8_t>(number());
    return p;
}
static void state(const Front& f) {
    const auto& s = f.state(); const auto& a = s.allocator;
    std::cout << ",\"ranks\":"; array(a.ranks);
    std::cout << ",\"notes\":"; array(a.notes);
    std::cout << ",\"pending\":"; array(a.pending);
    std::cout << ",\"keyed\":"; array(a.keyed);
    std::cout << ",\"cached\":"; array(s.cachedPrograms);
    std::cout << ",\"delay\":"; array(f.vibratoDelay());
    std::cout << ",\"byte21\":"; array(f.cachedByte21());
    std::cout << ",\"byte15\":"; array(f.cachedByte15());
    std::cout << ",\"byte22\":"; array(f.cachedByte22());
    std::cout << ",\"held\":[";
    bool first = true;
    for (int n = 0; n < 128; ++n) if (a.held[0][static_cast<std::size_t>(n)]) {
        if (!first) std::cout << ',';
        first = false; std::cout << n;
    }
    std::cout << "],\"effects\":" << static_cast<int>(s.effects)
              << ",\"program\":" << static_cast<int>(s.program)
              << ",\"allocations\":" << allocations;
}
int main() {
    Front f; std::string command;
    while (std::cin >> command) {
        allocations = 0;
        std::vector<Front::RegisterWrite> words;
        if (command == "init") {
            const int model = number(680, 780);
            if (model != 680 && model != 780) return 2;
            Front::Snapshot s;
            s.front.program = static_cast<std::uint8_t>(number());
            s.front.effects = static_cast<std::uint8_t>(number());
            s.controllers.volumeIndex = number(0, 9);
            s.controllers.bendHigh = number(0, 127);
            s.controllers.bendSpan = number(-12, 12);
            s.controllers.fineSteps = number(-16, 16);
            s.front.patch = patch();
            for (auto& x : s.front.allocator.ranks) x = static_cast<std::uint8_t>(number());
            for (auto& x : s.front.allocator.notes) x = number(0, 127);
            for (auto& x : s.front.allocator.pending) x = static_cast<std::uint8_t>(number());
            for (auto& x : s.front.allocator.keyed) x = number(0, 1) != 0;
            for (auto& x : s.vibratoDelay) x = static_cast<std::uint8_t>(number());
            const int held = number(0, 128);
            for (int n = 0; n < held; ++n) s.front.allocator.held[0].set(static_cast<std::size_t>(number(0, 127)));
            counting = true;
            const auto status = f.restore(model == 780 ? Front::Target::PSS780 : Front::Target::PSS680, s);
            counting = false;
            std::cout << "{\"kind\":\"init\",\"status\":" << static_cast<int>(status);
        } else {
            Front::Plan plan;
            if (command == "on") {
                const int n = number(0, 127), v = number(0, 127);
                counting = true; plan = f.noteOn(n, v); counting = false;
            } else if (command == "off") {
                const int n = number(0, 127);
                counting = true; plan = f.noteOff(n); counting = false;
            } else if (command == "cc64") {
                const int v = number(0, 127);
                counting = true; plan = f.sustainController(v); counting = false;
            } else if (command == "load") {
                const auto program = static_cast<std::uint8_t>(number());
                const auto p = patch();
                counting = true; plan = f.selectProgram(p, program); counting = false;
            } else if (command == "key" || command == "vib" || command == "mixed") {
                // Fixture aggregation only. The component API always receives
                // one explicit service invocation and returns a complete plan.
                const int count = number(0, 255);
                for (int i = 0; i < count; ++i) {
                    if (command != "vib") {
                        counting = true; plan = f.serviceKeyOn(); counting = false;
                        if (plan.status != Front::Status::Ok) return 3;
                        words.insert(words.end(), plan.writes.begin(), plan.writes.begin() + static_cast<std::ptrdiff_t>(plan.count));
                    }
                    if (command != "key") {
                        counting = true; plan = f.serviceVibrato(); counting = false;
                        if (plan.status != Front::Status::Ok) return 3;
                        words.insert(words.end(), plan.writes.begin(), plan.writes.begin() + static_cast<std::ptrdiff_t>(plan.count));
                    }
                }
                plan.count = 0;
            } else return 2;
            if (plan.count) words.insert(words.end(), plan.writes.begin(), plan.writes.begin() + static_cast<std::ptrdiff_t>(plan.count));
            std::cout << "{\"kind\":\"" << command << "\",\"status\":" << static_cast<int>(plan.status) << ",\"writes\":[";
            for (std::size_t i = 0; i < words.size(); ++i) {
                if (i) std::cout << ',';
                std::cout << '[' << words[i].address << ',' << static_cast<int>(words[i].value) << ']';
            }
            std::cout << ']';
        }
        state(f); std::cout << "}\n";
    }
}
