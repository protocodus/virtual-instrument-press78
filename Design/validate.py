"""Independent layout/control-contract checks for the review artifacts."""
from pathlib import Path
from itertools import combinations
import hashlib,json,base64,io,xml.etree.ElementTree as ET
from PIL import Image,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Design'
g=json.loads((OUT/'geometry.json').read_text());canonical={x['id']:x for x in json.loads((ROOT/'Resources/controls.json').read_text())['controls']}
font_path='/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf'
font=ImageFont.truetype(font_path,11)
W,H=g['logical_size']['width'],g['logical_size']['height']
assert H==g['logical_size']['rack_units']*69
controls=g['controls'];ids=[x['property_id'] for x in controls]
assert len(ids)==len(set(ids))
assert set(ids)==set(canonical),{'unmapped':sorted(set(canonical)-set(ids)),'extra':sorted(set(ids)-set(canonical))}
for d in controls:
 p=canonical[d['property_id']]
 assert all(d[k]==p[k] for k in ('min','max','default')),d['id']
 assert d['property_path']=='/custom_properties/'+d['property_id']
 b=d['widget_bounds'];assert b['x']>=0 and b['y']>=0 and b['x']+b['width']<=W and b['y']+b['height']<=H,d['id']
 if d['kind']!='wave':assert font.getlength(d['label'])<=d['width'],d['id']
rear_ids={c['property_id'] for c in controls if c['panel']=='rear'}
front_ids={f'{op}_{field}' for op in ('mod','car') for field in ('wave','mul','dt1','tl','ar','d1r','d1l','d2r','rr')}|{'feedback','modulationAmount','lfoRateHz','vibratoDelay','vibratoDepth','tremoloDepth','velocitySensitivity','vibrato','sustain','chorusMix','chorusRateHz','chorusDepthMs','stereoWidth','noiseRms','drive','toneCutoffHz','masterGain'}
assert {c['property_id'] for c in controls if c['panel']=='front'}==front_ids
assert rear_ids==set(canonical)-front_ids
assert len(front_ids)==35 and len(rear_ids)==30
section_map={s['id']:s for panel in g['sections'].values() for s in panel}
for c in controls:
 sec=section_map[c['section']];b=c.get('visual_bounds',c['widget_bounds']);caption=c['caption']
 assert b['x']-sec['x']>=24 and sec['x']+sec['width']-b['x']-b['width']>=24,c['id']
 assert b['y']-sec['heading']['y']>=17.5,c['id']
 assert sec['y']+sec['height']-(caption['baseline_y']+2)>=14,c['id']
 if c['kind']=='wave':
  cells=c['wave_cells']
  assert all(z['width']>=60 for z in cells)
  assert all(b['x']-a['x']-a['width']>=8 for a,b in zip(cells,cells[1:]))
for a,b in combinations(controls,2):
 if a['section']==b['section'] and a['y']==b['y'] and a['kind']!='wave' and b['kind']!='wave':
  ac=a['x']+a['width']/2;bc=b['x']+b['width']/2
  assert abs(ac-bc)>=58.3,(a['id'],b['id'])
sockets=g['sockets'];socket_paths=[s['property_path'] for s in sockets]
assert len(socket_paths)==len(set(socket_paths))==6
assert set(socket_paths)=={'/cv_inputs/'+p+'_cv' for p in ('gate','note','fm','level')}|{'/audio_outputs/left','/audio_outputs/right'}
for s in sockets:
 b=s['widget_bounds'];assert b['x']>=0 and b['y']>=0 and b['x']+b['width']<=W and b['y']+b['height']<=H,s['id']
for a,b in combinations(controls+sockets,2):
 if a['panel']!=b['panel']:continue
 x,y=a.get('visual_bounds',a['widget_bounds']),b.get('visual_bounds',b['widget_bounds'])
 overlap=max(x['x'],y['x'])<min(x['x']+x['width'],y['x']+y['width']) and max(x['y'],y['y'])<min(x['y']+x['height'],y['y']+y['height'])
 assert not overlap,(a['id'],b['id'])
for name,digest in g['branding']['source_sha256'].items():
 assert hashlib.sha256((OUT/'Brand'/name).read_bytes()).hexdigest()==digest,name
with Image.open(OUT/'Brand/Protocodus-logo.png') as source:
 canonical_logo=source.convert('RGBA');canonical_logo=canonical_logo.crop(canonical_logo.getchannel('A').getbbox())
for face,brand in g['branding']['faces'].items():
 logo,word=brand['logo'],brand['wordmark'];ink=word['ink_bounds']
 assert abs(logo['width']/logo['height']-canonical_logo.width/canonical_logo.height)<.01,face
 assert abs(logo['height']-(ink[3]-ink[1]))<1e-6,face
 assert abs(word['x']-logo['x']-logo['width']-10)<1e-6,face
 assert ink[2]<=(188 if face=='full' else 255),face
images={}
for name,expected in [('front',(W,H)),('rear',(W,H)),('folded-front',(754,30)),('folded-rear',(754,30))]:
 xml=ET.parse(OUT/(name+'.svg')).getroot()
 assert (int(xml.attrib['width']),int(xml.attrib['height']))==expected
 brand=xml.find("{http://www.w3.org/2000/svg}g[@class='maker-brand']")
 assert brand is not None and 'by Protocodus' not in ''.join(xml.itertext()),name
 mark=brand.find('{http://www.w3.org/2000/svg}image');assert mark is not None,name
 with Image.open(io.BytesIO(base64.b64decode(mark.attrib['href'].split(',',1)[1]))) as embedded:
  assert embedded.size==canonical_logo.size and embedded.tobytes()==canonical_logo.tobytes(),name
 size=Image.open(OUT/(name+'@1x.png')).size;assert size==expected
 images[name]=list(size)
source_paths=[OUT/'geometry.json',OUT/'build_wireframe.py',OUT/'preview_template.html',OUT/'index.html',OUT/'render_preview.cjs',ROOT/'Resources/controls.json']
result={'passed':True,'controls':len(ids),'canonical_properties':len(canonical),'unmapped_properties':[],'overlapping_widget_bounds':0,'captions_fit_at_11px':True,'caption_font':font_path,'raster_dimensions':images,'svg_rasterizer':'@resvg/resvg-js 2.6.2, DIN Alternate / DIN Condensed system fonts','browser_visual_review':'Layout study 07: full browser and four local panels visually inspected at 1x; separate native asset validation in Rack checkout.','native_host_tested':False,'scope':'Wireframe geometry, property contract and SVG raster checks; no DSP/audio or native host claims.','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}}
result.update(sockets=len(sockets),cv_inputs=4,audio_outputs=2,front_controls=35,rear_controls=30,rack_units=g['logical_size']['rack_units'],section_side_padding_min_px=24,heading_to_visible_control_min_px=17.55,caption_to_section_bottom_min_px=14,wave_button_min_width_px=60,wave_button_gap_px=8,knob_body_px=40,knob_sprite_px=50)
(OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
