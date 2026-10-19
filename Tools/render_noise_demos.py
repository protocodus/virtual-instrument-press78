"""Synthetic matched-note/noise auditions; no claim of hardware measurement."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

import numpy as np
from scipy.io import wavfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--renderer',type=Path,default=ROOT/'build/press78_render')
    parser.add_argument('--out',type=Path,default=ROOT/'build/noise-demos')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    bank=json.loads((ROOT/'Assets/FactoryBank/press78-factory.json').read_text())['voices']
    rows=[]
    for number in (65,93,97):
        voice=bank[number];raw=bytes(voice['raw_data']).hex()
        for noise in (0,.002):
            filename=f'{number:02d}-'+('no-added-noise' if noise==0 else 'circuit-noise')+'.wav'
            path=args.out/filename
            command=[str(args.renderer.resolve()),'--output',str(path),'--raw',raw,'--rate','48000',
                     '--note','60','--velocity','100','--gate','3','--seconds','6',
                     '--noise-model','1','--noise',str(noise)]
            result=subprocess.run(command,check=True,text=True,capture_output=True)
            rows.append({'file':filename,'voice':voice['name'],'midi':60,'velocity':100,
                         'noise_model':'Circuit','noise_reference_level':noise,'master_gain':.25,
                         'chorus_mix':0,'metrics':json.loads(result.stdout)})
    solo=args.out/'solo-circuit-noise-quiet.wav'
    command=[str(args.renderer.resolve()),'--output',str(solo),'--rate','48000','--velocity','0',
             '--seconds','6','--noise-model','1','--noise','.002']
    subprocess.run(command,check=True,capture_output=True)
    sr,x=wavfile.read(solo);boosted=x*10
    assert np.isfinite(boosted).all() and np.max(abs(boosted))<1
    loud=args.out/'solo-circuit-noise-plus20dB.wav';wavfile.write(loud,sr,boosted.astype(np.float32))
    rows += [{'file':solo.name,'kind':'Noise only; native level .002 before master .25',
              'rms':np.sqrt(np.mean(x.astype(float)**2,axis=0)).tolist()},
             {'file':loud.name,'kind':'Same solo noise waveform with fixed20dB audition gain; no normalization',
              'rms':np.sqrt(np.mean(boosted.astype(float)**2,axis=0)).tolist()}]
    for row in rows:row['sha256']=hashlib.sha256((args.out/row['file']).read_bytes()).hexdigest()
    report={'scope':'Synthetic native model auditions, not real-recording comparisons or recovered PSS780 noise.',
            'normalization':'No file normalization. noiseRms sets gain relative to one fixed continuous20-20kHz circuit RMS; only named boosted file applies fixed20dB audition gain.',
            'signal_path':'Default related PSS480 output filter and tone; no chorus; fixed .25 master gain; circuit noise inserted after chorus before DC/master.',
            'rows':rows,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [Path(__file__),ROOT/'Tools/NativeRender.cpp',*sorted((ROOT/'Source/DSP').glob('*.h')),*sorted((ROOT/'Source/DSP').glob('*.cpp'))]}}
    (args.out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'{len(rows)} synthetic audition WAVs written to {args.out}')


if __name__=='__main__':main()
