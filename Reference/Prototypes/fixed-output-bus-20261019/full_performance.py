#!/usr/bin/env python3
"""Replay the previously frozen eight48k complete-performances, no timing changes."""
from pathlib import Path
import hashlib,json,subprocess,datetime
P=Path(__file__).resolve().parent;ROOT=P.parents[2];OUT=ROOT/'build/fixed-output-bus-20261019/full-performances'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n')
def run():
    OUT.mkdir(exist_ok=False)
    prior=ROOT/'build/sustain-b13-20261019/no-CC64/design-frozen.json';d=json.loads(prior.read_text());original=Path(d['fixture']['path']);assert sha(original)==d['fixture']['sha256']
    fixture=original.read_text().replace('#include "Press78Engine.h"','#include "FixedOutputBus.h"').replace('press78::Press78Engine','press78::fixed_bus_research::FixedOutputBus')
    assert fixture.count('if(argc!=7)')==1 and fixture.count('press78::Controls c;c.masterGain=1.;')==1
    fixture=fixture.replace('if(argc!=7)','if(argc!=8)').replace('press78::Controls c;c.masterGain=1.;','press78::Controls c;c.pitchModel=1;c.sustainMode=std::stoi(argv[7]);c.midiPitchBend=-1;c.masterGain=1.;')
    source=OUT/'FixedBusSequence.cpp';source.write_text(fixture)
    binding={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prior_design':{'path':str(prior),'sha256':sha(prior)},'runner_sha256':sha(__file__),'fixture_sha256':sha(source),'prototype_source_sha256':{f.name:sha(f) for f in P.glob('*.h')},'engine_source_sha256':{f.name:sha(f) for f in (ROOT/'Source/DSP').iterdir() if f.is_file()},'purpose':'Onlyreplaceengine with48directwrapper; sameevents/controls/pitch/sustain/chorusepoch/32framelatency. Boundbeforecompile/audio.'}
    write(OUT/'bound.json',binding);exe=OUT/'sequence'
    subprocess.run(['c++','-std=c++17','-O2','-I',str(P),'-I',str(ROOT/'Source/DSP'),str(source),str(ROOT/'Source/DSP/Press78Engine.cpp'),'-o',str(exe)],check=True)
    rows=[]
    for m in d['maps']:
        assert sha(m['events']['path'])==m['events']['sha256']
        for name,mode in d['laws'].items():
            wav=OUT/f"{m['id']}-{name}.wav";pressure=wav.with_suffix('.csv')
            cmd=[str(exe),m['events']['path'],str(wav),str(d['render']['frames']),'48000','recorded',str(pressure),str(mode)]
            info=json.loads(subprocess.run(cmd,check=True,text=True,capture_output=True).stdout)
            actual=sha(wav);passed=actual==m['expected_legacy_audio']['sha256'];rows.append({'map':m['id'],'sustain_mode':mode,'info':info,'WAV_sha256':actual,'expected_sha256':m['expected_legacy_audio']['sha256'],'passed':passed,'new_duplicate_deleted':passed})
            if passed:wav.unlink()
            write(OUT/'progress.json',rows);print(m['id'],name,passed,flush=True)
    assert binding['prototype_source_sha256']=={f.name:sha(f) for f in P.glob('*.h')}
    write(OUT/'result.json',{'passed':all(r['passed'] for r in rows) and len(rows)==8,'rows':rows,'binding_sha256':sha(OUT/'bound.json'),'scope':'Exactcompatibility at48k; no newhardware score or envelope/audio fit.'})
if __name__=='__main__':run()
