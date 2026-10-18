"""Compare the new default/Studio path with an explicitly frozen old source."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DRIVER = r'''
#include "Press78Engine.h"
#include "FactoryVoices.h"
#include <array>
#include <cstdio>
#include <memory>
int main() {
    for(double sr : {44100.0,48000.0,96000.0}) {
        auto e=std::make_unique<press78::Press78Engine>();
        for(int p=0;p<100;++p) {
            e->prepare(sr);
            press78::Controls c;
            if(p%3) {c.chorusMix=.8;c.chorusRateHz=.97;c.chorusDepthMs=3;c.stereoWidth=1.7;
                c.drive=.07;c.noiseRms=.001;c.clockOffsetPpm=5000;c.clockDriftPpm=1200;}
            e->setControls(c);e->setPatch(press78::decodeVoice(press78::kFactoryVoices[p].bytes));
            for(int n:{48,60,67,72})e->noteOn(n,101);
            std::array<float,2048> l{},r{};
            e->process(l.data(),r.data(),1024);e->noteOff(60);e->noteOn(53,127);
            c.chorusMix=.4;c.masterGain=.3;e->setControls(c);
            e->process(l.data()+1024,r.data()+1024,1024);
            std::fwrite(l.data(),sizeof(float),l.size(),stdout);
            std::fwrite(r.data(),sizeof(float),r.size(),stdout);
        }
    }
}
'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline',type=Path,required=True)
    args=parser.parse_args()
    sources={'baseline':args.baseline.resolve(),'current':ROOT/'Source/DSP'}
    outputs={}
    with tempfile.TemporaryDirectory(prefix='press78-studio-') as temp:
        tmp=Path(temp);(tmp/'driver.cpp').write_text(DRIVER)
        for name,src in sources.items():
            subprocess.run(['clang++','-std=c++17','-O2','-I'+str(src),str(tmp/'driver.cpp'),
                            str(src/'Press78Engine.cpp'),'-o',str(tmp/name)],check=True)
            outputs[name]=subprocess.run([str(tmp/name)],check=True,capture_output=True).stdout
    assert outputs['baseline']==outputs['current'],'Studio compatibility regression'
    result={'passed':True,'scope':'Byte-identical Studio/default output vs explicit archived native source;300 preset/rate/chord/control cases, not hardware verification.',
            'cases':300,'sample_rates':[44100,48000,96000],'frames_per_case':2048,
            'output_sha256':hashlib.sha256(outputs['current']).hexdigest(),
            'source_sha256':{name:{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(src.glob('*.h'))+list(src.glob('*.cpp'))}
                             for name,src in sources.items()},
            'fixture_sha256':hashlib.sha256(DRIVER.encode()).hexdigest(),
            'baseline_directory':str(sources['baseline'])}
    (ROOT/'Tests/results/studio-compatibility.json').write_text(json.dumps(result,indent=2)+'\n')
    print('300 Studio/default cases byte-identical to frozen native baseline')


if __name__=='__main__':main()
