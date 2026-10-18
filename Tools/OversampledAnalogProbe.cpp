// SDK-free native output-circuit verification tool. No synthesized noise.
// The descriptor mode independently evaluates full C/G recurrence, bypassing
// AnalogOutput and all SOS/state-reduction implementation paths.
#include "../Source/DSP/OversampledAnalogOutput.h"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <new>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

static std::size_t allocationCount=0;
void* operator new(std::size_t size){++allocationCount;if(void* p=std::malloc(size))return p;throw std::bad_alloc();}
void operator delete(void* p) noexcept {std::free(p);}
void operator delete(void* p,std::size_t) noexcept {std::free(p);}

namespace {
class Resampler4x {
public:
  Resampler4x():a(press78::analog_oversampling_detail::outerOdd),b(press78::analog_oversampling_detail::innerOdd),c(press78::analog_oversampling_detail::innerOdd),d(press78::analog_oversampling_detail::outerOdd){}
  void prepare(double)noexcept{a.reset();b.reset();c.reset();d.reset();}
  double process(double x)noexcept{
    const auto v=a.process(x);const auto u0=b.process(v[0]),u1=b.process(v[1]);
    const double even=c.process(u0[0],u0[1]);const double odd=c.process(u1[0],u1[1]);
    return d.process(even,odd);
  }
private:
 press78::analog_oversampling_detail::Up2<64>a;press78::analog_oversampling_detail::Up2<32>b;
 press78::analog_oversampling_detail::Down2<32>c;press78::analog_oversampling_detail::Down2<64>d;
};

template<class Filter>void impulse(double rate,int frames,const std::filesystem::path&path){
 Filter f;f.prepare(rate);std::ofstream stream(path,std::ios::binary);
 if(!stream)throw std::runtime_error("Cannot open impulse output");
 for(int i=0;i<frames;++i){const double y=f.process(i==0?1.:0.);stream.write(reinterpret_cast<const char*>(&y),sizeof(y));}
}

template<class Filter>double benchmark(double rate,int frames){
 std::array<double,1024> input{};
 for(std::size_t n=0;n<input.size();++n)input[n]=.1*std::sin(n*.032)+.02*std::cos(n*.7)+.007*std::sin(n*1.123);
 std::vector<double>times;Filter f;
 for(int rep=0;rep<4;++rep){
  f.prepare(rate);double sum=0;
  for(int n=0;n<4096;++n)sum+=f.process(input[n%input.size()]);
  const auto t0=std::chrono::steady_clock::now();
  for(int n=0;n<frames;++n)sum+=f.process(input[n%input.size()]);
  const auto t1=std::chrono::steady_clock::now();
  volatile double sink=sum;(void)sink;
  if(rep>0)times.push_back(std::chrono::duration<double>(t1-t0).count());
 }
 std::sort(times.begin(),times.end());return times[1];
}

void validate(double rate,std::ostream& out){
 const std::size_t frames=static_cast<std::size_t>(rate*2.);
 std::vector<double>input(frames),one(frames),blocks(frames),again(frames);
 for(std::size_t n=0;n<frames;++n){double t=n/rate;input[n]=.2*std::sin(2*3.1415926535897932384626433832795*137*t)+.1*std::cos(2*3.1415926535897932384626433832795*11713*t)+.03*std::sin(2*3.1415926535897932384626433832795*19997*t);}
 press78::OversampledAnalogOutput f;f.prepare(rate);
 auto allocBefore=allocationCount;
 for(std::size_t n=0;n<frames;++n)one[n]=f.process(input[n]);
 const auto processAllocations=allocationCount-allocBefore;
 f.reset();const std::array<std::size_t,10>sizes{{1,17,64,3,127,1024,61,2,4096,7}};
 for(std::size_t pos=0,chunk=0;pos<frames;++chunk){const std::size_t count=std::min(sizes[chunk%sizes.size()],frames-pos);f.processBlock(input.data()+pos,blocks.data()+pos,count);pos+=count;}
 f.reset();f.processBlock(input.data(),again.data(),frames);
 double blockError=0,resetError=0,peak=0;
 for(std::size_t n=0;n<frames;++n){blockError=std::max(blockError,std::abs(one[n]-blocks[n]));resetError=std::max(resetError,std::abs(one[n]-again[n]));peak=std::max(peak,std::abs(one[n]));if(!std::isfinite(one[n]))throw std::runtime_error("Nonfinite multitone output");}
 f.reset();double silence=0;for(int n=0;n<20000;++n)silence=std::max(silence,std::abs(f.process(0)));
 f.reset();double stepPeak=0,stepTail=0;const int stepFrames=static_cast<int>(rate*5);
 for(int n=0;n<stepFrames;++n){const double y=f.process(1);if(!std::isfinite(y))throw std::runtime_error("Nonfinite step output");stepPeak=std::max(stepPeak,std::abs(y));if(n>stepFrames-static_cast<int>(rate))stepTail=std::max(stepTail,std::abs(y));}
 f.reset();double clean=0;for(int n=0;n<20000;++n)clean=std::max(clean,std::abs(f.process(0)));
 const bool passed=blockError==0&&resetError==0&&silence==0&&clean==0&&stepTail<1e-7&&processAllocations==0;
 if(!passed){std::cerr<<"rate="<<rate<<" block="<<blockError<<" reset="<<resetError<<" silence="<<silence<<" clean="<<clean<<" stepTail="<<stepTail<<" allocations="<<processAllocations<<"\n";throw std::runtime_error("Validation failed");}
 out<<"{\"sample_rate\":"<<rate<<",\"frames\":"<<frames<<",\"block_max_error\":"<<blockError<<",\"reset_max_error\":"<<resetError<<",\"zero_input_peak\":"<<silence<<",\"reset_after_step_zero_peak\":"<<clean<<",\"step_peak\":"<<stepPeak<<",\"step_final_second_peak\":"<<stepTail<<",\"multitone_peak\":"<<peak<<",\"process_heap_allocations\":"<<processAllocations<<",\"passed\":true}";
}
}

