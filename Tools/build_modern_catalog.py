"""Publish fixed-gain modern factory auditions as a local HTML/MP3 catalog."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import json
from pathlib import Path
import subprocess

from modern_bank import ROOT, load_modern

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audition',required=True,type=Path)
    args=parser.parse_args(); source=args.audition.resolve()
    result=json.loads((source/'results.json').read_text())
    assert result['passed'] and result['preset_count']==50 and result['render_count']==450
    for name,value in result['source_sha256'].items():
        assert sha(Path(name))==value, 'Audition source changed: '+name
    voices=load_modern(); by_id={v['id']:v for v in result['presets']}
    dest=ROOT/'Docs/audio/modern';dest.mkdir(parents=True,exist_ok=True)
    def encode(v):
        raw=source/by_id[v['id']]['renders']['phrase']['relative_path']
        out=dest/(v['id']+'.mp3')
        command=['ffmpeg','-nostdin','-v','error','-y','-i',str(raw),'-map_metadata','-1',
                 '-c:a','libmp3lame','-b:a','160k','-ar','48000','-ac','2','-threads','1',str(out)]
        subprocess.run(command,check=True,capture_output=True)
        return {'id':v['id'],'name':v['name'],'input_wav_sha256':sha(raw),
                'mp3_sha256':sha(out),'path':out.relative_to(ROOT).as_posix(),
                'input_peak':by_id[v['id']]['renders']['phrase']['peak']}
    with ThreadPoolExecutor(max_workers=4) as pool:
        files=list(pool.map(encode,voices))
    esc=html.escape; cards=[]
    for v in voices:
        low,high=v['recommended_notes']; perf=v['performance']
        cards.append('<article data-category="'+esc(v['category'])+'"><small>'+esc(v['category'])+
          ' · MIDI '+str(low)+'–'+str(high)+'</small><h2>'+esc(v['name'])+'</h2><p>'+esc(v['description'])+
          '</p><audio controls preload="none" src="../audio/modern/'+v['id']+'.mp3"></audio><details><summary>Playing response</summary><p><b>Velocity:</b> '+
          esc(perf['velocity'])+'</p><p><b>Mod wheel:</b> '+esc(perf['mod_wheel'])+'</p><p><b>Pitch bend:</b> '+esc(perf['pitch_bend'])+'</p></details></article>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Press78 · Modern factory sounds</title>
<style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#1d2327;color:#ece8dd;font:16px/1.55 system-ui}main{max-width:1140px;padding:40px 24px;margin:auto}h1{margin:0;font-size:36px;letter-spacing:.02em}header{border-bottom:3px solid #64bdc8;padding-bottom:24px;margin-bottom:24px}header p{max-width:820px;color:#bbc5ca}nav{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}input,select{font:inherit;color:inherit;background:#151b1f;border:1px solid #78868d;padding:10px 14px;border-radius:5px}input{flex:1;min-width:220px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}article{background:#292f34;border:1px solid #485259;border-radius:8px;padding:22px;display:flex;flex-direction:column;gap:10px}article[hidden]{display:none}h2{font-size:18px;color:#d1c4ed;margin:0}small{color:#69c6d2}article p{margin:0;color:#c7cdd0}audio{width:100%;margin-top:auto;padding-top:8px}summary{cursor:pointer;color:#e4dbe8}details p{padding-top:8px;font-size:14px}footer{margin-top:28px;color:#aebbc1;font-size:14px}a{color:#69c6d2}</style>
<main><header><h1>PRESS78 / MODERN</h1><p>50 original sounds for bass lines, donk rhythms, melodic hooks, layered chords and transitions. The instrument also includes 100 original presets under the PSS prefix.</p><p>These demos play the exported Reason patches through the native Rack wrapper at their authored levels. No per-file normalization. MP3 previews accompany the lossless validation renders.</p></header><nav><input id="search" type="search" aria-label="Search sounds" placeholder="Search sounds…"><select id="category" aria-label="Category"><option value="">All 50 sounds</option>'''+''.join('<option>'+c+'</option>' for c in ['Bass','Donk','Pluck','Lead','Pad','FX'])+'''</select></nav><section class="grid">'''+''.join(cards)+'''</section><footer>Load sounds using Reason’s standard patch browser: Modern → category. The wheel adds pitch vibrato; LFO rates are free running. <a href="factory-presets.md">Full playing guide</a>.</footer></main><script>const cards=[...document.querySelectorAll('article')],search=document.querySelector('#search'),category=document.querySelector('#category');function filter(){const q=search.value.toLowerCase();for(const c of cards)c.hidden=Boolean(category.value&&category.value!==c.dataset.category)||!c.textContent.toLowerCase().includes(q)}search.addEventListener('input',filter);category.addEventListener('change',filter);document.addEventListener('play',e=>{if(e.target.tagName==='AUDIO')for(const a of document.querySelectorAll('audio'))if(a!==e.target)a.pause()},true);</script></html>'''
    (ROOT/'Docs/guide/modern-presets.html').write_text(page)
    manifest={'schema':'press78.modern-audio-catalog.v1','audition_results_sha256':sha(source/'results.json'),
              'builder_sha256':sha(Path(__file__)),'encoding':'160kbps stereo MP3; fixed source gain; no normalization or dynamics processing',
              'encoder':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0],
              'files':files,'catalog_sha256':sha(ROOT/'Docs/guide/modern-presets.html')}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'catalog':str(ROOT/'Docs/guide/modern-presets.html'),'audio_files':len(files),
                      'mp3_bytes':sum((ROOT/f['path']).stat().st_size for f in files)}))

if __name__=='__main__':
    main()
