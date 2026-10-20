"""Generate the Rack parameter contract and local development factory patches."""
from pathlib import Path
import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
from modern_bank import load_modern, load_rack_startup, preset_relative_path

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.1.4b1'
PRODUCT='cz.protocodus.Press78'
# Rack startup character: enable the existing physical/effective model paths.
# Slow clock excursion is a conservative scenario, not a recovered PSS-780
# component measurement. Former noise properties are inert compatibility slots.
LEGACY_NOISE={'noiseRms','noiseModel'}
REAL_DEFAULTS={'outputCircuit':1,'noiseModel':0,'noiseRms':0,
               'chorusMode':1,'chorusMix':1,'chorusRateHz':0.9546467517767424,
               'chorusDepthMs':math.hypot(0.0495126833338911,0.4943632948117077),
               'clockOffsetPpm':0,'clockDriftPpm':20,'clockDriftRateHz':.1,
               'lfoRateHz':5.24,'triangleLfo':1,'globalLfo':1,
               'drive':0,'dcBlock':1,'outputLimit':1,'pitchModel':1,'sustainMode':1,
               'bendRange':1,'velocityCurve':1}
FACTORY_CHARACTER=REAL_DEFAULTS


def specs():
    rows=[]
    def add(name,label,lo,hi,default,integer=False,target='controls'):
        rows.append(dict(id=name,label=label,min=lo,max=hi,default=default,
                         integer=integer,target=target))
    fields=[('mul','Ratio',0,15,1),('dt1','Fine detune',-7,7,0),
            ('tl','Attenuation',0,127,0),('wave','Wave',0,3,0),
            ('ar','Attack rate',0,63,63),('d1r','Decay 1 rate',0,63,0),
            ('d1l','Decay 1 level',0,15,0),('d2r','Decay 2 rate',0,63,0),
            ('rr','Release rate',0,15,10),('srr','Sustain release rate',0,15,5),
            ('lksHi','Upper key level',0,15,0),('lksLo','Lower key level',0,15,0),
            ('rks','Key rate scaling',0,3,0),('amEnable','AM enable',0,1,0),
            ('dt2','Coarse detune',0,1,0)]
    for prefix,label in [('mod','Modulator'),('car','Carrier')]:
        for field,caption,lo,hi,default in fields:
            if prefix=='mod' and field=='tl':default=127
            add(prefix+'_'+field,label+' '+caption,lo,hi,default,True,'patch')
    for name,label,lo,hi,default in [
        ('feedback','Feedback',0,7,0),('pms','Pitch modulation',0,7,0),
        ('ams','Amplitude modulation',0,3,0),('vibratoDelay','LFO delay',0,127,0),
        ('vibrato','Vibrato enable',0,1,0),('sustain','Sustain release',0,1,0)]:
        add(name,label,lo,hi,default,True,'patch')
    for name,label,lo,hi,default,integer in [
        ('masterGain','Volume',0,2,.25,False),
        ('masterTuneCents','Tune',-100,100,0,False),
        ('velocitySensitivity','Velocity to level',0,2,1,False),
        ('velocityToModulation','Velocity to FM',0,2,0,False),
        ('modulationAmount','FM amount',0,2,1,False),
        ('polyphony','Voices',1,12,12,True),
        ('lfoRateHz','LFO rate',.05,30,6.1,False),
        ('vibratoDepth','Pitch depth',0,4,1,False),
        ('tremoloDepth','AM depth',0,4,1,False),
        ('lfoDelayScale','LFO delay scale',0,4,1,False),
        ('triangleLfo','Triangle LFO',0,1,0,True),
        ('globalLfo','Global LFO phase',0,1,0,True),
        ('clockOffsetPpm','Clock offset',-5000,5000,0,False),
        ('clockDriftPpm','Clock drift',0,2000,0,False),
        ('clockDriftRateHz','Drift rate',.01,1,.1,False),
        ('toneCutoffHz','Tone cutoff',1000,20000,14000,False),
        ('drive','Drive',0,1,0,False),
        ('chorusMix','Chorus mix',0,1,0,False),
        ('chorusMode','Chorus model',0,1,0,True),
        ('chorusRateHz','Chorus rate',.05,8,.65,False),
        ('chorusDepthMs','Chorus depth',0,8,2,False),
        ('stereoWidth','Stereo width',0,2,1,False),
        ('noiseRms','Noise level',0,.02,0,False),
        ('noiseModel','Noise model',0,1,0,True),
        ('outputCircuit','Output circuit',0,1,1,True),
        ('dcBlock','DC filter',0,1,1,True),
        ('outputLimit','Output protection',0,1,1,True),
        ('bendRange','Pitch bend range',0,24,2,True),
        ('modWheelDepth','Wheel to vibrato',0,4,1,False)]:
        add(name,label,lo,hi,default,integer)
        if name=='chorusMode': rows[-1]['options']=['Studio','Recorded']
        if name=='noiseModel': rows[-1]['options']=['White','Circuit']
        # PSS-780 owner's manual, printed pp.10 and 39: the wheel range is
        # +/-1..12 semitones and ALL RESET sets 1. Older songs keep 2.
        if name=='bendRange': rows[-1]['startup_default']=1
    # Missing properties in pre-b12 songs retain equal-tempered playback.
    # New Init/factory files explicitly select the Original pitch model.
    add('pitchModel','Pitch model',0,1,0,True)
    rows[-1]['options']=['Equal','Original']
    rows[-1]['startup_default']=1
    # Preserve conventional pedal holding for older patches. The current
    # factory bank explicitly chooses the Original release-rate policy.
    add('sustainMode','Original release policy',0,1,0,True)
    rows[-1].update(options=['Legacy','Original'],startup_default=1,hidden=True,
                   description='Compatibility policy: Original pedal selects release rate; Legacy pedal holds notes.')
    # PSS-780 owner's manual, printed p.9: the Portamento effect button and
    # its speed 1 (slow)..5 (fast), default 3. Off, as the button powers up.
    add('portamento','Portamento',0,1,0,True)
    add('portamentoSpeed','Portamento speed',1,5,3,True)
    # Older songs keep the linear velocity law. The current factory bank
    # selects the PSS-780's own Mode 99 velocity table.
    add('velocityCurve','Original velocity curve',0,1,0,True)
    rows[-1].update(options=['Legacy','Original'],startup_default=1,hidden=True,
                   description='Compatibility policy: Original follows the PSS-780 Mode 99 velocity table; Legacy scales level linearly.')
    for row in rows:
        if row['id'] in REAL_DEFAULTS and row['id'] not in ('pitchModel','sustainMode','bendRange','velocityCurve'): row['default']=REAL_DEFAULTS[row['id']]
        if row['id'] in LEGACY_NOISE:
            row.update(hidden=True,deprecated='Inert compatibility property; additive noise has been removed.')
    return rows