namespace {
std::vector<double> loadDoubles(const char* path) {
    std::ifstream input(path,std::ios::binary);
    if(!input)throw std::runtime_error("Cannot open descriptor input");
    const auto bytes=std::filesystem::file_size(path);
    if(bytes%sizeof(double)!=0)throw std::runtime_error("Invalid binary input size");
    std::vector<double> data(bytes/sizeof(double));
    input.read(reinterpret_cast<char*>(data.data()),bytes);
    if(!input)throw std::runtime_error("Cannot read descriptor input");
    return data;
}
void descriptor(const char* aPath,const char* bPath,const char* inputPath,const char* outputPath) {
    const auto a=loadDoubles(aPath),b=loadDoubles(bPath),input=loadDoubles(inputPath);
    if(a.size()!=19*19||b.size()!=19)throw std::runtime_error("Unexpected descriptor dimensions");
    std::ofstream output(outputPath,std::ios::binary);
    std::array<double,19> state{},next{};
    double previous=0;
    for(double u:input) {
        const double sum=u+previous;
        for(int i=0;i<19;++i) {
            double value=b[i]*sum;
            for(int j=0;j<19;++j)value+=a[i*19+j]*state[j];
            next[i]=value;
        }
        state=next;previous=u;
        const double sample=state[9];
        output.write(reinterpret_cast<const char*>(&sample),sizeof(sample));
    }
    if(!output)throw std::runtime_error("Cannot write descriptor output");
}
void checkSanitization(std::ostream& out) {
    const std::array<double,5> input{{NAN,INFINITY,-1.0,0.0,1e9}};
    const std::array<double,5> expected{{48000.0,48000.0,8000.0,8000.0,192000.0}};
    bool exact=true;
    for(std::size_t i=0;i<input.size();++i) {
        press78::OversampledAnalogOutput test,reference;
        test.prepare(input[i]);reference.prepare(expected[i]);
        for(int n=0;n<8192;++n) {
            const double x=n==0?1.0:0.0;
            const double a=test.process(x),b=reference.process(x);
            exact=exact&&std::isfinite(a)&&a==b;
        }
    }
    if(!exact)throw std::runtime_error("Invalid-rate sanitization mismatch");
    out<<"{\"passed\":true,\"nan_inf_fallback_hz\":48000,\"minimum_hz\":8000,\"maximum_hz\":192000}";
}
}

int main(int argc,char** argv) {
    try {
        if(argc<2)throw std::runtime_error("Modes: impulse, validate, benchmark, descriptor, metadata, sanitize");
        const std::string mode=argv[1];
        std::cout<<std::setprecision(17);
        if(mode=="descriptor") {
            if(argc!=6)throw std::runtime_error("descriptor A.f64 B.f64 input.f64 output.f64");
            descriptor(argv[2],argv[3],argv[4],argv[5]);return 0;
        }
        if(mode=="metadata") {
            std::cout<<"{\"latency_frames\":"<<press78::OversampledAnalogOutput::kLatencyFrames
                <<",\"instance_bytes\":"<<sizeof(press78::OversampledAnalogOutput)
                <<",\"baseline_bytes\":"<<sizeof(press78::AnalogOutput)<<"}\n";return 0;
        }
        if(mode=="sanitize"){checkSanitization(std::cout);std::cout<<'\n';return 0;}
        if(argc<3)throw std::runtime_error("Missing sample rate");
        const double rate=std::stod(argv[2]);
        if(!std::isfinite(rate)||rate<8000||rate>192000)throw std::runtime_error("Invalid sample rate");
        if(mode=="validate") {
            validate(rate,std::cout);std::cout<<'\n';return 0;
        }
        if(mode=="benchmark") {
            if(argc!=4)throw std::runtime_error("benchmark rate frames");
            const int frames=std::stoi(argv[3]);
            if(frames<1||frames>19200000)throw std::runtime_error("Invalid frame count");
            const double oldTime=benchmark<press78::AnalogOutput>(rate,frames);
            const double newTime=benchmark<press78::OversampledAnalogOutput>(rate,frames);
            std::cout<<"{\"sample_rate\":"<<rate<<",\"frames_per_repetition\":"<<frames
                <<",\"median_repetitions\":3,\"baseline_seconds\":"<<oldTime
                <<",\"candidate_seconds\":"<<newTime
                <<",\"candidate_realtime_single_thread_percent\":"<<newTime/(frames/rate)*100.0
                <<",\"candidate_to_baseline_cpu_ratio\":"<<newTime/oldTime<<"}\n";return 0;
        }
        if(mode=="impulse") {
            if(argc!=6)throw std::runtime_error("impulse rate baseline|oversampled|resampler frames output.f64");
            const std::string kind=argv[3];const int frames=std::stoi(argv[4]);
            if(frames<1||frames>19200000)throw std::runtime_error("Invalid frame count");
            if(kind=="baseline")impulse<press78::AnalogOutput>(rate,frames,argv[5]);
            else if(kind=="oversampled")impulse<press78::OversampledAnalogOutput>(rate,frames,argv[5]);
            else if(kind=="resampler")impulse<Resampler4x>(rate,frames,argv[5]);
            else throw std::runtime_error("Unknown impulse mode");
            return 0;
        }
        throw std::runtime_error("Unknown probe mode");
    } catch(const std::exception& error) {
        std::cerr<<error.what()<<'\n';return 1;
    }
}
