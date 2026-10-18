"""Build a local audition page from the generated circuit-noise manifest."""
from pathlib import Path
import argparse
import html
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=ROOT/'build/noise-demos')
    args = parser.parse_args()
    manifest = json.loads((args.directory/'manifest.json').read_text())
    rows = manifest['rows']

    def player(row, label):
        name = html.escape(row['file'], quote=True)
        assert (args.directory/row['file']).is_file()
        return f'<div><p>{html.escape(label)}</p><audio controls preload="metadata" src="{name}"></audio></div>'

    cards = []
    for number in (65, 93, 97):
        pair = [r for r in rows if r['file'].startswith(str(number)+'-')]
        assert len(pair) == 2
        cards.append('<article><h2>'+html.escape(pair[0]['voice'])+'</h2>'+
                     player(pair[0], 'No added noise')+player(pair[1], 'Circuit noise · level 0.002')+'</article>')
    cards.append('<article><h2>Noise alone</h2>'+player(rows[-2], 'Same native level')+
                 player(rows[-1], 'Same waveform · fixed +20 dB audition gain')+'</article>')
    spectrum = '<figure><img src="circuit-noise-spectrum.png" alt="PSS-480 circuit noise spectrum and interchannel correlation"><figcaption>Electrical circuit prediction. Digital curves retain bilinear high-frequency warping; no per-rate gain correction.</figcaption></figure>' if (args.directory/'circuit-noise-spectrum.png').is_file() else ''
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Press78 · Circuit noise auditions</title><style>
body{margin:0;background:#20292b;color:#eeeadd;font:16px/1.55 system-ui,sans-serif}main{max-width:1120px;margin:48px auto;padding:0 24px}h1{font-size:clamp(28px,4vw,46px);line-height:1.1}h2{font-size:22px}p{max-width:85ch}a{color:#79c5b7}.eyebrow{color:#79c5b7;letter-spacing:.13em;font-size:12px;font-weight:700}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;margin:28px 0}article{background:#2c373a;border:1px solid #465254;padding:22px;border-radius:8px}audio{width:100%}figure{margin:32px 0}img{max-width:100%;height:auto}figcaption,footer{color:#bbc7c5;font-size:14px}.note{border-left:3px solid #d2ad64;padding:12px 18px;background:#293335}
</style><main><div class="eyebrow">PRESS78 · RELATED CIRCUIT MODEL</div><h1>Output noise, with its stereo character intact</h1>
<p>These synthetic auditions compare the same three-second MIDI 60 note, velocity 100, followed by its release. Each pair uses the same voice, output circuit and master gain. Chorus is off. No file is loudness-normalized.</p>
<p class="note">This is the PSS-480 sibling resistor/opamp model. The source is 300 K thermal noise and a declared white opamp-noise scenario. It is not a measurement of PSS-780 hiss, its DAC or BBD. The selected level is an audition setting.</p>
<div class="grid">CARDS</div>
<p>The Noise control scales the electrical output against one fixed 11.96866768 µVrms continuous 20–20 kHz reference. At 48 kHz, numerical frequency warping gives about 0.9228 times that in-band level, before the 0.25 master gain. It is not corrected per clip or sample rate. Shared and private circuit noise sources preserve the modeled relationship between left and right.</p>
SPECTRUM
<footer><a href="manifest.json">Exact render settings, levels and source hashes</a> · <a href="../../Reference/Research/hardware-pass-20261018.md">Circuit research</a><p>The boosted noise-only file is exactly ten times the quiet waveform. All other files retain native output level. Reference recordings are not used in these auditions.</p></footer></main></html>'''
    (args.directory/'report.html').write_text(page.replace('CARDS', ''.join(cards)).replace('SPECTRUM', spectrum))
    print(args.directory/'report.html')


if __name__ == '__main__':
    main()
