"""Generate the review wireframe and its single geometry/control source."""
from pathlib import Path
import json, math, html, hashlib, base64, io
from PIL import Image, ImageFont
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Design'; W,H=754,552
C={'bg':'#303238','panel':'#25282d','edge':'#4a4e55','ink':'#e9e4d2','muted':'#b9bbb8','cyan':'#67c4d0','lavender':'#b1a1d2','coral':'#ea8197','red':'#ff4777','white':'#ffffff','black':'#14171b','cyanCap':'#3c9fb1','lavenderCap':'#9384b6','coralCap':'#d85d7b','ivory':'#e9e4d2'}
contract=json.loads((ROOT/'Resources/controls.json').read_text())
by_id={p['id']:p for p in contract['controls']}
controls=[]
sections={'front':[], 'rear':[]}
TITLE_FONT=ImageFont.truetype('/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf',75)
BRAND_SHA256={'Protocodus-logo.svg':'65bc6ca2d22a6b5ac322f8ad7f7694f11d4a9dbf549778da36b03afb9b1a4841','Protocodus-logo.png':'d7ebc1f2ee9488dfb345e677d8b56ba8e0f76ae2e6276879d133483a50f56175'}
for name,digest in BRAND_SHA256.items():
 if hashlib.sha256((OUT/'Brand'/name).read_bytes()).hexdigest()!=digest:raise ValueError('Canonical Protocodus logo changed: '+name)
with Image.open(OUT/'Brand/Protocodus-logo.png') as source:
 BRAND_IMAGE=source.convert('RGBA');BRAND_IMAGE=BRAND_IMAGE.crop(BRAND_IMAGE.getchannel('A').getbbox())
brand_bytes=io.BytesIO();BRAND_IMAGE.save(brand_bytes,format='PNG');BRAND_URI='data:image/png;base64,'+base64.b64encode(brand_bytes.getvalue()).decode()
def brand_geometry(x,center_y,size):
 face=ImageFont.truetype('/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf',size*5)
 left,top,right,bottom=face.getbbox('PRESS78',anchor='ls');height=bottom-top
 logo_width=round(BRAND_IMAGE.width*height/BRAND_IMAGE.height)/5
 logo_y=round(center_y*5-height/2)/5;baseline=round(center_y*5-(top+bottom)/2)/5
 text_x=x+logo_width+10
 return {'logo':{'x':x,'y':logo_y,'width':logo_width,'height':height/5},'wordmark':{'x':text_x,'baseline_y':baseline,'size':size,'ink_bounds':[text_x+left/5,baseline+top/5,text_x+right/5,baseline+bottom/5]}}
BRANDING={'source_sha256':BRAND_SHA256,'gap':10,'faces':{'full':brand_geometry(28,25,30),'folded':brand_geometry(26,15,23)}}
APPEARANCE={'knob_size':40,'knob_sprite_size':50,'knob_inner_radius':15.5,'knob_pointer_inner':15.5,'knob_pointer_outer':24.1,'knob_pointer_width':13,'knob_pointer_style':'wedge','envelope_pointer_outline':.7,'value_font_size':11,'wave_font_size':13,'wave_active_color':'white','button_active_color':'white','envelope_face':'operator_accent','envelope_pointer':'black'}
APPEARANCE.update(knob_arc_radius=22.2,knob_arc_width=1.5,knob_track='#5b626b',pointer_fill='ink',pointer_outline='black',pointer_outline_width=.7)
def section(id,title,panel,x,y,w,h,accent):
 padding=20 if panel=='front' else 24;heading_offset=27 if panel=='front' else 25
 rule_start=round(x+padding+TITLE_FONT.getbbox(title,anchor='ls')[2]/5+6,3) if title else None
 d={'id':id,'title':title,'panel':panel,'x':x,'y':y,'width':w,'height':h,'accent':accent,'padding':padding,'heading':{'x':x+padding,'y':y+heading_offset,'rule_start':rule_start,'rule_end':x+w-padding,'rule_width':2,'rule_gap':6} if title else None}
 sections[panel].append(d);return d
