# Press78 design — layout study 11

Open `index.html` directly or serve the repository and visit `/Design/index.html`. It is a self-contained interactive layout review, with 100 factory-preset previews. Preset changes update both operators, wave selections, and values. Knobs support horizontal dragging, keyboard arrows and the precise-value inspector. Front, rear and folded views use logical rack geometry.

This prototype does not produce audio. The native Reason patch selector and sockets are represented by review placeholders. Both native GUI formats use standard `jbox.patch_name` and `jbox.patch_browse_group` widgets with unchanged stock artwork. All 100 factory `.repatch` files use the `PSS` prefix; `Init.repatch` remains separate.

## Geometry and control contract

- Full panels: **754 × 552**, eight rack units of 69 pixels each.
- Folded panels: **754 × 30**.
- Front section bounds follow the photographic pockets: x=35/385, y=73/314, widths 334 and heights 224/192. Front headings and selector banks have 20 px side padding; rear sections retain 24 px. Knob rows use shared first/last centers 45 px inside each front section, including rows with three, four or five controls. Main operator knob rows use 64 px vertical pitch, modulation/output rows 66 px; waveform buttons are 67.5 px wide with 8 px gaps. Knobs and toggle caps share each row’s visual center; captions share a baseline. Rear rows use five or six columns with common outer anchors and 66 px row spacing. Full header groups share y=25 visual centers, folded elements y=15. DEVICE tape plus its caption occupy y=13–37; NOTE lamp plus its caption occupy y=13.5–37, with both caption baselines at 37. Both full-panel separator rules sit at y=49. Upper screws use symmetrical x=17/737, y=38 centers on the procedural front and rear; the generated photo places the upper screws at approximately the same coordinates, within 1 px vertically. The fixed host fold region at the upper left remains reserved.
- Schematic envelope plots were removed to give the actual envelope and key-response controls room; no uncalibrated timing display is shown.
- `geometry.json` is the layout source consumed by both native GUI pipelines. The 64 visible entries in `Resources/controls.json` are represented by `property_id`, `property_path`, API binding, range and default.
- The rear has four CV inputs (Gate, Note, FM, Level) and two audio outputs. Their exact property paths, centers and 24×24 widget bounds are included in `geometry.json`.
- Each control includes label-slot bounds, separate `widget_bounds`, and a caption baseline/font size. Knob faces are 40 × 40, with 31 px number wells and 11 px readouts; 13 px wide wedge pointers stay outside those wells, extending 4.1 px beyond the caps within 50 px transparent sprites; waveforms use four separate radio hit regions.
- The front has 34 main controls: both oscillator and envelope editors, modulation depth/rate and performance switches, chorus amount/rate/depth/width, drive, tone and output. The rear has 30 advanced options: operator key scaling, sustain release and AM/DT2, modulation setup, model selection, tuning/clock calibration, DC filtering and output protection, plus sockets.
- `default` values come from the canonical control contract, except the explicitly declared `startup_default` for Pitch model. Its preview/Init value is Original (1), while `document_default` remains Equal (0) for older patches missing the property. `preview_state` and `preview_patch=0` are the first factory preset shown in this design review; they do not silently change the device's startup contract.
- Level stores raw TL attenuation unchanged. Its displayed/edited range is 0–99: clockwise/upward means louder, `OFF` is the minimum, and display values invert `99 − TL`. Raw muted codes 99–127 survive loading, clicks and canceled gestures exactly; only an actual edit maps back through the displayed Level. The precise inspector uses the displayed Level, and tooltips explain musical behavior. Envelope rate values are rate codes, not seconds. Init and all factory patches use the Real startup profile from the canonical contract; this includes recorded chorus and 20 ppm clock drift, with controls independently editable. Additive noise is disabled.

