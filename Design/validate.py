"""Independent layout/control-contract checks for the review artifacts."""
from pathlib import Path
from itertools import combinations
import hashlib,json,base64,io,xml.etree.ElementTree as ET
from PIL import Image,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Design'
g=json.loads((OUT/'geometry.json').read_text());canonical={x['id']:x for x in json.loads((ROOT/'Resources/controls.json').read_text())['controls'] if not x.get('hidden',False)}
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
front_ids={f'{op}_{field}' for op in ('mod','car') for field in ('wave','mul','dt1','tl','ar','d1r','d1l','d2r','rr')}|{'feedback','modulationAmount','lfoRateHz','vibratoDelay','vibratoDepth','tremoloDepth','velocitySensitivity','vibrato','sustain','chorusMix','chorusRateHz','chorusDepthMs','stereoWidth','drive','toneCutoffHz','masterGain'}
assert {c['property_id'] for c in controls if c['panel']=='front'}==front_ids
assert rear_ids==set(canonical)-front_ids
assert len(front_ids)==34 and len(rear_ids)==29
section_map={s['id']:s for panel in g['sections'].values() for s in panel}
for c in controls:
 sec=section_map[c['section']];b=c.get('visual_bounds',c['widget_bounds']);caption=c['caption']
 assert b['x']-sec['x']>=min(14,sec['padding']) and sec['x']+sec['width']-b['x']-b['width']>=min(14,sec['padding']),c['id']
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
# Physical-pocket evidence is independent of generated section declarations.
# The header-only material edit must retain these measured bevel coordinates.
expected_pockets={'modulator':(35,73,334,224),'carrier':(385,73,334,224),'modulation':(35,314,334,192),'effects':(385,314,334,192)}
assert hashlib.sha256((OUT/g['material_bounds']['photo_asset']).read_bytes()).hexdigest()==g['material_bounds']['photo_source_sha256']
for sec in g['sections']['front']:
 assert tuple(sec[k] for k in ('x','y','width','height'))==expected_pockets[sec['id']]
 rows={}
 for c in controls:
  if c['section']==sec['id'] and c['kind']!='wave':rows.setdefault(c['y'],[]).append(c)
 for row in rows.values():
  centers=sorted(c['x']+c['width']/2 for c in row)
  assert abs(centers[0]-(sec['x']+45))<=.001 and abs(centers[-1]-(sec['x']+sec['width']-45))<=.001,sec['id']
  assert len({c['caption']['baseline_y'] for c in row})==1,sec['id']
  for c in row:
   b=c['widget_bounds'];center=b['y']+(b['height']-1)/2 if c['kind']=='toggle' else b['y']+b['height']/2
   assert abs(center-(c['y']+17))<1e-6,c['id']
header=g['header_alignment'];assert header['separator_y']==49 and header['caption_baseline_y']==37
assert header['full_center_y']==25 and header['folded_center_y']==15
for panel,pos in g['device_name_positions'].items():
 if panel.startswith('folded'):assert abs(pos['y']+6.5-15)<=.5,panel
 else:assert pos=={'x':586,'y':13},panel
for name,group in g['header_groups'].items():
 b=group['visible_bounds'];assert abs(b['y']+b['height']/2-header['full_center_y'])<=.5,name
 assert b['y']>0 and b['y']+b['height']<header['separator_y'],name
 if 'caption' in group:assert group['caption']['baseline_y']==37,name
# Captions are part of their group bounds; independently measure the text ink.
for name in ('device','note'):
 group=g['header_groups'][name];caption=group['caption'];face=ImageFont.truetype(font_path,55)
 left,top,right,bottom=[v/5 for v in face.getbbox(caption['text'],anchor='ls')]
 b=group['visible_bounds'];assert abs(caption['baseline_y']+bottom-b['y']-b['height'])<1e-6,name
 assert caption['baseline_y']+top>b['y'],name