mod=section('modulator','01  MODULATOR','front',35,73,334,224,'cyan')
car=section('carrier','02  CARRIER','front',385,73,334,224,'lavender')
motion=section('modulation','MODULATION / PERFORMANCE','front',35,314,334,192,'cyan')
output=section('effects','CHORUS / OUTPUT','front',385,314,334,192,'coral')
advanced=section('advanced','ADVANCED / CALIBRATION','rear',28,84,698,388,'cyan')
connections=section('connections',None,'rear',28,480,698,52,'cyan')
steps={'noiseRms':.0001,'clockDriftRateHz':.001,'masterTuneCents':.1,'lfoRateHz':.1,'chorusDepthMs':.1,'chorusRateHz':.01,'toneCutoffHz':1,'clockOffsetPpm':1,'clockDriftPpm':1}
units={'modulationAmount':'×','velocitySensitivity':'×','stereoWidth':'×','masterGain':'×','lfoRateHz':'Hz','chorusRateHz':'Hz','chorusDepthMs':'ms','toneCutoffHz':'Hz','clockOffsetPpm':'ppm','clockDriftPpm':'ppm','clockDriftRateHz':'Hz','masterTuneCents':'¢'}
OP_HELP={
 'mul':'Frequency ratio relative to the played note. Zero selects a half-frequency ratio.',
 'dt1':'Small pitch offset for beating and harmonic color; these are detune codes, not cents.',
 'tl':'Operator level. Turn up for more output. The modulator changes timbre; the carrier changes loudness.',
 'wave':'Choose a sine, signed squared sine, half sine, or squared half sine waveform.',
 'ar':'Attack rate: higher values reach full level faster. Zero prevents the attack from rising.',
 'd1r':'First decay rate: how fast the envelope falls toward the D1 level. Higher is faster; zero holds.',
 'd1l':'First decay attenuation: higher values set a quieter target for the first decay stage.',
 'd2r':'Second decay rate after the D1 target. Higher fades faster; zero holds the level.',
 'rr':'Release rate after note-off. Higher is faster; the Sustain switch selects the separate rear release rate.',
 'srr':'Release rate used when Sustain is enabled. Higher values release faster.',
 'lksLo':'Level scaling below the keyboard pivot. Larger codes reduce the lower notes more.',
 'lksHi':'Level scaling above the keyboard pivot. Larger codes reduce the upper notes more.',
 'rks':'Keyboard rate scaling. Larger settings speed up envelopes on higher notes.',
 'amEnable':'Allow the LFO to change this operator’s level. The rear AM range and front AM depth set the amount.',
 'dt2':'Shift this operator up by 600 cents, independently of fine detune.'}
HELP={
 'feedback':'Feed the modulator back into itself for brighter, rougher harmonics.',
 'modulationAmount':'Scale how strongly the modulator changes the carrier. More adds harmonic complexity.',
 'lfoRateHz':'Pitch and amplitude modulation speed in hertz.',
 'vibratoDelay':'Delay code before vibrato starts. The rear Delay scale multiplies it.',
 'vibratoDepth':'Pitch modulation depth multiplier. Enable Vibrato and choose a nonzero PM range on the rear.',
 'tremoloDepth':'Amplitude modulation depth multiplier. Also requires rear AM range and operator AM enable.',
 'velocitySensitivity':'How strongly note velocity changes loudness. Zero ignores velocity.',
 'vibrato':'Enable delayed pitch modulation. PM depth and the rear PM range set its strength.',
 'sustain':'Use each operator’s Sustain RR setting from the rear after note-off.',
 'chorusMix':'Chorus amount. Recorded mode scales the captured stereo-side character; Studio uses its creative delay blend.',
 'chorusRateHz':'Chorus motion speed in hertz.',
 'chorusDepthMs':'Chorus delay modulation depth in milliseconds.',
 'stereoWidth':'Stereo width multiplier. Zero is mono; one preserves the reference width.',
 'noiseRms':'Added noise amplitude before master volume. The rear Noise model chooses Circuit or White.',
 'drive':'Additional creative saturation. Zero leaves this extra drive stage off.',
 'toneCutoffHz':'Output low-pass cutoff in hertz. Lower values soften the high end.',
 'masterGain':'Master output gain. One is unity; zero mutes the instrument.',
 'pms':'Base pitch modulation range used with front PM depth and the Vibrato switch.',
 'ams':'Base amplitude modulation range used with front AM depth and each operator’s AM enable.',
 'lfoDelayScale':'Multiply the front vibrato delay. Zero starts modulation immediately.',
 'triangleLfo':'Select a sine or triangle modulation shape.',
 'globalLfo':'Share a running LFO phase across notes instead of starting each note’s phase separately.',
 'velocityToModulation':'How strongly note velocity changes FM intensity.',
 'bendRange':'Pitch-wheel range in semitones.',
 'modWheelDepth':'Additional pitch modulation depth from the modulation wheel.',
 'polyphony':'Maximum simultaneous voices.',
 'chorusMode':'Recorded follows the recording-derived stereo transfer; Studio is a creative chorus.',
 'noiseModel':'Circuit follows the sibling-circuit noise spectrum; White uses flat-spectrum noise.',
 'outputCircuit':'Enable the modeled sibling analog output transfer.',
 'clockOffsetPpm':'Fixed synthesis-clock offset in parts per million. Zero is nominal tuning.',
 'clockDriftPpm':'Peak modeled clock excursion in parts per million.',
 'clockDriftRateHz':'Speed of modeled clock drift in hertz.',
 'masterTuneCents':'Overall tuning offset in cents.',
 'dcBlock':'Remove DC from the output.',
 'outputLimit':'Enable output-level protection.'}