The current visual combines YouKnow's DIN wordmark, condensed section headings, recessed groups and 2 px accent rules starting 6 px beyond measured title ink with the PSS-780 photographs supplied as a moodboard. The material is cool charcoal ABS with fine grain, shallow molded ribs and short cap shadows. Cyan identifies the modulator and modulation controls; lavender identifies the carrier; coral identifies output effects. Ivory labels and a ruby FM badge complete the palette. The ten primary envelope knobs have cyan modulator and lavender carrier faces with dark readouts. All knob pointers use ivory with a dark outline; thin cyan, lavender or coral value arcs show position. Wave buttons use centered 13 px labels. Every active button has a white face and dark text, including waveform selections and on/off switches. Inactive waveform caps retain the operator color; inactive switches stay dark.

The photos informed the palette and material only; they are not embedded or redistributed as interface assets. The default panel geometry, SVG artwork and procedural texture are generated locally. The interface uses original Press78/Protocodus branding, with no Yamaha marks, keyboard, rhythm or accompaniment controls. DIN Condensed and DIN Alternate are installed macOS rendering inputs shared with YouKnow; font binaries are not bundled. The SVG uses Arial fallback on systems without those faces, while the raster panels retain the intended typography.

The **Photorealistic** front background uses [the generated ABS faceplate](Assets/press78-photo-background-v3.png), created with the built-in image-generation tool from the current layout preview. It contains no labels or controls; the browser overlays the existing live interface. Open `index.html?material=photo` or use the Original/Photorealistic buttons to compare. The [exact prompt](Assets/press78-photo-background-v3.prompt.txt), [provenance](Assets/press78-photo-background-v3.json), and [latest composited front preview](front-photo@1x.png) and [rear preview](rear@1x.png) are saved alongside it. The native front also uses this generated plate; native labels and controls remain separate. Rear and folded assets retain the original material. The native renderer supports `--material original` as a fallback. Installed/build verification is recorded in the Rack checkout. `material-validation.json` records bitmap loading, switching and interaction checks.

## Rebuild

```sh
python3 Design/build_wireframe.py
```

This regenerates geometry, SVGs and the standalone HTML from `preview_template.html`, the current control contract and factory bank. The native GUI generator lives separately in the Rack worktree; this script does not alter native assets or DSP.

To reproduce the exact 1× raster previews with the renderer used for review:

```sh
npm install --prefix /tmp/press78-svg-render --no-audit --no-fund @resvg/resvg-js@2.6.2
PRESS78_RESVG_MODULE=/tmp/press78-svg-render/node_modules/@resvg/resvg-js node Design/render_preview.cjs
python3 Design/validate.py
```

The PNGs are raster renders of the SVG at actual logical size, not screenshots of a running Rack Extension. SDK authority was checked at `/Users/vojta/Dev/reason-rack-extension/SDK/version.txt`: `JukeboxSDK_500_028`, `TargetVersion=5.0`. The SDK5 YouKnow native GUI example was inspected for patch-widget and geometry conventions. A real Reason/Recon creation and interaction test belongs to the native integration stage.

## Validation scope

`validation.json` records exact canonical mappings, bounds, caption-width checks using DIN Alternate at 11 px, nonoverlapping widget rectangles and raster dimensions. Browser/DOM review is separately identified; it must not be mistaken for native host testing or audio behavior. The photo composition and four 1× raster panels were visually reviewed for layout study 11; these are deterministic SVG rasterizations. Older live-browser results are retained as historical records, not rerun claims. Both native GUI pipelines are regenerated and checked in the Rack checkout. Native widget coordinates are snapped to whole logical pixels using one anchor per knob; numeric readouts remain centered, and GUI2D exports use exact fivefold coordinates. The browser retains the continuous source geometry. The native renderer generates 47 read-only numeric displays and two interactive Level displays over the original raw properties. The Level gestures use documented SDK5 Lua callbacks; the independent native contract exercises 256 draw states and 322 gesture cases. Number values are not baked into knob filmstrips. Host creation and interaction evidence is recorded separately in the Rack checkout.

`interaction-validation.json` records passing synthetic DOM checks for preset 99, operator readouts, waveform state, the 34/30 front/rear allocation, panel views, chorus model choices and absent noise controls, the output-circuit toggle and preset reload. Reproduce them with:

