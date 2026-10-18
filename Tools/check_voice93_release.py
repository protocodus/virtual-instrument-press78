#!/usr/bin/env python3
"""Focused Human Voice1 release diagnosis; external local recording required.

No core, preset, timing, pitch or release parameter is fitted or changed.
RR6/RR5 are explanatory local copies. Auditions share ONE baseline-derived
gain, preserving differences in tail energy. Artifacts must be local/ignored.
"""
from pathlib import Path
import argparse, hashlib, html, json, shutil, subprocess, sys, tempfile
import numpy as np
from scipy import signal
from scipy.io import wavfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];SR=48000
START=163.75;END=168.5
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
rms=lambda x:float(np.sqrt(np.mean(np.asarray(x,dtype=float)**2)))


def savejson(path,data):
    Path(path).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def line_amplitude(stereo,frequency):
    """Centered80ms Hann lock-in amplitude; explicitly has±40ms time support."""
    n=round(.08*SR)+1;window=signal.windows.hann(n);window/=window.sum()
    carrier=np.exp(-2j*np.pi*frequency*np.arange(len(stereo))/SR)
    z=signal.fftconvolve(stereo*carrier[:,None],window[:,None],mode='same',axes=0)*2
    return {'power_mean':np.sqrt(np.mean(abs(z)**2,axis=1)),
            'mid':abs(z.mean(axis=1)),'left':abs(z[:,0]),'right':abs(z[:,1])}