def stored(row,value):
    return value-row['min'] if row['integer'] else (value-row['min'])/(row['max']-row['min'])


def decode(raw):
    out={}
    for prefix,k in [('mod',0),('car',1)]:
        dt=raw[1+k]>>4
        values=dict(mul=raw[1+k]&15,dt1=-(dt&7) if dt&8 else dt&7,
            tl=raw[3+k]&127,lksHi=raw[5+k]>>4,lksLo=raw[5+k]&15,
            rks=raw[7+k]>>6,ar=raw[7+k]&63,amEnable=raw[9+k]>>7,
            dt2=(raw[9+k]>>6)&1,d1r=raw[9+k]&63,wave=raw[11+k]>>6,
            d2r=raw[11+k]&63,d1l=raw[13+k]>>4,rr=raw[13+k]&15,srr=raw[20+k]&15)
        out.update({prefix+'_'+name:value for name,value in values.items()})
    out.update(feedback=(raw[15]>>3)&7,pms=(raw[16]>>4)&7,ams=raw[16]&3,
        vibratoDelay=raw[22]&127,vibrato=int(bool(raw[24]&128)),sustain=int(bool(raw[24]&64)))
    return out


def write_patch(path,rows,overrides):
    patch=ET.Element('JukeboxPatch',version='1.0')
    ET.SubElement(patch,'DeviceNameInEnglish').text='Press78'
    properties=ET.SubElement(patch,'Properties',deviceProductID=PRODUCT,deviceVersion=VERSION)
    obj=ET.SubElement(properties,'Object',name='custom_properties')
    for row in rows:
        value=stored(row,overrides.get(row['id'],row['default']))
        ET.SubElement(obj,'Value',property=row['id'],type='number').text=format(value,'.17g')
    ET.indent(patch,space='    ')
    # Recon's SXML reader rejects ElementTree's declaration on line 1.
    # Match the SDK5 example and the host serializer; keep ET escaping the body.
    path.write_bytes(b'<?xml version="1.0"?>\n'+ET.tostring(patch,encoding='utf-8',xml_declaration=False)+b'\n')


def update_info(text,startup):
    # Preserve authored identity/category metadata. Require one plain string
    # assignment per generated field rather than silently creating or guessing it.
    for field,value in [('version_number',VERSION),('default_patch',startup['default_patch'])]:
        assignments=re.findall(rf'^[ \t]*{field}[ \t]*=',text,re.MULTILINE)
        pattern=rf'^([ \t]*{field}[ \t]*=[ \t]*)"[^"\n]*"([ \t]*(?:--[^\n]*)?)$'
        if len(assignments)!=1 or len(re.findall(pattern,text,re.MULTILINE))!=1:
            raise ValueError(f'info.lua must contain exactly one quoted {field} assignment')
        text=re.sub(pattern,lambda match:match[1]+json.dumps(value)+match[2],text,flags=re.MULTILINE)
    return text


