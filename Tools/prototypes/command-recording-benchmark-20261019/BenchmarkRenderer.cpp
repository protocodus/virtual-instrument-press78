// Gated research executable. Never run on retained fixtures until root review.
#include "../../../Source/DSP/Press78Engine.cpp"
#include "../command-audio-consumer-20261019/CommandAudioConsumer.h"
#include "BenchmarkSequence.h"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <cstring>

namespace recording=press78::research::recording;
using Consumer=press78::research::CommandAudioConsumer;
using Commands=press78::research::Mode00CompleteCommands;
namespace {
void require(bool good,const char* text) {if(!good)throw std::runtime_error(text);}
press78::Controls controls(bool command) {
    press78::Controls c;c.pitchModel=command?0:1;c.sustainMode=command?0:1;
    c.midiPitchBend=-1;c.pitchBendSemitones=0;c.masterTuneCents=0;c.hostTuneCents=0;
    c.clockOffsetPpm=0;c.clockDriftPpm=0;c.polyphony=12;
    c.masterGain=1;c.toneCutoffHz=0;c.dcBlock=false;c.outputLimit=false;c.outputCircuit=true;c.drive=0;
    c.modulationAmount=1;c.velocitySensitivity=1;c.velocityToModulation=0;
    c.chorusMode=1;c.chorusMix=1;c.chorusRateHz=press78::RecordedChorusProfile::rateHz;
    c.chorusDepthMs=press78::RecordedChorusProfile::depthMs;c.stereoWidth=1;
    c.lfoRateHz=5.24;c.triangleLfo=true;c.globalLfo=true;
    c.noiseRms=0;c.noiseModel=0;
    return c;
}
Commands::WorkingPatch working(const std::array<std::uint8_t,33>& raw) {
    Commands::WorkingPatch p;
    // Original D8F4 copies0..30; separate C79B flag replaces23. Static original
    // table validation proves all100 public raw24 flags. Byte31 was not written
    // by that loader;0 is explicit unused research padding, not recovered boot.
    std::copy_n(raw.begin()+1,31,p.bytes.begin());p.bytes[23]=raw[24];p.bytes[31]=0;
    return p;
}
void captureEpoch(Consumer& c) {
    // Underlying object is owned non-const; this narrow benchmark adapter only
    // calls an existing public calibration API before first process. No frozen
    // consumer/source change and no allocator or register metadata operation.
    auto& engine=const_cast<press78::Press78Engine&>(c.engine());
    engine.setChorusTime(-32.0/48000.0);
}
void u16(std::ostream& out,std::uint16_t x){out.put(static_cast<char>(x));out.put(static_cast<char>(x>>8));}
void u32(std::ostream& out,std::uint32_t x){u16(out,static_cast<std::uint16_t>(x));u16(out,static_cast<std::uint16_t>(x>>16));}
void sample(std::ostream& out,float x){std::uint32_t bits=0;std::memcpy(&bits,&x,4);u32(out,bits);}
void limitedLine(std::ostream& stream,const std::string& line,std::uint64_t cap,std::size_t lineCap) {
    const auto position=stream.tellp();
    require(position>=0 && line.size()<=lineCap,"Log position/line bound exceeded");
    require(static_cast<std::uint64_t>(position)+line.size()<=cap,"Log byte cap exceeded before write");
    stream.write(line.data(),static_cast<std::streamsize>(line.size()));
}
struct Renderer {
    bool command;
    std::unique_ptr<Consumer> consumer;
    std::unique_ptr<press78::Press78Engine> baseline;
    std::ofstream audio,pressure,journal;
    std::size_t inputs=0,programs=0,ons=0,offs=0,groups=0,grids=0,words=0,processFrames=0;
    int currentProgram=-1;double peak=0;
    Renderer(bool path,const std::string& wav,const std::string& csv,const std::string& commands,std::size_t frames):command(path) {
        for(const auto& p:{wav,csv,commands})require(!std::filesystem::exists(p),"Refusing existing output");
        audio.open(wav,std::ios::binary);pressure.open(csv);journal.open(commands);
        require(audio.good()&&pressure.good()&&journal.good(),"Cannot create new outputs");
        audio.write("RIFF",4);u32(audio,static_cast<std::uint32_t>(36+frames*8));audio.write("WAVEfmt ",8);u32(audio,16);u16(audio,3);u16(audio,2);u32(audio,48000);u32(audio,384000);u16(audio,8);u16(audio,32);audio.write("data",4);u32(audio,static_cast<std::uint32_t>(frames*8));
        limitedLine(pressure,"frame,input_index,kind,program,input_midi_channel,engine_source,note,velocity,active_before,active_after,command_words,allocation_slot\n",1024*1024,256);
        limitedLine(journal,"frame,origin,input_index,word_index,address,value\n",4*1024*1024,256);
        if(command) {
            consumer=std::make_unique<Consumer>();Commands::Snapshot snapshot;
            snapshot.controllers.volumeIndex=9;snapshot.controllers.bendHigh=64;snapshot.controllers.bendSpan=2;snapshot.controllers.fineSteps=0;snapshot.front.effects=4;
            require(consumer->initialize(Commands::Target::PSS780,snapshot,controls(true),48000,
                Consumer::ReverbPolicy::StoreReverbBitWithoutAudioEffect)==Consumer::Status::Ok,"Consumer initialization rejected");
            captureEpoch(*consumer);
        }else {
            baseline=std::make_unique<press78::Press78Engine>();baseline->prepare(48000);baseline->setControls(controls(false));baseline->setChorusTime(-32.0/48000.0);
        }
    }
    std::size_t active() const {return command?consumer->engine().activeVoices():baseline->activeVoices();}
    void log(std::size_t frame,const char* origin,std::size_t index) {
        if(!command)return;
        const auto& plan=consumer->lastPlan();
        // Structural ceiling:100*204+1761*9+1761*3+1761*3+1761.
        require(words+plan.count<=48576,"Complete frontend word ceiling exceeded");words+=plan.count;
        for(std::size_t i=0;i<plan.count;++i) {
            std::ostringstream row;row<<frame<<','<<origin<<','<<index<<','<<i<<','<<plan.writes[i].address<<','<<static_cast<int>(plan.writes[i].value)<<'\n';
            limitedLine(journal,row.str(),4*1024*1024,64);
        }
    }
    void event(std::size_t frame,std::size_t index,const recording::Event& e) {
        const auto before=active();++inputs;
        if(e.kind=="patch") {
            currentProgram=e.program;++programs;
            if(command)require(consumer->selectProgram(working(e.raw),static_cast<std::uint8_t>(e.program))==Consumer::Status::Ok,"Program command rejected");
            else baseline->setPatch(press78::decodeVoice(e.raw),false);
        }else if(e.kind=="on") {
            ++ons;
            if(command)require(consumer->noteOn(e.note,e.velocity)==Consumer::Status::Ok,"Note-on command rejected");
            else baseline->noteOn(e.note,e.velocity,0);
        }else {
            ++offs;
            if(command)require(consumer->noteOff(e.note)==Consumer::Status::Ok,"Note-off command rejected");
            else baseline->noteOff(e.note,0);
        }
        log(frame,"event",index);
        require(inputs<=3622 && programs<=100,"Source count cap exceeded");
        std::ostringstream row;row<<frame<<','<<index<<','<<e.kind<<','<<currentProgram<<','<<e.channel<<",0,"<<e.note<<','<<e.velocity<<','<<before<<','<<active()<<','<<(command?consumer->lastPlan().count:0)<<','<<(command?consumer->lastPlan().slot:-1)<<'\n';
        limitedLine(pressure,row.str(),1024*1024,128);
    }
    void vibrato(std::size_t frame) {
        ++grids;if(command) {require(consumer->serviceVibrato()==Consumer::Status::Ok,"Vibrato service rejected");log(frame,"vibrato",grids);}
    }
    void keyService(std::size_t frame) {
        ++groups;if(command) {require(consumer->serviceKeyOn()==Consumer::Status::Ok,"Key service rejected");log(frame,"key",groups);}
    }
    void process(std::size_t,std::size_t count) {
        std::array<float,4096> l{},r{};require(count<=l.size(),"Process overflow");
        if(command)consumer->process(l.data(),r.data(),count);else baseline->process(l.data(),r.data(),count);
        for(std::size_t i=0;i<count;++i) {require(std::isfinite(l[i])&&std::isfinite(r[i]),"Nonfinite model output");sample(audio,l[i]);sample(audio,r[i]);peak=std::max({peak,std::abs(static_cast<double>(l[i])),std::abs(static_cast<double>(r[i]))});}
        processFrames+=count;
    }
    void finish() {audio.flush();pressure.flush();journal.flush();require(audio.good()&&pressure.good()&&journal.good(),"Output write failure");}
};
}
int main(int argc,char** argv) {
    try {
        require(argc==9,"Usage: renderer A|B events.txt new.wav pressure.csv commands.csv frames block REVIEW_AUTHORIZED");
        require(std::string(argv[8])=="REVIEW_AUTHORIZED","A bound root review is required through run.py");
        const bool command=std::string(argv[1])=="B";require(command || std::string(argv[1])=="A","Unknown path");
        const auto frames=static_cast<std::size_t>(std::stoull(argv[6]));const auto block=static_cast<std::size_t>(std::stoull(argv[7]));
        require(frames==8931705,"Only frozen performance length accepted");
        std::ifstream input(argv[2]);require(input.good(),"Cannot open fixture");const auto events=recording::readEvents(input,frames);
        require(events.size()==3622,"Unexpected event count");
        Renderer renderer(command,argv[3],argv[4],argv[5],frames);recording::runSchedule(events,frames,block,renderer);renderer.finish();
        require(renderer.programs==100 && renderer.ons==1761 && renderer.offs==1761,"Unexpected source totals");
        std::cout<<"{\"path\":\""<<(command?'B':'A')<<"\",\"frames\":"<<renderer.processFrames<<",\"events\":"<<renderer.inputs<<",\"programs\":"<<renderer.programs<<",\"ons\":"<<renderer.ons<<",\"offs\":"<<renderer.offs<<",\"source_groups\":"<<renderer.groups<<",\"vibrato_invocations\":"<<renderer.grids<<",\"command_words\":"<<renderer.words<<",\"latency_frames\":32,\"chorus_epoch_seconds\":"<<std::setprecision(17)<<-32.0/48000.0<<",\"peak\":"<<renderer.peak<<",\"reverb_store_only\":"<<(command?"true":"false")<<"}\n";
        return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