def add(prop,label,sec,y,col=0,cols=4,kind=None,accent=None):
 p=by_id[prop]
 if prop.startswith(('mod_','car_')):
  op='modulator' if prop.startswith('mod_') else 'carrier'; binding='patch.'+op+'.'+prop[4:]
 else:binding=p['target']+'.'+prop
 if prop in ('bendRange','modWheelDepth'):binding='rack.'+prop
 kind=kind or ('wave' if prop.endswith('_wave') else 'toggle' if p['integer'] and p['min']==0 and p['max']==1 else 'knob')
 content=sec['width']-2*sec['padding'];pitch=content/cols;w=min(90 if sec['panel']=='rear' else 68,pitch-8);cx=sec['x']+sec['padding']+(col+.5)*pitch
 if sec['panel']=='front':
  # Shared outer anchors keep differently sized knob rows aligned; the full-width
  # waveform bank remains an independent selector rather than a knob-column map.
  first=sec['x']+sec['padding']+25;last=sec['x']+sec['width']-sec['padding']-25
  pitch=(last-first)/(cols-1);cx=first+col*pitch;w=min(68,pitch-8)
 d={'id':(binding[6:] if prop.startswith(('mod_','car_')) else binding).replace('.','_'),'label':label,'binding':binding,'property_id':prop,'property_path':'/custom_properties/'+prop,'section':sec['id'],'panel':sec['panel'],'kind':kind,'x':round(cx-w/2,3),'y':y,'width':round(w,3),'height':52,'min':p['min'],'max':p['max'],'default':p['default'],'step':1 if p['integer'] else steps.get(prop,.01),'unit':units.get(prop,''),'accent':sec['accent']}
 if 'options' in p:d['options']=p['options']
 if accent:d['accent']=accent
 d['integer']=p['integer']
 if prop.startswith(('mod_','car_')) and prop[4:] in ('ar','d1r','d1l','d2r','rr'):d['visual_role']='envelope'
 d['tooltip']=OP_HELP[prop[4:]] if prop.startswith(('mod_','car_')) else HELP[prop]
 if prop in ('mod_tl','car_tl'):d['presentation']='operator_level'
 if kind=='wave':
  d.update(x=sec['x']+sec['padding'],width=content,height=28)
  gap=8;button=(content-3*gap)/4
  d['wave_cells']=[{'index':i,'label':v,'x':d['x']+i*(button+gap),'y':y,'width':button,'height':28} for i,v in enumerate(['SIN','SIN²','HALF','HALF²'])]
 controls.append(d)
for prefix,sec,extra in [('mod',mod,('feedback','Feedback')),('car',car,('modulationAmount','FM amount'))]:
 add(prefix+'_wave','Wave',sec,124)
 for col,(field,label) in enumerate([('mul','Ratio'),('dt1','Detune'),('tl','Level')]):add(prefix+'_'+field,label,sec,168,col)
 add(*extra,sec,168,3)
 for col,(field,label) in enumerate([('ar','Atk rate'),('d1r','D1 rate'),('d1l','D1 atten'),('d2r','D2 rate'),('rr','Rel rate')]):add(prefix+'_'+field,label,sec,232,col,5)
for row,entries in enumerate([
 [('lfoRateHz','LFO Hz'),('vibratoDelay','Delay'),('vibratoDepth','Pitch mod'),('tremoloDepth','Amp mod')],
 [('velocitySensitivity','Velocity'),('vibrato','Vibrato'),('sustain','Sustain')]]):
 for col,(prop,label) in enumerate(entries):add(prop,label,motion,366+row*66,col,len(entries))
for row,entries in enumerate([
 [('chorusMix','Chorus'),('chorusRateHz','Rate Hz'),('chorusDepthMs','Depth ms'),('stereoWidth','Width')],
 [('noiseRms','Noise'),('drive','Drive'),('toneCutoffHz','Cutoff Hz'),('masterGain','Output')]]):
 for col,(prop,label) in enumerate(entries):add(prop,label,output,366+row*66,col)
for row,(prefix,number,accent) in enumerate([('mod','01','cyan'),('car','02','lavender')]):
 for col,(field,label) in enumerate([('lksLo','LKS low'),('lksHi','LKS high'),('rks','RKS'),('srr','Sustain RR'),('amEnable','AM enable'),('dt2','DT2 +600¢')]):add(prefix+'_'+field,number+' '+label,advanced,134+row*66,col,6,accent=accent)
