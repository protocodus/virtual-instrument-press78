#!/usr/bin/env python3
"""Build a local listening page from the frozen b11 comparison receipt."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=ROOT/'Tests/results/hardware-fidelity-b11.json')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    out = (args.output or Path(report['artifact_directory'])/'audition.html').resolve()
    if out.is_relative_to(ROOT):
        assert subprocess.run(['git', 'check-ignore', '--quiet', str(out)], cwd=ROOT).returncode == 0, 'Use an ignored local artifact directory'
    out.parent.mkdir(parents=True, exist_ok=True)
    assert report['selected_model_key'] == 'lfo_only'
    assert report['selected_production_verification']['whole_wav_byte_identical']
    expected_audio = {item['file']: item for item in report['validation']['audition_validation']}
    labels = {'reference': 'Hardware recording', 'd1_old_lfo': 'Previous modulation', 'lfo_only': 'Selected b11'}
    cards, media, score_rows = [], [], []
    for audition in report['auditions']:
        patch = audition['patch']
        row = next(r for r in report['rows'] if r['patch'] == patch)
        scores = row['scores']
        score_rows.append('<tr><td>' + html.escape(audition['name'].split(' ', 2)[-1])
                          + ''.join(f'<td>{scores[key]["joint_lr_band_rmse_db"]:.3f}</td>'
                                    for key in ('d1_old_lfo', 'lfo_only')) + '</tr>')
        players = []
        for key in ('reference', 'd1_old_lfo', 'lfo_only', 'selected_three_way'):
            path = Path(audition['files'][key])
            assert path.is_file(), path
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            expected = expected_audio[str(path)]
            assert digest == expected['sha256'] and expected['finite'] and expected['peak'] <= .85
            media.append({'file': str(path), 'sha256': digest})
            src = quote(os.path.relpath(path, out.parent), safe='/')
            label = labels.get(key, 'Play in order: hardware → previous modulation → b11')
            players.append(f'<div class="player"><label>{html.escape(label)}</label><audio controls preload="none" src="{src}"></audio></div>')
        cards.append(f'<section><p class="number">PSS {patch:02d}</p><h2>{html.escape(audition["name"].split(" ", 2)[-1])}</h2>'
                     + ''.join(players) + '</section>')
    url = html.escape(report['source_recording']['url'], quote=True)
    target = report['aggregate']['targets']['scores']
    score_rows.append('<tr><td>Three-target mean</td>'
                      + ''.join(f'<td>{target[key]["joint_lr_band_rmse_db"]:.3f}</td>'
                                for key in ('d1_old_lfo', 'lfo_only')) + '</tr>')
    counts = report['all100_counts']['isolated_lfo_delta']['joint_lr_band_rmse_db']
    assert counts['equality_tolerance'] == 1e-6
    count_summary = (f'Across all {len(report["rows"])} reused windows, {counts["improved"]} improve, '
                     f'{counts["worsened"]} worsen and {counts["same"]} stay equal within 10⁻⁶ dB. '
                     f'Target log-STFT error changes {target["d1_old_lfo"]["stereo_stft_log_error_db"]:.3f}'
                     f'→{target["lfo_only"]["stereo_stft_log_error_db"]:.3f} dB; STFT convergence changes '
                     f'{target["d1_old_lfo"]["stereo_stft_convergence"]:.3f}'
                     f'→{target["lfo_only"]["stereo_stft_convergence"]:.3f}.')
    analog_worse = report['all100_counts']['isolated_analog_delta']['joint_lr_band_rmse_db']['worsened']
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Press78 b11 · Listening comparison</title><style>
*{box-sizing:border-box}body{margin:0;background:#181b1f;color:#ece9dc;font:16px/1.55 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:36px 24px}h1,h2{font-family:"DIN Condensed",system-ui,sans-serif;line-height:1.1}h1{font-size:40px;margin:0 0 12px}h2{margin:0 0 22px;font-size:28px}.eyebrow,.number{color:#67c4d0;font-weight:700;font-size:13px;letter-spacing:.1em}p{max-width:80ch;color:#c8cbc8}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin:28px 0}section{background:#292d32;border:1px solid #484f57;border-radius:10px;padding:24px}.player{margin:18px 0}label{display:block;font-size:13px;margin-bottom:8px}audio{width:100%;height:36px}a{color:#93d2dc}table{border-collapse:collapse;width:100%;margin:20px 0;font-variant-numeric:tabular-nums}td,th{text-align:left;padding:12px;border-bottom:1px solid #42484f}th{color:#b1a1d2;font-size:13px}.note{border-left:3px solid #ea8197;padding-left:16px}details{margin:24px 0}summary{cursor:pointer;color:#b1a1d2}.small{font-size:13px}footer{padding:24px 0;border-top:1px solid #42484f}
</style></head><body><main><p class="eyebrow">PROTOCODUS · PRESS78 · RESEARCH</p><h1>b11 listening comparison</h1>
<p>The selected model corrects the D1 endpoint and uses a 5.24 Hz shared triangle LFO with revised PMS depth. Compare the same performance window with the previous modulation. Operator presets, event timing and Recorded chorus stay fixed.</p>
<p class="note">These clips reuse the polyphonic PSS-780 tour with hardware effects enabled. They are level matched per stereo pair, with no phase fitting or added noise. They are diagnostic comparisons, not isolated dry-note tests or a percentage of authenticity.</p>
<div class="grid">''' + ''.join(cards) + '''</div>
<h2>Measured result</h2><p>Joint stereo spectral-band error in dB; lower is better. Small regressions remain visible.</p>
<table><thead><tr><th>Voice</th><th>Previous modulation</th><th>Selected b11</th></tr></thead><tbody>
''' + ''.join(score_rows) + '''</tbody></table>
<p>''' + html.escape(count_summary) + '''</p>
<details><summary>Rejected analog experiment and remaining gaps</summary><p>A fourfold analog implementation improves numerical agreement with the PSS-480 circuit surrogate but worsens the PSS-780 recording comparison on ''' + str(analog_worse) + '''/100 presets. It is retained for component research and is not used by the instrument. Human Voice 1's release/Reverb behavior, exact OPU timing and exact output circuit remain unresolved.</p></details>
<footer><p class="small">Reference: <a href="''' + url + '''">original PSS-780 recording</a>. Local research media only; reference audio is not bundled with the instrument. “Previous modulation” uses the D1-corrected baseline to isolate the LFO change. The final source's whole performance is byte-identical to the scored selected model.</p></footer></main></body></html>'''
    out.write_text(page)
    result = {'passed': True, 'html': str(out), 'report_sha256': hashlib.sha256(args.report.read_bytes()).hexdigest(),
              'html_sha256': hashlib.sha256(page.encode()).hexdigest(), 'audio_links': media,
              'scope': 'Local frozen-comparison player; no live browser, listening-study or new hardware measurement claim.'}
    (out.parent/'audition-page-validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'Built {out}; {len(media)} existing local audio links verified')


if __name__ == '__main__':
    main()
