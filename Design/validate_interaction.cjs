// Run a synthetic DOM check; this does not exercise a browser or native host.
const fs=require('fs'),path=require('path');
const {JSDOM}=require(process.env.PRESS78_JSDOM_MODULE || 'jsdom');
const dom=new JSDOM(fs.readFileSync(path.join(__dirname,'index.html'),'utf8'),{runScripts:'dangerously'}),w=dom.window,d=w.document;
const assert=(ok,reason)=>{if(!ok)throw Error(reason);};
assert(d.querySelector('#preset').options.length===100,'100 presets');
assert(Array.from(d.querySelector('#preset').options).every(o=>/^PSS \d{2} /.test(o.textContent)),'all factory names have PSS prefix');
assert(d.querySelectorAll('[data-range-id],[data-toggle-id]').length===61,'61 nonwave controls');
assert(d.querySelectorAll('[data-wave-id]').length===8,'two four-way waves');
assert(d.querySelectorAll('[data-socket-path]').length===6,'four CV and two audio sockets');
assert(d.querySelectorAll('#front-panel [data-range-id],#front-panel [data-toggle-id]').length+2===34,'34 front main sound and performance controls');
assert(d.querySelectorAll('#rear-panel [data-range-id],#rear-panel [data-toggle-id]').length===29,'29 rear advanced/calibration controls');
const geometry=w.eval('geometry');
const near=(a,b)=>Math.abs(a-b)<1e-6;
for(const c of geometry.controls){
 if(c.kind==='wave'){
  for(const cell of c.wave_cells){const hit=d.querySelector(`[data-wave-id="${c.id}"][data-value="${cell.index}"]`);for(const [css,key] of [['left','x'],['top','y'],['width','width'],['height','height']])assert(near(parseFloat(hit.style[css]),cell[key]),`${c.id} wave hit${cell.index} ${css}`);}
 }else{
  const hit=c.kind==='toggle'?d.querySelector(`[data-toggle-id="${c.id}"]`):d.querySelector(`[data-range-id="${c.id}"]`).parentElement;
  for(const [css,key] of [['left','x'],['top','y'],['width','width'],['height','height']])assert(near(parseFloat(hit.style[css]),c.widget_bounds[key]),`${c.id} hit matches drawn geometry: ${css}`);
  if(c.kind==='toggle'){const cap=d.getElementById(c.id+'-button');assert(near(+cap.getAttribute('y')+ +cap.getAttribute('height')/2,c.y+17),`${c.id} cap shares knob row center`);}
 }
}
const presetStyle=w.getComputedStyle(d.querySelector('#preset'));
assert(near(parseFloat(presetStyle.top)+parseFloat(presetStyle.height)/2,25),'preset selector shares full header center');
assert(Math.abs(geometry.branding.faces.full.logo.y+geometry.branding.faces.full.logo.height/2-25)<=.100001,'logo5x raster rounding preserves header center');
for(const panel of ['front','rear']){
 const scope=d.querySelector(`#${panel}-panel`),tape=scope.querySelector(`#header-${panel}-device-tape`),caption=scope.querySelector(`#header-${panel}-device-caption text`);
 assert(+tape.getAttribute('y')===13&&+caption.getAttribute('y')===37,`${panel} complete DEVICE group centered`);
 assert(near((+tape.getAttribute('y')+ +caption.getAttribute('y'))/2,25),`${panel} DEVICE ink bounds share header center`);
 const screws=scope.querySelectorAll('[data-top-screw] > circle:first-child');
 assert(screws.length===2&&Array.from(screws).every(s=>+s.getAttribute('cy')===38&&+s.getAttribute('r')===8),`${panel} screws clear fixed fold area`);
}
const note=d.querySelector('#header-note-lamp'),noteCaption=d.querySelector('#header-front-note-caption text');
assert(+note.getAttribute('cx')===710&&+note.getAttribute('cy')===16&&+noteCaption.getAttribute('y')===37,'NOTE visible group raised and cleared from right screw');
assert(Math.abs((+note.getAttribute('cy')-2.5+ +noteCaption.getAttribute('y'))/2-25)<=.5,'NOTE ink bounds share header center');
const select=d.querySelector('#preset');select.value='99';select.dispatchEvent(new w.Event('change'));
assert(d.querySelector('#preset').selectedOptions[0].textContent.startsWith('PSS 99'),'native-style preset name');
assert(d.querySelector('#front-panel svg').textContent.includes('FM'),'fixed FM badge matches native header');
assert(d.querySelector('#modulator_tl-value').textContent==='OFF','sine modulator muted');
assert(d.querySelector('#carrier_tl-value').textContent==='86','sine carrier TL decoded');
const attack=d.querySelector('[data-range-id="carrier_ar"]');attack.value='12';attack.dispatchEvent(new w.Event('input'));
assert(d.querySelector('#carrier_ar-value').textContent==='12','knob readout');
d.querySelector('[data-wave-id="carrier_wave"][data-value="3"]').click();assert(d.querySelector('[data-wave-id="carrier_wave"][data-value="3"]').getAttribute('aria-pressed')==='true','wave selection');
for(const op of ['modulator','carrier'])for(let selected=0;selected<4;selected++){
 d.querySelector(`[data-wave-id="${op}_wave"][data-value="${selected}"]`).click();
 for(let i=0;i<4;i++){const cap=d.querySelector(`#${op}_wave-w${i}`);assert((cap.getAttribute('fill')==='#ffffff')===(i===selected),'only selected waveform lights white');assert(cap.getAttribute('filter')===(i===selected?'url(#waveGlow)':'none'),'wave glow follows selection');}
}
d.querySelector('[data-view="rear"]').click();assert(!d.querySelector('#rear-panel').hidden&&d.querySelector('#front-panel').hidden,'rear view');
const model=d.querySelector('[data-toggle-id="controls_chorusMode"]');assert(model.getAttribute('aria-pressed')==='true','factory chorus model Recorded');assert(d.querySelector('#controls_chorusMode-value').textContent==='Recorded','model label');model.click();assert(d.querySelector('#controls_chorusMode-value').textContent==='Studio','model changes');
assert(!d.querySelector('[data-toggle-id="controls_noiseModel"]')&&!d.querySelector('[data-range-id="controls_noiseRms"]'),'removed noise controls absent');
const circuit=d.querySelector('[data-toggle-id="controls_outputCircuit"]');assert(circuit.getAttribute('aria-pressed')==='true','circuit defaults on');assert(d.querySelector('#controls_outputCircuit-button').getAttribute('fill')==='#ffffff','active toggles are white');circuit.click();assert(circuit.getAttribute('aria-pressed')==='false','circuit toggle');
d.querySelector('[data-view="folded"]').click();assert(!d.querySelector('#folded-view').hidden,'folded view');assert(d.querySelector('#folded-view').textContent.includes('PSS 99'),'folded patch follows preset');
d.querySelector('#restore').click();assert(d.querySelector('#carrier_ar-value').textContent==='63','restore resets patch edits');assert(circuit.getAttribute('aria-pressed')==='true','restore baseline globals');
// Level presentation must reverse the raw attenuation property without changing
// raw factory bytes on load, click, cancel, or movement against the mute limit.
const level=d.querySelector('[data-range-id="modulator_tl"]');
const raw=()=>w.eval('state["patch.modulator.tl"]');
const send=(type,init={})=>level.dispatchEvent(new w.MouseEvent(type,{bubbles:true,button:0,clientX:100,clientY:100,...init}));
assert(raw()===127,'muted factory raw TL preserved');assert(level.value==='0','muted Level starts at zero');
const mutePath=d.querySelector('#modulator_tl-pointer').getAttribute('d');
send('pointerdown');send('pointerup');assert(raw()===127,'tap preserves raw muted code');
send('pointerdown');send('pointermove',{clientY:120});send('pointerup');assert(raw()===127,'drag below mute preserves raw code');
send('pointerdown');send('pointermove',{clientY:30});assert(raw()===49,'upward half-range drag increases Level to50');
assert(d.querySelector('#modulator_tl-value').textContent==='50','Level readout follows gesture');assert(d.querySelector('#modulator_tl-pointer').getAttribute('d')!==mutePath,'Level pointer turns clockwise');
send('pointercancel');assert(raw()===127,'cancel restores exact muted raw code');
send('pointerdown');send('pointermove',{clientY:30,shiftKey:true});assert(raw()===94,'Shift applies one-tenth movement');send('pointerup');
send('pointerdown',{ctrlKey:true});assert(raw()===127,'Ctrl reset restores exact default');
level.dispatchEvent(new w.KeyboardEvent('keydown',{key:'ArrowUp',bubbles:true}));assert(raw()===98,'up arrow raises Level');
level.dispatchEvent(new w.KeyboardEvent('keydown',{key:'End',bubbles:true}));assert(raw()===0,'End reaches full Level');
const field=d.querySelector('#precise');field.value='25';field.dispatchEvent(new w.Event('input'));assert(raw()===74,'precise inspector accepts displayed Level');
assert(!d.querySelector('#control-description').textContent.includes('/custom_properties'),'help describes sound rather than property paths');
assert(d.querySelector('#controls_chorusMix').textContent.includes('Chorus'),'chorus controls identified');
assert(d.querySelector('#carrier_ar').textContent.includes('Atk rate'),'envelope caption describes rate');
assert(d.querySelectorAll('[id$="-arc"]').length===49,'all knobs have position arcs');
// Accessible values retain physical units while avoiding a second multiplier
// already included by the visible formatter. Exercise real DOM input updates.
for(const [id,value,expected] of [
 ['controls_modulationAmount',1,'1×'],
 ['controls_masterGain',0.25,'0.25×'],
 ['controls_lfoRateHz',30,'30 Hz'],
 ['controls_toneCutoffHz',14000,'14.0k Hz'],
 ['controls_chorusDepthMs',0.5,'0.5 ms'],
 ['controls_clockOffsetPpm',20,'+20 ppm'],
 ['controls_masterTuneCents',0,'0 ¢'],
 ['modulator_mul',0,'½'],
 ['modulator_mul',1,'1×'],
 ['modulator_tl',0,'OFF'],
]){
 const control=d.querySelector(`[data-range-id="${id}"]`);control.value=String(value);control.dispatchEvent(new w.Event('input'));
 assert(control.getAttribute('aria-valuetext')===expected,`accessible unit/value: ${id}`);
}
d.querySelector('#restore').click();
const report={passed:true,kind:'Synthetic DOM interaction checks, not browser/native-host testing',preset_options:100,canonical_controls:63,sockets:6,checks:['100 PSS-prefixed presets; preset99 name, Level values and folded name','attack edit updates readout','all eight waveform selections: aria, whole white cap and glow','fixed FM badge matches native header','DEVICE/NOTE captions included in centering; both full panels clear fixed host fold area','all69 browser hit regions match drawn geometry; mixed row and header visual centers','rear/folded visibility','chorus model choices; removed noise controls absent','output circuit default and toggle','preset reload restores fields and global defaults','four CV and two audio socket placeholders','34 front controls and 29 rear advanced/configuration controls','Level inverse drag, fine adjustment, reset, cancel, keyboard and numeric entry preserve raw patch semantics','musical help, unit/rate captions and 49 position arcs','10 accessible value cases retain physical units without duplicated multiplier suffixes'],runtime:'Node.js with jsdom 30.1.3'};
fs.writeFileSync(path.join(__dirname,'interaction-validation.json'),JSON.stringify(report,null,2)+'\n');console.log(report);