def main():
    parser=argparse.ArgumentParser();parser.add_argument('device',type=Path);args=parser.parse_args()
    device=args.device.resolve();device.mkdir(parents=True,exist_ok=True)
    rows=specs()
    modern=load_modern()
    startup=load_rack_startup(modern)
    info_path=device/'info.lua'
    info=update_info(info_path.read_text(),startup)
    (ROOT/'Assets/controls.json').write_text(json.dumps({'product':PRODUCT,'version':VERSION,'startup_profile':{'name':'Real','values':REAL_DEFAULTS},'rack_startup':startup,'controls':rows},indent=2)+'\n')
    info_path.write_text(info)
    lua=['format_version = "4.0"','custom_properties = jbox.property_set{',
         ' document_owner = { properties = {']
    for row in rows:
        step=f'steps = {int(row["max"]-row["min"]+1)}, ' if row['integer'] else ''
        ui='jbox.ui_selector{'+','.join('jbox.ui_text("value '+row['id']+' '+str(i)+'")' for i,_ in enumerate(row['options']))+'}' if row.get('options') else f'jbox.ui_linear{{min={row["min"]}, max={row["max"]}, units={{{{decimals={0 if row["integer"] else 2}}}}}}}'
        lua.append(f'  {row["id"]} = jbox.number{{ {step}default = {stored(row,row["default"]):.17g}, ui_name = jbox.ui_text("{row["id"]}"), ui_type = {ui}, persistence="patch" }},')
    lua+=['  pitchBend = jbox.performance_pitchbend{},','  modWheel = jbox.performance_modwheel{},',
          '  sustainPedal = jbox.performance_sustainpedal{},',' } },',
          ' rtc_owner = { properties = { instance = jbox.native_object{} } },',
          ' rt_owner = { properties = { noteOn = jbox.boolean{default=false, ui_name=jbox.ui_text("property note on"), ui_type=jbox.ui_linear{min=0,max=1,units={{decimals=0}}}} } },','}',
          'audio_outputs = { left=jbox.audio_output{ui_name=jbox.ui_text("audio left")}, right=jbox.audio_output{ui_name=jbox.ui_text("audio right")} }',
          'cv_inputs = { note_cv=jbox.cv_input{ui_name=jbox.ui_text("cv note")}, gate_cv=jbox.cv_input{ui_name=jbox.ui_text("cv gate")}, fm_cv=jbox.cv_input{ui_name=jbox.ui_text("cv fm")}, level_cv=jbox.cv_input{ui_name=jbox.ui_text("cv level")} }',
          'jbox.add_stereo_audio_routing_pair{left="/audio_outputs/left",right="/audio_outputs/right"}',
          'jbox.add_stereo_instrument_routing_hint{left_output="/audio_outputs/left",right_output="/audio_outputs/right"}',
          'jbox.add_stereo_audio_routing_target{signal_type="normal",left="/audio_outputs/left",right="/audio_outputs/right",auto_route_enable=true}',
          'jbox.add_cv_routing_target{signal_type="gate",path="/cv_inputs/gate_cv",auto_route_enable=true}',
          'jbox.add_cv_routing_target{signal_type="pitch",path="/cv_inputs/note_cv",auto_route_enable=true}',
          'remote_implementation_chart = {']
    for row in rows:
        if row.get('hidden'): continue
        lua.append(f' ["/custom_properties/{row["id"]}"] = {{internal_name="{row["label"]}",short_ui_name=jbox.ui_text("short {row["id"]}"),shortest_ui_name=jbox.ui_text("tiny {row["id"]}")}},')
    # Fixed registry: adding or reordering controls must never renumber existing
    # Reason automation lanes. SDK5 reserves 256..10039 for automation-only IDs.
    automation=json.loads((ROOT/'Assets/rack-automation.json').read_text())
    assert automation['product']==PRODUCT
    ids=automation['ids']
    assert set(ids)=={row['id'] for row in rows}
    assert len(set(ids.values()))==len(ids)
    assert ids['masterGain']==7 and ids['toneCutoffHz']==74
    assert all(value in (7,74) or 256<=value<=10039 for value in ids.values())
    lua+=['}','midi_implementation_chart = { midi_cc_chart = {']
    lua += [f' [{value}]="/custom_properties/{name}",' for name,value in ids.items()]
    lua.append('} }')
    output={'masterGain','toneCutoffHz','drive','chorusMix','chorusMode','chorusRateHz','chorusDepthMs','stereoWidth','noiseRms','noiseModel','outputCircuit','dcBlock','outputLimit'}
    performance={'masterTuneCents','velocitySensitivity','velocityToModulation','polyphony','bendRange','modWheelDepth','portamento','portamentoSpeed'}
    groups={'Modulator':[], 'Carrier':[], 'FM and LFO':[], 'Performance':[], 'Output and effects':[], 'Clock':[]}
    for row in rows:
        if row.get('hidden'): continue
        name=row['id']
        group='Modulator' if name.startswith('mod_') else 'Carrier' if name.startswith('car_') else 'Clock' if name.startswith('clock') else 'Output and effects' if name in output else 'Performance' if name in performance else 'FM and LFO'
        groups[group].append(name)
    lua.append('ui_groups = {')
    for group,names in groups.items():
        lua.append(' {ui_name=jbox.ui_text("group '+group+'"),properties={'+','.join('"/custom_properties/'+name+'"' for name in names)+'}},')
    lua.append('}')
    (device/'motherboard_def.lua').write_text('\n'.join(lua)+'\n')
    texts={row['id']:row['label'] for row in rows}
    texts.update({'group '+group:group for group in groups})
    for row in rows:
        texts['short '+row['id']]=row['label'][:8];texts['tiny '+row['id']]=row['label'][:4]
        for i,label in enumerate(row.get('options',[])):texts['value '+row['id']+' '+str(i)]=label
    texts.update({'gesture mod_tl level':'Modulator Level','gesture car_tl level':'Carrier Level','property note on':'Note On'})
    texts.update({'audio left':'Left / Mono','audio right':'Right','cv note':'Note','cv gate':'Gate','cv fm':'FM amount','cv level':'Level'})
    locale=device/'Resources/English';locale.mkdir(parents=True,exist_ok=True)
    (locale/'texts.lua').write_text('format_version = "1.0"\ntexts = {\n'+''.join(f' [{json.dumps(k)}] = {json.dumps(v)},\n' for k,v in texts.items())+'}\n')
    public=device/'Resources/Public';public.mkdir(parents=True,exist_ok=True)
    write_patch(public/'Init.repatch',rows,FACTORY_CHARACTER)
    bank=json.loads((ROOT/'Assets/FactoryBank/press78-factory.json').read_text())
    for voice in bank['voices']:
        write_patch(public/(voice['name'].replace('/','-')+'.repatch'),rows,{**decode(voice['raw_data']),**FACTORY_CHARACTER})
    for voice in modern:
        destination=public/preset_relative_path(voice)
        destination.parent.mkdir(parents=True,exist_ok=True)
        write_patch(destination,rows,voice['parameters'])
    header=['#pragma once','#include <array>','namespace press78rack {',
        'struct Parameter { const char* name; double minimum, maximum, initial; bool stepped; };',
        f'inline constexpr std::array<Parameter,{len(rows)+3}> kParameters{{{{']
    for row in rows:
        header.append(' {'+json.dumps(row['id'])+f', {row["min"]}, {row["max"]}, {stored(row,row["default"]):.17g}, '+str(row['integer']).lower()+'},')
    header+=[' {"pitchBend",0,1,.5,false},',' {"modWheel",0,1,0,false},',' {"sustainPedal",0,1,0,false},','}};',
             'enum ParameterIndex {']
    header+=[' k_'+row['id']+',' for row in rows]
    header+=[' k_pitchBend, k_modWheel, k_sustainPedal, kParameterCount','};','}']
    (device/'Parameters.h').write_text('\n'.join(header)+'\n')
    (device/'ApplyParameters.inc').write_text('\n'.join(
        [f'controls.{row["id"]} = 0; // Inert legacy noise property.'
         if row['id'] in LEGACY_NOISE else
         f'patch.{"modulator" if row["id"].startswith("mod_") else "carrier"}.{row["id"].split("_",1)[1]} = static_cast<{"bool" if row["id"].endswith(("amEnable","dt2")) else "int"}>(physical(k_{row["id"]}));'
         if row['id'].startswith(('mod_','car_')) else
         f'patch.{row["id"]} = static_cast<{"bool" if row["id"] in ("vibrato","sustain") else "int"}>(physical(k_{row["id"]}));'
         if row['target']=='patch' else
         f'controls.{row["id"]} = static_cast<{"bool" if row["id"] in ("triangleLfo","globalLfo","dcBlock","outputLimit","outputCircuit") else "int" if row["id"] in ("polyphony","chorusMode","noiseModel","pitchModel","sustainMode","velocityCurve") else "double"}>(physical(k_{row["id"]}));'
         for row in rows if row['id'] not in ('bendRange','modWheelDepth')])+'\n')
    print(f'Generated {len(rows)} stored properties ({sum(not row.get("hidden",False) for row in rows)} visible controls), 3 performance inputs, Init +100 PSS +{len(modern)} modern patches at {device}; startup: {startup["name"]}')


if __name__=='__main__':main()
