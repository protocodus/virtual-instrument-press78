#include "Mode00ProgramCommands.h"
#include <cstdlib>
#include <iostream>
#include <new>
#include <string>

using Front = press78::research::Mode00ProgramCommands;
static bool countAllocations = false;
static std::size_t allocations = 0;
void* operator new(std::size_t size) {
    if (countAllocations) ++allocations;
    if (void* p = std::malloc(size ? size : 1)) return p;
    throw std::bad_alloc();
}
void* operator new[](std::size_t size) { return ::operator new(size); }
void operator delete(void* p) noexcept { std::free(p); }
void operator delete[](void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }
void operator delete[](void* p, std::size_t) noexcept { std::free(p); }

template<class A> static void array(const A& a) {
    std::cout << '[';
    bool first = true;
    for (const auto& value : a) {
        if (!first) std::cout << ',';
        first = false;
        std::cout << static_cast<int>(value);
    }
    std::cout << ']';
}
static void snapshot(const Front& f) {
    const auto& s = f.state(); const auto& a = s.allocator;
    std::cout << ",\"ranks\":"; array(a.ranks);
    std::cout << ",\"notes\":"; array(a.notes);
    std::cout << ",\"pending\":"; array(a.pending);
    std::cout << ",\"keyed\":"; array(a.keyed);
    std::cout << ",\"cached\":"; array(s.cachedPrograms);
    std::cout << ",\"held\":[";
    bool first = true;
    for (int i = 0; i < 128; ++i) if (a.held[0][static_cast<std::size_t>(i)]) {
        if (!first) std::cout << ',';
        first = false; std::cout << i;
    }
    std::cout << "],\"program\":" << static_cast<int>(s.program)
              << ",\"effects\":" << static_cast<int>(s.effects);
    std::cout << ",\"byte21\":"; array(f.cachedByte21());
    std::cout << ",\"byte15\":"; array(f.cachedByte15());
    std::cout << ",\"byte22\":"; array(f.cachedByte22());
}
static int number(int maximum = 255) {
    int value = -1;
    if (!(std::cin >> value) || value < 0 || value > maximum) std::exit(2);
    return value;
}
static Front::WorkingPatch patch() {
    Front::WorkingPatch p;
    for (auto& value : p.bytes) value = static_cast<std::uint8_t>(number());
    return p;
}
int main() {
    Front f;
    std::string command;
    while (std::cin >> command) {
        allocations = 0;
        if (command == "init") {
            const int target = number(780);
            if (target != 680 && target != 780) return 2;
            Front::Snapshot s;
            s.program = static_cast<std::uint8_t>(number());
            s.effects = static_cast<std::uint8_t>(number());
            s.patch = patch();
            for (auto& value : s.allocator.ranks) value = static_cast<std::uint8_t>(number());
            for (auto& value : s.allocator.notes) value = number(127);
            for (auto& value : s.allocator.pending) value = static_cast<std::uint8_t>(number());
            for (auto& value : s.allocator.keyed) value = number(1) != 0;
            const int held = number(128);
            for (int i = 0; i < held; ++i) s.allocator.held[0].set(static_cast<std::size_t>(number(127)));
            countAllocations = true;
            const auto status = f.restore(target == 780 ? Front::Target::PSS780 : Front::Target::PSS680, s);
            countAllocations = false;
            std::cout << "{\"kind\":\"init\",\"status\":" << static_cast<int>(status);
        } else if (command == "load") {
            const auto program = static_cast<std::uint8_t>(number());
            const auto p = patch();
            countAllocations = true;
            const auto plan = f.selectProgram(p, program);
            countAllocations = false;
            std::cout << "{\"kind\":\"load\",\"status\":" << static_cast<int>(plan.status)
                      << ",\"writes\":[";
            for (std::size_t i = 0; i < plan.count; ++i) {
                if (i) std::cout << ',';
                std::cout << '[' << plan.writes[i].address << ',' << static_cast<int>(plan.writes[i].value) << ']';
            }
            std::cout << "],\"released\":[";
            for (std::size_t i = 0; i < plan.releasedCount; ++i) {
                if (i) std::cout << ',';
                std::cout << static_cast<int>(plan.releasedSlots[i]);
            }
            std::cout << ']';
        } else if (command == "on" || command == "off" || command == "service") {
            const int value = number(65535);
            countAllocations = true;
            const auto event = command == "on" ? f.noteOn(value)
                : command == "off" ? f.noteOff(value) : f.service(value);
            countAllocations = false;
            std::cout << "{\"kind\":\"" << command << "\",\"status\":" << static_cast<int>(event.status)
                      << ",\"slot\":" << event.allocation.slot << ",\"edge\":" << (event.allocation.edge ? 1 : 0)
                      << ",\"keys\":[";
            for (int i = 0; i < event.allocation.keyCount; ++i) {
                if (i) std::cout << ',';
                std::cout << "[520," << static_cast<int>(event.allocation.keys[i]) << ']';
            }
            std::cout << ']';
        } else return 2;
        snapshot(f);
        std::cout << ",\"allocations\":" << allocations << "}\n";
    }
}