def synth_isolated(note,patch,start,end,python_root):
    """Same behavioral FM, exact48k host MNA and frozen causal stereo law."""
    sys.path[:0]=[str(python_root),str(python_root/'src')]
    from pss780 import render_note
    from circuit.model import build_circuit
    from circuit.calibrated_chorus import process_calibrated_chorus
    first=round(start*SR);length=round((end-start)*SR)
    x=np.zeros(length);on=note['on_frame']-first
    y=render_note(patch,note['midi'],note['velocity'],(length-on)/SR,(note['off_frame']-note['on_frame'])/SR,SR)
    x[on:on+len(y)]=y
    circuit,output=build_circuit(model='pss480');x=circuit.process(x,SR,output)
    return process_calibrated_chorus(x,SR,start_seconds=start)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-root',type=Path,required=True)
    parser.add_argument('--benchmark-dir',type=Path,required=True)
    parser.add_argument('--artifact-dir',type=Path,required=True)
    args=parser.parse_args();refroot=args.reference_root.resolve();bench=args.benchmark_dir.resolve();out=args.artifact_dir.resolve()
    if (out/'report.json').exists():parser.error('Choose a new artifact directory; completed diagnoses are preserved')
    if out.is_relative_to(ROOT) and subprocess.run(['git','check-ignore','--quiet',str(out)],cwd=ROOT).returncode:parser.error('Audio artifacts in repository must be ignored')
    out.mkdir(parents=True,exist_ok=True);(out/'audio').mkdir(exist_ok=True)
    shutil.copy2(Path(__file__),out/Path(__file__).name)
    benchmark=read(bench/'report.json');alignment=read(refroot/'references/v2/alignment.json')
    timeline=read(refroot/'references/v3_program_timeline.json')['intervals'];program=timeline[93];next_program=timeline[94]
    native_path=Path(benchmark['native_renders']['recorded']['file'])
    assert sha(native_path)==benchmark['native_renders']['recorded']['sha256']
    _,native=wavfile.read(native_path,mmap=True);latency=benchmark['native_renders']['recorded']['latency_samples']
    original_path=refroot/'references/v2/user-ONfIvtDOog0.wav';sr,original=wavfile.read(original_path,mmap=True);assert sr==SR
    a,z=round(START*SR),round(END*SR);reference=original[a:z].astype(float)/32768;baseline=native[a+latency:z+latency].astype(float)
    notes=[]
    for n in read(refroot/'references/v2/eugenia-events.json')['notes']:
        start=alignment['offset_seconds']+alignment['scale']*n['start'];gate=alignment['scale']*n['gate'];on=round(start*SR);off=on+round(gate*SR)
        if START-1<start<END:
            notes.append({**n,'audio_start':start,'audio_off':off/SR,'on_frame':on,'off_frame':off,
                          'patch':max((p['patch'] for p in timeline if round(p['audio_start_seconds']*SR)<=on),default=0)})
    target_notes=[n for n in notes if n['patch']==93 and n['channel']==0]
    protocol={'scope':'Previously observed polyphonic recording; descriptive release check, no hardware RR fit',
        'context_seconds':[START,END],'old_AB_seconds':[165.5,166.66666666666666],
        'primary_note':74,'other_checked_notes':[82,77,80],
        'line_frequency':'MIDI equal temperament440Hz times carrier ratio2, fixed; no peak search',
        'analysis_window':'Centered80ms Hann complex demodulator, ±40ms support; not a sample-exact gate detector',
        'primary_tail_seconds_after_gate':[.15,.22],'secondary_tail_seconds_after_gate':[.22,.35],
        'pre_gate_level_seconds':[-.08,-.02],'gate_uncertainty_seconds':[-.05,0,.05],
        'contamination_test':'Subtract isolated behavioral target-note stereo from complete native baseline; this is model-only evidence, not recovered recorded stems',
        'audition_gain':'One stereo RMS gain computed from baseline/reference whole context; reused for RR6/RR5. One safety gain for every file.',
        'candidate_changes':'Only patch93 carrierRR low nibble7→6 or5; all other raw bytes, all other programs and all note events fixed',
        'timeline':{'program93':program,'program94':next_program},'target_notes':target_notes,
        'source_sha256':{'recording':sha(original_path),'native_baseline':sha(native_path),'events':sha(bench/'events.txt'),
            'benchmark_report':sha(bench/'report.json'),'script':sha(Path(__file__))}}
    savejson(out/'protocol.json',protocol)
    sys.path[:0]=[str(ROOT/'Tools/reference/src'),str(ROOT/'Tools/reference')]
    from pss780 import get_patch
    patch=get_patch(93)
    gain=rms(reference)/rms(baseline)
    candidates={'baseline_RR7':baseline};render_info={}
    # Frozen engine/fixture, only local raw program bytes differ.
    fixture=bench/'HardwareSequence.cpp';source=bench/'source';events=(bench/'events.txt').read_text().splitlines()
    raw=bytes(patch['raw_data']).hex();program_frame=round(program['audio_start_seconds']*SR)
    with tempfile.TemporaryDirectory(prefix='release-render-',dir=out) as directory:
        temp=Path(directory);executable=temp/'sequence'
        subprocess.run(['c++','-std=c++17','-O2','-I',str(source),str(fixture),str(source/'Press78Engine.cpp'),'-o',str(executable)],check=True,capture_output=True)
        frames=z+4096
        for rr in (6,5):
            data=list(patch['raw_data']);data[14]=(data[14]&240)|rr
            lines=[line for line in events if int(line.split()[0])<frames]
            needle=f'{program_frame} patch {raw}';assert lines.count(needle)==1
            lines=[f'{program_frame} patch {bytes(data).hex()}' if line==needle else line for line in lines]
            eventfile=out/f'RR{rr}-events.txt';eventfile.write_text('\n'.join(lines)+'\n')
            output=temp/'render.wav';result=subprocess.run([str(executable),str(eventfile),str(output),str(frames),str(SR),'recorded'],check=True,capture_output=True,text=True)
            detail=json.loads(result.stdout);_,y=wavfile.read(output,mmap=True)
            candidates[f'carrier_RR{rr}']=y[a+latency:z+latency].astype(float).copy();output.unlink()
            render_info[str(rr)]={'renderer':detail,'events_sha256':sha(eventfile),'only_changed_raw_index':14,'old_byte':patch['raw_data'][14],'new_byte':data[14]}
    times=START+np.arange(len(reference))/SR;traces={};results=[]
    for n in target_notes:
        frequency=440*2**((n['midi']-69)/12)*2
        isolated=synth_isolated(n,patch,START,END,ROOT/'Tools/reference');other=baseline-isolated
        waves={'reference':reference,'baseline_RR7':baseline*gain,'carrier_RR6':candidates['carrier_RR6']*gain,'carrier_RR5':candidates['carrier_RR5']*gain,
               'isolated_note_model':isolated*gain,'other_notes_model':other*gain}
        envelopes={key:line_amplitude(y,frequency) for key,y in waves.items()}
        quiet=[]
        for begin,end in ((.05,.55),(184.5,185.5)):
            x=original[round(begin*SR):round(end*SR)].astype(float)/32768
            quiet.append(rms(line_amplitude(x,frequency)['power_mean'][round(.08*SR):-round(.08*SR)]))
        noise=max(quiet)
        def level(env,t0,t1):return rms(env[(times>=t0)&(times<t1)])
        off=n['audio_off'];pre=(off-.08,off-.02);windows=[]
        for shift in (-.05,0,.05):
            for lo,hi in ((.15,.22),(.22,.35)):
                begin,end=off+shift+lo,off+shift+hi
                values={}
                for key,env in envelopes.items():
                    before=level(env['power_mean'],*pre);tail=level(env['power_mean'],begin,end)
                    values[key]={'tail_amplitude':tail,'tail_db_relative_own_pre':20*np.log10(max(tail,1e-30)/max(before,1e-30)),
                                 'left_tail_amplitude':level(env['left'],begin,end),'right_tail_amplitude':level(env['right'],begin,end),
                                 'mid_tail_amplitude':level(env['mid'],begin,end)}
                windows.append({'gate_shift_seconds':shift,'post_gate_interval':[lo,hi],'absolute_interval':[begin,end],
                    'levels':values,'reference_above_quiet_db':20*np.log10(max(values['reference']['tail_amplitude'],1e-30)/noise),
                    'reference_over_baseline_db':20*np.log10(max(values['reference']['tail_amplitude'],1e-30)/max(values['baseline_RR7']['tail_amplitude'],1e-30)),
                    'other_model_relative_reference_db':20*np.log10(max(values['other_notes_model']['tail_amplitude'],1e-30)/max(values['reference']['tail_amplitude'],1e-30))})
        results.append({'midi':n['midi'],'on_seconds':n['audio_start'],'off_seconds':off,'carrier_hz':frequency,'quiet_line_amplitude':noise,'windows':windows})
        traces[n['midi']]={key:env['power_mean'] for key,env in envelopes.items()}
    all_audio={'reference':reference,**{key:y*gain for key,y in candidates.items()}}
    safety=min(1.,.85/max(np.max(abs(y)) for y in all_audio.values()));auditions={}
    for name,(begin,end) in {'long_context':(START,END),'focused_noteoffs':(165.85,166.95)}.items():
        lo,hi=round((begin-START)*SR),round((end-START)*SR);files={}
        for key,y in all_audio.items():
            path=out/'audio'/f'{name}-{key}.wav';wavfile.write(path,SR,(y[lo:hi]*safety).astype(np.float32));files[key]=str(path)
        combined=out/'audio'/f'{name}-comparison.wav';wavfile.write(combined,SR,np.concatenate([part for y in all_audio.values() for part in(y[lo:hi]*safety,np.zeros((round(.5*SR),2)))]).astype(np.float32))
        auditions[name]={'start_seconds':begin,'end_seconds':end,'files':files,'order':list(all_audio),'combined':str(combined)}
    fig,axes=plt.subplots(3,1,figsize=(13,10),constrained_layout=True)
    for ax,midi in zip(axes,(82,74,77)):
        n=next(x for x in target_notes if x['midi']==midi);off=n['audio_off'];pre=(times>=off-.08)&(times<off-.02);normal=rms(traces[midi]['reference'][pre])
        mask=(times>=off-.15)&(times<=off+.55)
        for key,color in [('reference','#151515'),('baseline_RR7','#bd6030'),('carrier_RR6','#00887b'),('carrier_RR5','#7054af'),('other_notes_model','#aaa')]:
            ax.plot((times[mask]-off)[::24],20*np.log10(np.maximum(traces[midi][key][mask][::24]/normal,1e-6)),label=key,color=color,lw=1.4)
        ax.axvline(0,color='black',ls='--',lw=.8);ax.axvspan(-.05,.05,color='grey',alpha=.15,label='±50ms gate uncertainty')
        ax.axvspan(.15,.22,color='green',alpha=.08);ax.axvspan(.22,.35,color='blue',alpha=.05)
        for note in notes:
            if off<note['audio_start']<off+.55:ax.axvline(note['audio_start']-off,color='#999',ls=':',lw=.5)
        ax.set(title=f'MIDI{midi} · fixed carrier{440*2**((midi-69)/12)*2:.2f}Hz · gate{off:.6f}s',xlabel='Seconds relative to inferred MIDI note-off',ylabel='Line amplitude, dB\nrelative to reference pre-off',ylim=(-80,8));ax.grid(alpha=.15)
    axes[0].legend(ncol=3,fontsize=8);fig.suptitle('Human Voice1 release: fixed80ms analysis window, no local alignment or gain fit',fontsize=14)
    fig.savefig(out/'release-partials.png',dpi=160);plt.close(fig)
    report={'scope':protocol['scope'],'protocol':protocol,'baseline_to_reference_gain':gain,'common_safety_gain':safety,
        'carrier_release_model':{'RR7_t60_seconds':.16572815184059708,'RR6_t60_seconds':.33145630368119416,'RR5_t60_seconds':.6629126073623883,
            'sustain':False,'modulator_RR':3,'only_carrier_RR_varied':True},'measurements':results,'auditions':auditions,'candidate_renders':render_info,
        'limitations':['All data previously observed; no exact hardware RR estimation or production change.',
            'The recording has reverb, chorus and vibrato on. These are not isolated dry notes.',
            'MIDI82 shares harmonic families with new46/58 at its gate; MIDI77 shares them with new41/53.',
            'MIDI74 is the primary less-confounded observable, but later partials, unknown effects and capture still matter.',
            '80ms Hann analysis smears by±40ms; source global timing has local uncertainty around50ms.',
            'Model-only stem subtraction does not prove corresponding hardware source separation.',
            'The old1.1667s comparison cuts before the93→94 transition; this new audition includes the transitions and later tails.',
            'Factory SysEx does not encode the global reverb state; a missing effect and a wrong raw release law cannot be separated definitively here.'],
        'source_sha256':{str(p):sha(p) for p in [fixture,*source.glob('*.h'),source/'Press78Engine.cpp',ROOT/'Tools/reference/src/pss780.py',ROOT/'Tools/reference/circuit/model.py',ROOT/'Tools/reference/circuit/calibrated_chorus.py']},
        'audio_sha256':{str(p):sha(p) for p in (out/'audio').glob('*.wav')}}
    savejson(out/'report.json',report)
    print(json.dumps({'artifact_dir':str(out),'primary_MIDI74':[w for row in results if row['midi']==74 for w in row['windows'] if w['gate_shift_seconds']==0]},indent=2))


if __name__=='__main__':main()
