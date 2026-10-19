#!/usr/bin/env python3
"""Freeze fixtures, build and compare complete OPU plans; never render audio.

The old allocation/release traces are explicitly posthoc development material.
Prospective original-CPU observations are collected once by collect_controls.py.
All native/expected/raw logs remain ignored; public receipts contain only hashes,
counts, scope and outcomes. Refuse overwrites, including failed-run artifacts.
"""
from pathlib import Path
import collections
import gzip
import hashlib
import json
import os
import subprocess
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
OLD=Path('/Users/vojta/Dev/virtual-instrument-press78')


def binding(path):
    p=Path(path);b=p.read_bytes()
    return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}


def held(ram):
    return [n for n in range(36,97) if ram[0x24bf+10-(n-31)//6] & (32>>((n-31)%6))]


def state(ram,keyed):
    return dict(ranks=list(ram[0x207e:0x208a]),notes=list(ram[0x2120:0x212c]),
        pending=list(ram[0x2194:0x21a0]),keyed=keyed.copy(),cached=list(ram[0x24a6:0x24b2]),
        delay=list(ram[0x248e:0x249a]),byte21=list(ram[0x2476:0x2482]),
        byte15=list(ram[0x246a:0x2476]),byte22=list(ram[0x2482:0x248e]),
        held=held(ram),program=ram[0x2585],effects=ram[0x2588])


def initial_line(model,ram,keyed,controllers):
    s=state(ram,keyed)
    values=[int(model[-3:]),s['program'],s['effects'],controllers['volume'],controllers['bend_high'],
            controllers['span'],controllers['fine'],*ram[0x2659:0x2679],*s['ranks'],*s['notes'],
            *s['pending'],*s['keyed'],*s['delay'],len(s['held']),*s['held']]
    return 'init '+' '.join(map(str,values))


def opu(trace):
    return [[w['address'],w['value']] for w in trace if 0x200<=w['address']<0x300]


def keys_apply(keyed,trace):
    for w in trace:
        if w['address']==0x208 and (w['value']&7)<6:
            pair=w['value']&7
            keyed[2*pair]=int(bool(w['value']&24));keyed[2*pair+1]=int(bool(w['value']&96))


def fixtures(prospective):
    lines=[];expected=[];stats=collections.Counter();templates={}
    neutral=dict(volume=0,bend_high=64,span=2,fine=0)
    excluded=collections.Counter()
    def add(command,wanted,label):
        lines.append(command);expected.append(dict(label=label,fields=dict(kind=command.split()[0],status=0,allocations=0,**wanted)))
    def count_excluded(group,trace):
        for w in trace:
            if not 0x200<=w['address']<0x300:excluded[(group,w['address'])]+=1
    def changes(ram,changes):
        for address,previous,value in changes:
            assert ram[address]==previous,('RAM previous value',address,ram[address],previous)
            ram[address]=value;stats['previous_ram_checks']+=1
    source=OLD/'build/opu-allocation-command-path-20261019/observation.jsonl.gz'
    with gzip.open(source,'rt') as f:
        for raw in f:
            row=json.loads(raw)
            if row['mode']!=0:continue
            label={k:row[k] for k in ['model','panel_program','scenario']};label['family']='posthoc-allocation'
            if row['record']=='initial':
                ram=bytearray(16384);ram[0x2000:0x26a0]=bytes(row['ram']);keyed=[0]*12
                keys_apply(keyed,row['initialization_io'])
                templates.setdefault((row['model'],row['panel_program']),(ram.copy(),keyed.copy()))
                add(initial_line(row['model'],ram,keyed,neutral),state(ram,keyed),label)
                stats['posthoc_allocation_cases']+=1
            elif row['record']=='event':
                changes(ram,row['ram_changes']);keys_apply(keyed,row['io'])
                ev=row['event'];kind=ev['kind']
                command=f"key {ev['count']}" if kind=='service' else (f"on {ev['note']} 127" if kind=='on' else f"off {ev['note']}")
                words=opu(row['io']);add(command,dict(writes=words,**state(ram,keyed)),dict(label,index=row['index']))
                stats['posthoc_allocation_events']+=1;stats['posthoc_allocation_words']+=len(words)
                count_excluded('posthoc-allocation',row['io'])
    assert stats['posthoc_allocation_events']==10872 and stats['posthoc_allocation_words']==37944
    # Complete original release word lists cover all effect masks. Their fixture
    # does not retain full post-event RAM, so claim word conformance, not new
    # raw-state validation, for this particular family.
    release=json.loads((OLD/'build/opu-release-command-path-20261019/release-validation.json').read_text())
    for row in release['cases']:
        if row['mode']!=0:continue
        ram,keyed=templates[(row['model'],row['panel_program'])]
        ram=ram.copy();keyed=keyed.copy();ram[0x2588]=row['effect_mask']
        label=dict(family='retained-release',model=row['model'],panel=row['panel_program'],note=row['note'],effects=row['effect_mask'])
        add(initial_line(row['model'],ram,keyed,neutral),{},label)
        for command,field in [(f"on {row['note']} 127",'noteon'),('key 1','keyon_service'),
                              ('mixed 4','hold_service'),(f"off {row['note']}",'noteoff'),('mixed 32','postoff_service_32')]:
            words=opu(row[field]);add(command,dict(writes=words),dict(label,operation=field))
            stats['retained_release_events']+=1;stats['retained_release_words']+=len(words)
            count_excluded('retained-release',row[field])
        stats['retained_release_cases']+=1
    with gzip.open(prospective/'prospective-observations.jsonl.gz','rt') as f:
        for index,raw in enumerate(f):
            row=json.loads(raw);assert 'error' not in row,row
            ram=bytearray(16384);ram[0x2000:0x26a0]=bytes(row['initial_ram']);keyed=[0]*12
            family='prospective-composition' if row['delay_edit'] is None else 'prospective-delay'
            label=dict(family=family,index=index,model=row['model'],panel=row['panel'],note=row['note'],effects=row['fx'])
            assert state(ram,keyed)==row['initial_state']
            add(initial_line(row['model'],ram,keyed,row['controllers']),state(ram,keyed),label)
            for ix,event in enumerate(row['events']):
                changes(ram,event['ram_changes']);keys_apply(keyed,event['io'])
                assert state(ram,keyed)==event['state'],('collector state reconstruction',label,ix)
                words=opu(event['io']);add(event['command'],dict(writes=words,**state(ram,keyed)),dict(label,event_index=ix))
                stats[family+'_events']+=1;stats[family+'_words']+=len(words)
                count_excluded(family,event['io'])
            stats[family+'_cases']+=1
    return lines,expected,dict(stats),[dict(family=k[0],address=hex(k[1]),writes=v) for k,v in sorted(excluded.items())]


def main():
    target=Path(sys.argv[1]);prospective=Path(sys.argv[2])
    if target.exists():raise SystemExit('Refuse overwrite validation directory')
    target.mkdir(parents=True)
    design=json.loads((HERE/'design-frozen.json').read_text())
    for item in design['inputs']:assert binding(item['path'])==item,item['path']
    lines,wanted,stats,excluded=fixtures(prospective)
    (target/'fixture.txt').write_text('\n'.join(lines)+'\n')
    (target/'expected.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in wanted))
    receipt={'passed':True,'design':binding(HERE/'design-frozen.json'),'stats':stats,'excluded_peripheral_io':excluded,
             'fixture':binding(target/'fixture.txt'),'expected':binding(target/'expected.jsonl'),
             'prospective_observations':binding(prospective/'prospective-observations.jsonl.gz'),
             'source_files':{p.name:binding(p) for p in HERE.iterdir() if p.suffix in ['.cpp','.h','.py']},'builds':[]}
    for label,flags in [('optimized',['-O2']),('sanitized',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
        build=target/label;build.mkdir(); entry=dict(label=label,commands=[],passed=True)
        for name in ['CommandProbe','SyntheticTests']:
            command=['clang++','-std=c++17','-Wall','-Wextra','-Wpedantic','-Werror',*flags,str(HERE/(name+'.cpp')),'-o',str(build/name)]
            compiled=subprocess.run(command,capture_output=True,text=True)
            (build/(name+'-compile.stdout')).write_text(compiled.stdout);(build/(name+'-compile.stderr')).write_text(compiled.stderr)
            entry['commands'].append(dict(command=command,exit_code=compiled.returncode))
            if compiled.returncode:
                entry['passed']=False;receipt['passed']=False
                receipt['builds'].append(entry);(target/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
                raise SystemExit('Compilation failed; receipts retained')
        env=dict(os.environ,ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        executed=subprocess.run([str(build/'CommandProbe')],input='\n'.join(lines)+'\n',capture_output=True,text=True,env=env)
        (build/'probe.stdout.jsonl').write_text(executed.stdout);(build/'probe.stderr').write_text(executed.stderr)
        actual=[json.loads(line) for line in executed.stdout.splitlines()]
        errors=[];fields=0;words=0
        if len(actual)!=len(wanted):errors.append(dict(issue='row count',actual=len(actual),expected=len(wanted)))
        for i,(a,w) in enumerate(zip(actual,wanted)):
            for key,value in w['fields'].items():
                fields+=1
                if a.get(key)!=value:errors.append(dict(row=i,label=w['label'],field=key,actual=a.get(key),expected=value))
            words+=len(w['fields'].get('writes',[]))
        (build/'errors.json').write_text(json.dumps(errors,indent=2)+'\n')
        synth=subprocess.run([str(build/'SyntheticTests')],capture_output=True,text=True,env=env)
        (build/'synthetic.stdout').write_text(synth.stdout);(build/'synthetic.stderr').write_text(synth.stderr)
        entry.update(rows=len(actual),expected_rows=len(wanted),exact_fields=fields,complete_opu_words=words,
            probe_exit_code=executed.returncode,synthetic_exit_code=synth.returncode,errors=len(errors),
            synthetic=json.loads(synth.stdout) if synth.returncode==0 else None,
            probe_stdout=binding(build/'probe.stdout.jsonl'),probe_stderr=binding(build/'probe.stderr'),
            errors_file=binding(build/'errors.json'),synthetic_stdout=binding(build/'synthetic.stdout'),
            synthetic_stderr=binding(build/'synthetic.stderr'),probe_binary=binding(build/'CommandProbe'),synthetic_binary=binding(build/'SyntheticTests'))
        entry['passed']=not errors and executed.returncode==0 and synth.returncode==0
        receipt['passed'] &= entry['passed'];receipt['builds'].append(entry)
        (target/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps({k:v for k,v in entry.items() if k in ['label','passed','rows','exact_fields','complete_opu_words','errors','synthetic']}),flush=True)
    receipt['optimized_sanitized_stdout_identical']=(target/'optimized/probe.stdout.jsonl').read_bytes()==(target/'sanitized/probe.stdout.jsonl').read_bytes()
    receipt['passed'] &= receipt['optimized_sanitized_stdout_identical']
    (target/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if not receipt['passed']:raise SystemExit('Conformance failure retained; no promotion')


if __name__=='__main__':main()
