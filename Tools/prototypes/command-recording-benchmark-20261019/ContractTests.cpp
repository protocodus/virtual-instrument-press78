#define main gated_benchmark_renderer_entrypoint
#include "BenchmarkRenderer.cpp"
#undef main
#include <sstream>

namespace {
std::uint64_t checks=0;
void check(bool value,const char* text){++checks;require(value,text);}
struct ScheduleWitness {
    std::vector<std::string> actions;
    std::size_t processed=0,groups=0,grids=0;
    void event(std::size_t frame,std::size_t index,const recording::Event& e){actions.push_back(std::to_string(frame)+" E"+std::to_string(index)+" "+e.kind+" ch"+std::to_string(e.channel));}
    void keyService(std::size_t frame){++groups;actions.push_back(std::to_string(frame)+" K");}
    void vibrato(std::size_t frame){++grids;actions.push_back(std::to_string(frame)+" V");}
    void process(std::size_t frame,std::size_t count){check(frame==processed,"Contiguous synthetic scheduler coverage");check(count>0,"Positive scheduler chunk");processed+=count;}
};
std::vector<recording::Event> syntheticEvents() {
    const std::string hex(66,'0');
    std::istringstream input("0 patch "+hex+"\n0 on 36 127 0\n239 off 36 0\n240 patch "+hex+"\n240 on 48 127 1\n240 off 48 1\n240 on 60 127 0\n480 off 60 0\n");
    return recording::readEvents(input,1000);
}
void pureTests() {
    std::ostringstream log;
    limitedLine(log,"abc",3,3);check(log.str()=="abc","Bounded log accepts exact cap");
    bool byteRejected=false;try{limitedLine(log,"d",3,3);}catch(const std::runtime_error&){byteRejected=true;}
    check(byteRejected && log.str()=="abc","Log byte overflow rejected before write");
    bool lineRejected=false;try{limitedLine(log,"long",100,2);}catch(const std::runtime_error&){lineRejected=true;}
    check(lineRejected && log.str()=="abc","Log line overflow rejected before write");
    const auto events=syntheticEvents();check(events.size()==8,"Synthetic parsed row count");
    check(events[4].channel==1 && events[6].channel==0,"Original MIDI channels retained");
    ScheduleWitness expected;recording::runSchedule(events,1000,256,expected);
    check(expected.groups==4 && expected.grids==4 && expected.processed==1000,"Service/source totals");
    const std::vector<std::string> actions={"0 E0 patch ch-1","0 E1 on ch0","0 K","239 E2 off ch0","239 K","240 V","240 E3 patch ch-1","240 E4 on ch1","240 E5 off ch1","240 E6 on ch0","240 K","480 V","480 E7 off ch0","480 K","720 V","960 V"};
    check(expected.actions==actions,"Grid first, ordered complete group, one key service");
    for(const std::size_t block:{1,127,4096}) {ScheduleWitness candidate;recording::runSchedule(events,1000,block,candidate);check(candidate.actions==expected.actions,"Actions independent of block boundaries");}
    for(const std::string& line:std::vector<std::string>{"0 on 36 127 0 extra\n","0 on 36 127\n","0 on 35 127 0\n","0 on 36 0 0\n","0 on 36 127 2\n","0 off 36 0 extra\n","1000 off 36 0\n","2 off 36 0\n1 on 36 127 0\n","0 patch A"+std::string(65,'0')+"\n","0 patch 00\n","\n"}) {
        bool rejected=false;try{std::istringstream input(line);(void)recording::readEvents(input,1000);}catch(const std::runtime_error&){rejected=true;}check(rejected,"Malformed synthetic input rejected");
    }
    std::array<std::uint8_t,33> raw{};for(int i=1;i<32;++i)raw[i]=static_cast<std::uint8_t>(i*7);raw[0]=4;
    const auto compiled=working(raw);
    for(int i=0;i<31;++i)check(compiled.bytes[i]==raw[i+1],"Untouched raw working field");
    check(compiled.bytes[31]==0,"Unwritten byte31 explicit padding");
    check(compiled.bytes[23]==raw[24],"Separate factory flag field supplied as raw24");
    // Public setter only: metadata can be checked before audio is authorized.
    auto c=std::make_unique<Consumer>();Commands::Snapshot s;s.controllers.volumeIndex=9;s.front.effects=4;
    check(c->initialize(Commands::Target::PSS780,s,controls(true),48000,Consumer::ReverbPolicy::StoreReverbBitWithoutAudioEffect)==Consumer::Status::Ok,"Synthetic initialization");
    const auto before=c->frontend().snapshot();const auto epoch=c->epochs();captureEpoch(*c);const auto after=c->frontend().snapshot();
    check(before.front.patch.bytes==after.front.patch.bytes && before.front.effects==after.front.effects && before.front.allocator.notes==after.front.allocator.notes && before.front.allocator.ranks==after.front.allocator.ranks && before.front.allocator.held==after.front.allocator.held && before.vibratoDelay==after.vibratoDelay && c->epochs()==epoch,"Epoch adapter preserves frontend/allocation/trace metadata");
}
std::array<std::uint8_t,33> neutralRaw() {
    std::array<std::uint8_t,33> raw{};raw[1]=raw[2]=1;raw[3]=127;raw[4]=20;
    raw[7]=raw[8]=63;raw[13]=raw[14]=8;raw[20]=raw[21]=5;return raw;
}
struct AudioWitness {
    std::unique_ptr<Consumer> consumer=std::make_unique<Consumer>();
    std::vector<float> left,right;
    explicit AudioWitness(std::size_t total):left(total),right(total) {
        Commands::Snapshot s;s.controllers.volumeIndex=9;
        require(consumer->initialize(Commands::Target::PSS780,s,controls(true),48000,Consumer::ReverbPolicy::StoreReverbBitWithoutAudioEffect)==Consumer::Status::Ok,"Audio contract initialization");captureEpoch(*consumer);
    }
    void event(std::size_t,std::size_t,const recording::Event& e){
        auto status=Consumer::Status::Ok;
        if(e.kind=="patch")status=consumer->selectProgram(working(e.raw),static_cast<std::uint8_t>(e.program));
        else if(e.kind=="on")status=consumer->noteOn(e.note,e.velocity);else status=consumer->noteOff(e.note);
        require(status==Consumer::Status::Ok,"Audio contract event");
    }
    void vibrato(std::size_t){require(consumer->serviceVibrato()==Consumer::Status::Ok,"Audio contract vibrato");}
    void keyService(std::size_t){require(consumer->serviceKeyOn()==Consumer::Status::Ok,"Audio contract keyservice");}
    void process(std::size_t frame,std::size_t count){consumer->process(left.data()+frame,right.data()+frame,count);}
};
void audioTests() {
    // Must be called only after a bound root execution receipt through run.py.
    constexpr std::size_t n=12000;const auto raw=neutralRaw();
    AudioWitness command(n);require(command.consumer->selectProgram(working(raw),0)==Consumer::Status::Ok,"Neutral preload");require(command.consumer->noteOn(36)==Consumer::Status::Ok,"Neutral on");require(command.consumer->serviceKeyOn()==Consumer::Status::Ok,"Neutral service");command.process(0,n);
    auto baseline=std::make_unique<press78::Press78Engine>(),zeroEpoch=std::make_unique<press78::Press78Engine>();
    std::vector<float> l(n),r(n),zl(n),zr(n);
    for(auto* engine:{baseline.get(),zeroEpoch.get()}){engine->prepare(48000);engine->setControls(controls(false));engine->setPatch(press78::decodeVoice(raw),false);engine->noteOn(36,127,0);}
    baseline->setChorusTime(-32.0/48000.0);baseline->process(l.data(),r.data(),n);zeroEpoch->process(zl.data(),zr.data(),n);
    check(std::memcmp(l.data(),command.left.data(),n*sizeof(float))==0 && std::memcmp(r.data(),command.right.data(),n*sizeof(float))==0,"Requested initial chorus epoch reaches actual baseline-equivalent audio");
    check(std::memcmp(l.data(),zl.data(),n*sizeof(float))!=0 || std::memcmp(r.data(),zr.data(),n*sizeof(float))!=0,"Zero-epoch negative control differs");
    auto events=syntheticEvents();events[0].raw=raw;events[3].raw=raw;
    AudioWitness a(1000),b(1000),c(1000);recording::runSchedule(events,1000,1,a);recording::runSchedule(events,1000,127,b);recording::runSchedule(events,1000,256,c);
    for(const auto* x:{&b,&c})check(std::memcmp(a.left.data(),x->left.data(),4000)==0 && std::memcmp(a.right.data(),x->right.data(),4000)==0,"Synthetic command audio exact across1/127/256chunks");
}
}
int main(int argc,char** argv) {
    try {
        pureTests();bool audio=false;
        if(argc>1){require(argc==3 && std::string(argv[1])=="--audio-contract" && std::string(argv[2])=="REVIEW_AUTHORIZED","Audio contract requires bound root receipt through run.py");audio=true;audioTests();}
        std::cout<<"{\"passed\":true,\"checks\":"<<checks<<",\"audio_processed\":"<<(audio?"true":"false")<<",\"retained_fixture_replay\":false}\n";
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