for row,(entries,accent) in enumerate([
 ([('pms','PM range'),('ams','AM range'),('lfoDelayScale','Delay scale'),('triangleLfo','LFO shape'),('globalLfo','Global LFO'),('velocityToModulation','Vel → FM')],'cyan'),
 ([('bendRange','Bend range'),('modWheelDepth','Wheel → PM'),('polyphony','Polyphony'),('chorusMode','Chorus type'),('noiseModel','Noise model'),('outputCircuit','Circuit')],'coral'),
 ([('clockOffsetPpm','Clock offset'),('clockDriftPpm','Drift peak'),('clockDriftRateHz','Drift rate'),('masterTuneCents','Master tune'),('dcBlock','DC block'),('outputLimit','Limiter')],'coral')]):
 for col,(prop,label) in enumerate(entries):add(prop,label,advanced,266+row*66,col,6,accent=accent)
assert {c['property_id'] for c in controls}==set(by_id)
assert len(controls)==len(by_id)==65
annotations=[]
bank=json.loads((ROOT/'Resources/FactoryBank/press78-factory.json').read_text())
def decode(v):
 r=v['raw_data'];p={}
 for op,k in [('modulator',0),('carrier',1)]:
  dt=r[1+k]>>4
  fields={'mul':r[1+k]&15,'dt1':-(dt&7) if dt&8 else dt&7,'tl':r[3+k]&127,'lksHi':r[5+k]>>4,'lksLo':r[5+k]&15,'rks':r[7+k]>>6,'ar':r[7+k]&63,'amEnable':r[9+k]>>7,'dt2':(r[9+k]>>6)&1,'d1r':r[9+k]&63,'wave':r[11+k]>>6,'d2r':r[11+k]&63,'d1l':r[13+k]>>4,'rr':r[13+k]&15,'srr':r[20+k]&15}
  p.update({'patch.'+op+'.'+f:x for f,x in fields.items()})
 p.update({'patch.feedback':(r[15]>>3)&7,'patch.pms':(r[16]>>4)&7,'patch.ams':r[16]&3,'patch.vibratoDelay':r[22]&127,'patch.vibrato':int(bool(r[24]&128)),'patch.sustain':int(bool(r[24]&64))})
 p.update({'controls.chorusMode':1,'controls.chorusRateHz':0.9546467517767424,'controls.chorusDepthMs':math.hypot(0.0495126833338911,0.4943632948117077)})
 return {'number':v['number'],'name':v['name'],'values':p}
presets=[decode(v) for v in bank['voices']]
preview={d['binding']:d['default'] for d in controls};preview.update(presets[0]['values'])
geom={'version':'Press78 layout study 06','logical_size':{'width':W,'height':H,'rack_units':8},'folded_size':{'width':W,'height':30},'status':'Shared geometry for interactive design preview and native prototype widgets','palette':C,'appearance':APPEARANCE,'native_patch_selector':{'x':247,'y':11,'width':315,'height':28,'kind':'host_native_placeholder'},'controls':controls,'sections':sections,'annotations':annotations,'spacing':{'section_gap':16,'section_padding':20,'operator_knob_row_pitch':64,'global_row_pitch':66,'rear_row_pitch':66,'caption_offset':48},'notes':['35 main sound/performance controls on the front; 30 advanced options and calibration controls on the rear.','Reason standard patch-name and patch-browse widgets are represented by browser selection for review only; all 100 factory patches use the PSS prefix.','Patch level stores raw TL attenuation; readout displays OFF at TL>=99 and 99-TL otherwise.','Envelope rates are raw rate codes; cyan and lavender envelope faces identify their operator.']}
geom['sockets']=[{'id':key,'property_path':path,'label':label,'panel':'rear','section':'connections','x':x,'y':506,'width':24,'height':24,'widget_bounds':{'x':x-12,'y':494,'width':24,'height':24},'caption':{'x':x+20,'baseline_y':510,'font_size':11,'anchor':'start'}} for key,path,label,x in [('gate_cv','/cv_inputs/gate_cv','GATE CV',68),('note_cv','/cv_inputs/note_cv','NOTE CV',177),('fm_cv','/cv_inputs/fm_cv','FM CV',286),('level_cv','/cv_inputs/level_cv','LEVEL CV',395),('left','/audio_outputs/left','LEFT',550),('right','/audio_outputs/right','RIGHT',659)]]
geom['routing_icons']=[{'x':525,'y':498,'asset':'Routing_Icon_White_01_1frames'},{'x':634,'y':498,'asset':'Routing_Icon_White_02_1frames'}]
geom['device_name_positions']={'front':{'x':586,'y':19},'back':{'x':586,'y':19},'folded_front':{'x':610,'y':9},'folded_back':{'x':610,'y':9}}
geom['header_alignment']={'full_center_y':25,'folded_center_y':15,'caption_baseline_y':43}
geom['version']='Press78 layout study 08'
geom['branding']=BRANDING
geom['material_bounds']={'photo_source_sha256':hashlib.sha256((OUT/'Assets/press78-photo-background-v2.png').read_bytes()).hexdigest(),'front_header_seam_y':49,'front_section_inset':20,'photo_pockets':{s['id']:{k:s[k] for k in ('x','y','width','height')} for s in sections['front']}}
geom['group_markers']=[{'panel':'rear','type':'bar','x':39,'y':134,'width':3,'height':44,'color':'cyan'},{'panel':'rear','type':'bar','x':39,'y':200,'width':3,'height':44,'color':'lavender'},{'panel':'rear','type':'separator','x':52,'y':253,'width':650,'color':'edge'},{'panel':'rear','type':'separator','x':52,'y':385,'width':650,'color':'edge'}]
geom.update(preview_patch=0,preview_state=preview,sdk={'root':'/Users/vojta/Dev/reason-rack-extension/SDK','version':'JukeboxSDK_500_028','target':'5.0'},source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'Source/DSP/Press78Engine.h',ROOT/'Resources/controls.json',ROOT/'Resources/FactoryBank/press78-factory.json']})
(OUT/'geometry.json').write_text(json.dumps(geom,indent=2)+'\n')

