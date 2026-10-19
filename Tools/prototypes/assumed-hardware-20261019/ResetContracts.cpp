// Supplementary post-excitation reset check; emits no PCM and writes no WAV.
// Compile once per already generated native scenario, no new model or fitting.
#define main assumedAuditionRendererMain
#include PRESS78_GENERATED_SOURCE
#undef main

int main() {
    try {
        press78::Controls c;c.masterGain=.4;c.pitchModel=1;c.sustainMode=1;
        c.chorusMode=1;c.chorusMix=1;c.drive=.3;c.clockOffsetPpm=37;c.clockDriftPpm=20;
        auto patch=press78::factoryPatch(93);patch.sustain=false;
        press78::Press78Engine dirty,fresh;
        for(auto* e:{&dirty,&fresh}) {e->prepare(48000);e->setControls(c);e->setPatch(patch);e->reset();}
        dirty.noteOn(36,127);dirty.noteOn(60,95);dirty.sustainController(127);
        std::array<float,64> a{},b{},x{},y{};
        for(int i=0;i<128;++i)dirty.process(a.data(),b.data(),64);
        dirty.noteOff(36);dirty.noteOff(60);
        for(int i=0;i<128;++i)dirty.process(a.data(),b.data(),64);
        require(dirty.activeVoices()>0,"Post-excitation reset fixture already idle");
        dirty.reset();fresh.reset();
        require(dirty.activeVoices()==0,"Reset retained voices");
        for(int i=0;i<16;++i) {
            dirty.process(a.data(),b.data(),64);fresh.process(x.data(),y.data(),64);
            require(a==x&&b==y,"Post-excitation reset silent history differs");
            for(int j=0;j<64;++j)require(a[j]==0&&b[j]==0,"Post-excitation reset not silent");
        }
        dirty.noteOn(48,110);fresh.noteOn(48,110);
        for(int i=0;i<2048;++i) {
            if(i==512) {dirty.noteOff(48);fresh.noteOff(48);}
            dirty.process(a.data(),b.data(),64);fresh.process(x.data(),y.data(),64);
            require(a==x&&b==y,"Post-excitation reset audio differs from fresh");
        }
        std::cout<<"{\"post_excitation_reset_matches_fresh\":true,\"reset_silence_frames\":1024,\"comparison_frames\":131072}\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