```sh
npm install --prefix /tmp/press78-preview-test --no-audit --no-fund jsdom@30.1.3
PRESS78_JSDOM_MODULE=/tmp/press78-preview-test/node_modules/jsdom node Design/validate_interaction.cjs
```

## Modern interaction pass

Layout study 07 adds unit-bearing chorus/cutoff labels, explicit envelope rate/attenuation labels, position arcs, rear operator markers and separators, and a browser header that follows the native FM badge, stock patch group, name tape and note indicator. The empty patch recess was removed from the folded rear. The browser uses relative drag (up/right increases), Shift for fine movement, arrow keys, numeric entry and Ctrl/Cmd-click reset. Escape cancels an active browser drag. Native Level callbacks use the host’s documented fine/reset/cancel modifiers; ordinary controls retain Reason’s standard knob behavior. The native adapter declares stable automation mappings for all 65 controls, with existing CC7/74 assignments preserved.

`modern-browser-validation.json` records real Chromium pointer/keyboard checks, separately from the synthetic DOM tests. Native interaction in Reason remains a separate host-validation claim. No synthesis or raw factory parameter data changed in this UI pass.

## Layout study 08 alignment pass

The browser and native front now follow the actual molded pocket bounds, rather than the older nominal section rectangles. Controls and captions fit within those physical groups; section headings align with their content rails. Different-length knob rows keep common outer anchors. Header widgets, knob/toggle centers and caption baselines are aligned, with native rounding limited to half a logical pixel. The photo asset and 65-control contract are unchanged. `front-photo@1x.png` reproduces the browser photo-layer composition without running browser interaction; current layout and synthetic DOM checks are in `validation.json` and `interaction-validation.json`.

## Layout study 09 header pass

The header now centers each complete visible group, including DEVICE and NOTE captions. The rear uses the same separator and DEVICE group; its two-line calibration title also centers within the header. The NOTE group moves 9 px left to leave space beside the right screw. Upper screws move down symmetrically on the full front and rear; folded geometry and all sound controls remain unchanged.

The host owns the fold arrow. The [SDK 5 panel contract](https://developer.reasonstudios.com/documentation/rack-extension-sdk/5.0.0/jukebox-scripting-specification) exposes panel graphics, cable origin, options and widgets, with no fold-arrow position setting, so the artwork moves instead. `rack_hardware.host_fold_reserved_bounds` records the conservative upper-left area used for collision checks. Procedural screws do not overlap that area; image-generation coordinates are approximate, with a 1 px allowance at the vertical fold boundary. The v3 material is an image-generator edit of v2, not a pixel-identical patch; its molded pockets and header seam were visually checked against the original layout. `header_groups` records visible widget-plus-caption bounds so a centered widget cannot conceal an off-center group in validation.

## Layout study 10 fold-control clearance

The Protocodus logo and PRESS78 wordmark move together 16 logical pixels right on all four faces. The full group starts at x=44 and the folded group at x=42, leaving 17 px and 15 px respectively beyond the host fold-control reserved area. Their size, vertical position and 10 px internal gap stay unchanged. The native front Remote/automation bridge follows x=44–188 and retains all 29 visible rear property bindings; other header widgets keep their positions.

The rear control bank keeps its cyan and lavender operator bars without horizontal separators between knob rows. The header divider remains in place.

The front Noise amount knob and rear Noise model switch are removed. The three remaining front output controls and five controls in the affected rear row are evenly spaced between their original outer anchors. The two retired properties remain stored at zero only for patch and automation compatibility, without exposed widgets or additive noise.

## Layout study 11 pitch configuration

The rare Pitch model selector joins the rear configuration row, keeping 34 front controls unchanged. New Init and PSS patches select Original; old patches missing this appended property retain Equal. The selector shows the requested law, which takes effect only when all notes, release envelopes and steal fades have finished, or after reset/all-sound-off. Original device Tune rounds to 3.125-cent steps, while host tuning and internal modulation remain continuous. The recovered command lookup and MIDI bend behavior are software-verified; the downstream frequency conversion remains a behavioral model. See the [b12 comparison](../Reference/Research/hardware-pitch-b12-20261019.md). No noise control or additive noise is restored.