def txt(x,y,s,size=11,color='ink',anchor='start',weight=400,display=False):
 face='DIN Condensed' if display else 'DIN Alternate'
 return f'<text x="{x}" y="{y}" font-size="{size}" fill="{C[color]}" text-anchor="{anchor}" font-weight="{weight}" style="font-family:{face},Arial,sans-serif">{html.escape(str(s))}</text>'
def brand_wordmark(folded=False):
 layout=BRANDING['faces']['folded' if folded else 'full'];logo=layout['logo'];word=layout['wordmark']
 return '<g class="maker-brand"><image href="'+BRAND_URI+'" '+ ' '.join(f'{key}="{value}"' for key,value in logo.items())+'><title>Protocodus</title></image>'+txt(word['x'],word['baseline_y'],'PRESS78',word['size'],'ink',weight=700,display=True)+'</g>'
def rect(x,y,w,h,fill='panel',stroke='edge',r=2):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{C[fill]}" stroke="{C[stroke]}"/>'
def mixed_hex(a,b,amount):return '#'+''.join(f'{round(int(a[i:i+2],16)*(1-amount)+int(b[i:i+2],16)*amount):02x}' for i in (1,3,5))
def pointer_path(cx,cy,angle):
 inner,outer,half=APPEARANCE['knob_pointer_inner'],APPEARANCE['knob_pointer_outer'],APPEARANCE['knob_pointer_width']/2
 bx,by=cx+math.sin(angle)*inner,cy-math.cos(angle)*inner;tx,ty=math.cos(angle)*half,math.sin(angle)*half
 return f'M{bx+tx:.3f} {by+ty:.3f}L{cx+math.sin(angle)*outer:.3f} {cy-math.cos(angle)*outer:.3f}L{bx-tx:.3f} {by-ty:.3f}Z'
def position(d,v):
 return max(0,min(1,(99-v)/99)) if d.get('presentation')=='operator_level' else (v-d['min'])/(d['max']-d['min'])
def arc_path(cx,cy,fraction):
 radius=APPEARANCE['knob_arc_radius'];start=math.radians(-130);end=math.radians(-130+260*max(0,min(1,fraction)))
 if fraction<=0:return ''
 return f'M{cx+math.sin(start)*radius:.3f} {cy-math.cos(start)*radius:.3f}A{radius} {radius} 0 {int(fraction*260>180)} 1 {cx+math.sin(end)*radius:.3f} {cy-math.cos(end)*radius:.3f}'
def fmt(d,v):
 if 'options' in d:return d['options'][int(v)]
 if d['binding'].endswith('.tl'):return 'OFF' if v>=99 else str(99-int(v))
 if d['binding'].endswith('.mul'):return '½' if v==0 else str(v)+'×'
 if d['binding'].endswith('triangleLfo'):return 'TRI' if v else 'SINE'
 if d['kind']=='toggle':return 'ON' if v else 'OFF'
 if d['unit']=='Hz' and v>=1000:return f'{v/1000:.1f}k'
 if d['unit']=='ppm':
  n=f'{v/1000:g}k' if abs(v)>=1000 else f'{v:g}'
  return ('+' if 'Offset' in d['binding'] and v>=0 else '')+n
 if d['property_id']=='noiseRms' and 0<v<1:return f'{v:.4f}'.rstrip('0')[1:]
 return (f'{v:.4f}'.rstrip('0').rstrip('.') if d['step']<.001 else f'{v:.2f}'.rstrip('0').rstrip('.'))+('' if d['unit'] in ('Hz','ms') else d['unit'])
