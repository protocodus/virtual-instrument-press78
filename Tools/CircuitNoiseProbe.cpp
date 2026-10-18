// Standalone validation probe; not included in the instrument runtime.
#include "../Source/DSP/CircuitNoise.h"
#include <fstream>
#include <iostream>
#include <chrono>
#include <string>
#include <cstdlib>
int main(int argc,char** argv) {
    if(argc!=5)return 2;
    const std::string mode=argv[1];const double sr=std::atof(argv[2]);
    const auto count=std::strtoull(argv[3],nullptr,10);
    press78::CircuitNoise noise;noise.prepare(sr);
    std::ofstream out(argv[4],std::ios::binary);
    const auto start=std::chrono::steady_clock::now();
    for(std::uint64_t n=0;n<count;++n) {
        std::array<double,2> value;
        if(mode=="probe") {
            std::array<double,14> white{};
            for(unsigned j=0;j<14;++j)white[j]=(static_cast<int>((n*17+j*31)%101)-50)/50.0;
            value=noise.processWhite(white);
        } else value=noise.process();
        out.write(reinterpret_cast<const char*>(value.data()),sizeof(value));
    }
    out.close();
    const double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    std::cout<<"{\"bytes\":"<<sizeof(noise)<<",\"seconds\":"<<elapsed<<",\"sample_rate\":"<<noise.sampleRate()<<",\"frames\":"<<count<<"}\n";
}