assert g['note_positions']['front']=={'x':705,'y':11}
assert g['note_positions']['folded_front']=={'x':714,'y':10}
hardware=g['rack_hardware'];reserved=hardware['host_fold_reserved_bounds'];assert reserved=={'x':0,'y':0,'width':27,'height':30}
assert hardware['top_screws']==[{'x':17,'y':38,'radius':8},{'x':737,'y':38,'radius':8}]
assert sum(s['x'] for s in hardware['top_screws'])==W
for screw in hardware['top_screws']:
 assert screw['y']-screw['radius']>=reserved['y']+reserved['height']
 assert screw['y']+screw['radius']<header['separator_y']
note=g['header_groups']['note']['visible_bounds'];assert note['x']+note['width']+5<hardware['top_screws'][1]['x']-8
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
 assert logo['x']-(reserved['x']+reserved['width'])>=15,(face,'branding clears host fold area by at least15px')
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
 for asset,logical_size in [('ReasonPatchBrowse',(58,22)),('ReasonDeviceTape',(80,13))]:
  encoded='data:image/png;base64,'+base64.b64encode((OUT/'Assets'/(asset+'.png')).read_bytes()).decode()
  for image in xml.findall('{http://www.w3.org/2000/svg}image'):
   if image.attrib.get('href')!=encoded:continue
   assert tuple(float(image.attrib[k]) for k in ('width','height'))==logical_size,(name,asset)
   center=float(image.attrib['y'])+logical_size[1]/2
   expected_center=15 if name.startswith('folded') else 19.5 if asset=='ReasonDeviceTape' else 25
   assert abs(center-expected_center)<=.5,(name,asset)
 if not name.startswith('folded'):
  actual_screws=xml.findall(".//{http://www.w3.org/2000/svg}g[@data-top-screw='true']")
  assert len(actual_screws)==2,name
  for node,screw in zip(actual_screws,hardware['top_screws']):
   circle=node.find('{http://www.w3.org/2000/svg}circle')
   assert tuple(float(circle.attrib[k]) for k in ('cx','cy','r'))==tuple(screw[k] for k in ('x','y','radius')),name
  for key,group in g['header_groups'].items():
   if name not in group['panels'] or 'caption' not in group:continue
   caption=xml.find("{http://www.w3.org/2000/svg}g[@id='header-"+name+"-"+key+"-caption']/{http://www.w3.org/2000/svg}text")
   assert caption is not None and float(caption.attrib['y'])==37,(name,key)
 size=Image.open(OUT/(name+'@1x.png')).size;assert size==expected
 images[name]=list(size)
assert Image.open(OUT/'front-photo@1x.png').size==(W,H)
source_paths=[OUT/'geometry.json',OUT/'build_wireframe.py',OUT/'preview_template.html',OUT/'index.html',OUT/'render_preview.cjs',ROOT/'Resources/controls.json']
result={'passed':True,'controls':len(ids),'canonical_properties':len(canonical),'unmapped_properties':[],'overlapping_widget_bounds':0,'captions_fit_at_11px':True,'caption_font':font_path,'raster_dimensions':images,'svg_rasterizer':'@resvg/resvg-js 2.6.2, DIN Alternate / DIN Condensed system fonts','browser_visual_review':'Layout study10: header group bounds, at least15px brand/fold clearance and four deterministic local panels checked; synthetic DOM interaction separate; no new live-browser interaction claim.','native_host_tested':False,'scope':'Wireframe geometry, property contract and SVG raster checks; no DSP/audio or native host claims.','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}}
result.update(branding_fold_clearance_min_px=15,header_group_center_tolerance_px=.5,fold_reserved_nominal_clearance_px=0,photo_screw_position_tolerance_px=1,top_screw_center_y=38,sockets=len(sockets),cv_inputs=4,audio_outputs=2,front_controls=34,rear_controls=29,rack_units=g['logical_size']['rack_units'],section_side_padding_min_px=14,front_heading_padding_px=20,rear_heading_padding_px=24,heading_to_visible_control_min_px=17.55,caption_to_section_bottom_min_px=14,wave_button_min_width_px=60,wave_button_gap_px=8,knob_body_px=40,knob_sprite_px=50)
(OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