def widget(d):
 x,y,w=d['x'],d['y'],d['width'];cx=x+w/2;v=preview.get(d['binding'],d['default']);cid=d['id'];color=d['accent']
 s=f'<g id="{cid}" data-binding="{d["binding"]}" data-visual-role="{d.get("visual_role","standard")}">'
 if d['kind']=='wave':
  for cell in d['wave_cells']:
   i,label,bx,bw=cell['index'],cell['label'],cell['x'],cell['width']
   s+=f'<rect x="{bx}" y="{y+1.5}" width="{bw}" height="27" rx="2" fill="#080a0d"/>'
   active=i==v
   s+=f'<rect id="{cid}-w{i}" x="{bx+.5}" y="{y}" width="{bw-1}" height="25" rx="2" fill="{C["white"] if active else C[color+"Cap"]}" stroke="{"#ffffff" if active else "#171b20"}" filter="{"url(#waveGlow)" if active else "none"}"/>'
   s+=f'<text id="{cid}-label{i}" x="{bx+bw/2}" y="{y+12.5}" fill="{C["black"]}" font-size="{APPEARANCE["wave_font_size"]}" text-anchor="middle" dominant-baseline="central" font-weight="600">{label}</text>'
   s+=f'<path d="M{bx+3} {y+1.5}h{bw-6}" stroke="#ffffff" opacity=".25"/>'
 elif d['kind']=='toggle':
  s+=rect(x+3,y+7.5,w-6,21,'black','black')
  s+=f'<rect id="{cid}-button" x="{x+3}" y="{y+6}" width="{w-6}" height="22" rx="2" fill="{C["white"] if v else C["black"]}" stroke="{C["edge"]}"/>'
  s+=f'<path d="M{x+6} {y+7.5}h{w-12}" stroke="#ffffff" opacity=".15"/><text id="{cid}-value" x="{cx}" y="{y+21}" fill="{C["black"] if v else C["muted"]}" text-anchor="middle" font-size="11">{fmt(d,v)}</text>'+txt(cx,y+48,d['label'],11,'ink','middle')
 else:
  envelope=d.get('visual_role')=='envelope';cap='envelopeCap'+color if envelope else 'knobCap';face=C[color] if envelope else '#202329';pointer=C['ink'];ink=C['black'] if envelope else C['ink']
  fraction=position(d,v);angle=math.radians(-130+260*fraction)
  s+=f'<path d="{arc_path(cx,y+17,1)}" fill="none" stroke="{APPEARANCE["knob_track"]}" stroke-width="1.5" stroke-linecap="round"/><path id="{cid}-arc" d="{arc_path(cx,y+17,fraction)}" fill="none" stroke="{C[color]}" stroke-width="1.5" stroke-linecap="round"/>'
  s+=f'<circle cx="{cx}" cy="{y+17}" r="20" fill="#080a0d"/><circle cx="{cx}" cy="{y+16.5}" r="19.5" fill="url(#{cap})" stroke="{mixed_hex(C[color],C["black"],.28) if envelope else "#50545a"}" stroke-width=".65"/>'
  for tick in (-130,-65,0,65,130):
   a=tick*math.pi/180
   s+=f'<path d="M{cx+math.sin(a)*17} {y+16.5-math.cos(a)*17}L{cx+math.sin(a)*18.5} {y+16.5-math.cos(a)*18.5}" stroke="{C["black"] if envelope else "#797e83"}" opacity=".65" stroke-width=".65"/>'
  s+=f'<circle cx="{cx}" cy="{y+17}" r="15.5" fill="{face}" stroke="{mixed_hex(C[color],C["black"],.25) if envelope else "#15181c"}" stroke-width=".5"/><path id="{cid}-pointer" d="{pointer_path(cx,y+17,angle)}" fill="{pointer}" stroke="{C["black"]}" stroke-width=".7" stroke-linejoin="round"/>'
  s+=f'<text id="{cid}-value" x="{cx}" y="{y+21}" fill="{ink}" text-anchor="middle" font-size="11" style="font-family:Arial,sans-serif;font-variant-numeric:tabular-nums">{fmt(d,v)}</text>'+txt(cx,y+48,d['label'],11,'ink','middle')
 return s+'</g>'
def defs():
 envelope_defs=''.join(f'<linearGradient id="envelopeCap{color}" x2="0" y2="1"><stop stop-color="{mixed_hex(C[color],C["white"],.14)}"/><stop offset=".5" stop-color="{C[color]}"/><stop offset="1" stop-color="{mixed_hex(C[color],"#000000",.18)}"/></linearGradient>' for color in ('cyan','lavender'))
 return '<defs>'+envelope_defs+'<filter id="waveGlow" x="-15%" y="-35%" width="130%" height="170%"><feDropShadow dx="0" dy="0" stdDeviation="1.3" flood-color="#ffffff" flood-opacity=".3"/></filter><linearGradient id="shell" x2="0" y2="1"><stop stop-color="#373b41"/><stop offset="1" stop-color="#292c31"/></linearGradient><linearGradient id="pocket" x2="0" y2="1"><stop stop-color="#292c31"/><stop offset="1" stop-color="#23262b"/></linearGradient><linearGradient id="knobCap" x2="0" y2="1"><stop stop-color="#41464e"/><stop offset=".5" stop-color="#30353c"/><stop offset="1" stop-color="#25292f"/></linearGradient><linearGradient id="displayGlass" x2="0" y2="1"><stop stop-color="#2b1d25"/><stop offset=".45" stop-color="#19131c"/><stop offset="1" stop-color="#21151d"/></linearGradient><pattern id="grain" width="7" height="9" patternUnits="userSpaceOnUse"><path d="M1 1h.5M4 3h.6M2 7h.5M6 8h.4" stroke="#fff" stroke-width=".5" opacity=".09"/><path d="M5 1h.8M1 4h.5M4 6h.7" stroke="#000" stroke-width=".5" opacity=".15"/></pattern></defs>'
def shell(height):
 s=f'<rect width="754" height="{height}" fill="url(#shell)"/><rect width="754" height="{height}" fill="url(#grain)"/><path d="M0 .5H754" stroke="#60656b"/><path d="M0 {height-1}H754" stroke="#101216"/>'
 for x in (3,737):
  for y in range(65,height-25,6):s+=f'<path d="M{x} {y}h14" stroke="#15181d" stroke-width="2"/><path d="M{x} {y+1.5}h14" stroke="#42464c" stroke-width=".6"/>'
 return '<g class="material-surface">'+s+'</g>'
def title_rule(x,y,label,color,end,start,width):
 return txt(x,y,label,15,'ink',weight=700,display=True)+f'<path d="M{start} {y-5}H{end}" stroke="{C[color]}" stroke-width="{width}"/>'
def svg(panel):
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" overflow="visible" role="img" aria-label="Press78 {panel} design"><style>text{{font-family: DIN Alternate,Arial,sans-serif}}</style>'+defs()+shell(H)+'<g class="material-surface">'
 for x in (10,744):
  for y in (20,H-20):s+=f'<circle cx="{x}" cy="{y}" r="3.6" fill="#181b20" stroke="#50545a" stroke-width=".65"/><path d="M{x-1.7} {y}h3.4" stroke="#85898b" stroke-width=".7"/>'
 s+='</g>'
 s+=brand_wordmark()
 seam=49 if panel=='front' else 57.5
 s+=f'<path class="material-surface" d="M22 {seam}H732" stroke="#15181c"/><path class="material-surface" d="M22 {seam+1}H732" stroke="#4a4e55" stroke-width=".5"/>'
 if panel=='front':
  s+='<rect x="205" y="10" width="35" height="30" rx="2" fill="url(#displayGlass)" stroke="#111318"/>'+txt(222.5,32.9,'FM',22,'red','middle',display=True)+rect(247,11,315,28,'black','edge')
  s+='<image href="data:image/png;base64,'+base64.b64encode((OUT/'Assets/ReasonPatchBrowse.png').read_bytes()).decode()+'" x="498" y="14" width="58" height="22"><title>Reason standard patch browser — available in the host</title></image>'
  s+=txt(626,43,'DEVICE',11,'muted','middle')+txt(719,43,'NOTE',11,'muted','middle')+'<circle cx="719" cy="25" r="2.5" fill="#472332" stroke="#14171b"/>'
 else:s+=txt(233,31,'CONFIGURATION / CALIBRATION',16,'cyan',display=True)+txt(233,48,'DIGITAL SYNTHESIZER',9,'muted')
 s+='<image href="data:image/png;base64,'+base64.b64encode((OUT/'Assets/ReasonDeviceTape.png').read_bytes()).decode()+'" x="586" y="19" width="80" height="13"/>'+txt(626,29,'Press78',8,'black','middle')
 for sec in geom['sections'][panel]:
  x,y,w,h=sec['x'],sec['y'],sec['width'],sec['height']
  s+=f'<g class="material-surface"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2.5" fill="url(#pocket)" stroke="#191c21" stroke-width=".6"/><path d="M{x+2} {y+h+.5}H{x+w-2}" stroke="#555960" stroke-width=".5"/><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2.5" fill="url(#grain)"/></g>'
 for sec in geom['sections'][panel]:
  h=sec['heading']
  if h:s+=title_rule(h['x'],h['y'],sec['title'],sec['accent'],h['rule_end'],h['rule_start'],h['rule_width'])
 for a in geom['annotations']:
  if a['panel']==panel:s+=txt(a['x'],a['y'],a['text'],a['size'],a['color'])
 for marker in geom['group_markers']:
  if marker['panel']!=panel:continue
  x,y=marker['x'],marker['y']
  if marker['type']=='bar':s+=f'<rect x="{x}" y="{y}" width="{marker["width"]}" height="{marker["height"]}" rx="1.5" fill="{C[marker["color"]]}"/>'
  else:s+=f'<path d="M{x} {y}h{marker["width"]}" stroke="{C[marker["color"]]}" stroke-width=".65"/>'
 if panel=='rear':
  for socket in geom['sockets']:
   x,y=socket['x'],socket['y']
   s+=f'<g id="socket-{socket["id"]}" data-socket-path="{socket["property_path"]}"><circle cx="{x}" cy="{y}" r="12" fill="{C["black"]}" stroke="{C["edge"]}" stroke-width="3"/><circle cx="{x}" cy="{y}" r="5" fill="#080b0c"/>'+txt(x+20,y+4,socket['label'],11,'ink')+'</g>'
 for d in controls:
  if d['panel']==panel:s+=widget(d)
 return s+'</svg>'
for panel in ('front','rear'):(OUT/(panel+'.svg')).write_text(svg(panel))
for side in ('front','rear'):
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="754" height="30" viewBox="0 0 754 30">'+defs()+shell(30)+brand_wordmark(folded=True)
 if side=='front':
  s+=rect(267,5,295,20,'black')+txt(384,19,'PSS 00 Piano 1',11,'cyan','middle')+'<image href="data:image/png;base64,'+base64.b64encode((OUT/'Assets/ReasonPatchBrowse.png').read_bytes()).decode()+'" x="498" y="4" width="58" height="22"/>'+'<circle cx="719" cy="15" r="2.5" fill="#472332"/>'
 s+='<image href="data:image/png;base64,'+base64.b64encode((OUT/'Assets/ReasonDeviceTape.png').read_bytes()).decode()+'" x="610" y="9" width="80" height="13"/>'+txt(650,19,'Press78',8,'black','middle')+'</svg>'
 (OUT/('folded-'+side+'.svg')).write_text(s)
print(f'Generated styled {W}x{H} front/rear and folded SVGs; geometry.json')
for d in controls:
 if d['kind']=='knob':
  cx,cy=d['x']+d['width']/2,d['y']+17
  d['widget_bounds']={"x":cx-20,"y":cy-20,"width":40,"height":40}
  d['sprite_bounds']={"x":cx-25,"y":cy-25,"width":50,"height":50}
  extent=APPEARANCE['knob_pointer_outer']+.35
  d['visual_bounds']={"x":cx-extent,"y":cy-extent,"width":2*extent,"height":extent+20}
 elif d['kind']=='toggle':d['widget_bounds']={"x":d["x"]+3,"y":d["y"]+6,"width":d["width"]-6,"height":23}
 else:d['widget_bounds']={"x":d["x"],"y":d["y"],"width":d["width"],"height":28}
 d['caption']={"x":d["x"]+d["width"]/2,"baseline_y":d["y"]+48,"font_size":11,"anchor":"middle"}
(OUT/'geometry.json').write_text(json.dumps(geom,indent=2)+'\n')
template=(OUT/'preview_template.html').read_text()
for token,name in [('__FRONT__','front.svg'),('__REAR__','rear.svg'),('__FOLDED_FRONT__','folded-front.svg'),('__FOLDED_REAR__','folded-rear.svg')]:template=template.replace(token,(OUT/name).read_text())
template=template.replace('__PANEL_HEIGHT__',str(H)).replace('__RACK_UNITS__',str(H//69))
template=template.replace('62 mapped controls',str(len(controls))+' mapped controls')
template=template.replace('__GEOMETRY__',json.dumps(geom).replace('<','\\u003c')).replace('__PRESETS__',json.dumps(presets).replace('<','\\u003c'))
(OUT/'index.html').write_text(template)
print(f'Built interactive Design/index.html; all 100 factory previews and {len(controls)} canonical properties embedded.')
