// Rasterize reviewed SVG geometry at exactly 1x. No browser/audio is emulated.
const fs=require('fs'),path=require('path');
const {Resvg}=require(process.env.PRESS78_RESVG_MODULE || '@resvg/resvg-js');
for(const name of ['front','rear','folded-front','folded-rear']) {
 const input=fs.readFileSync(path.join(__dirname,name+'.svg'));
 const renderer=new Resvg(input,{font:{loadSystemFonts:true,fontFiles:['/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf','/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf'],defaultFontFamily:'DIN Alternate'}});
 fs.writeFileSync(path.join(__dirname,name+'@1x.png'),renderer.render().asPng());
}
console.log('Rendered front/rear/folded SVGs at logical 1x dimensions.');

// Mirror the browser's photo layer and material-surface visibility at1x.
// Read the selected generated material; code-native labels/widgets overlay it.
const geometry=JSON.parse(fs.readFileSync(path.join(__dirname,'geometry.json'),'utf8'));
const photo=fs.readFileSync(path.join(__dirname,geometry.material_bounds.photo_asset)).toString('base64');
const photoSvg=fs.readFileSync(path.join(__dirname,'front.svg'),'utf8').replace('</defs>','</defs><style>.material-surface{visibility:hidden}</style><image x="0" y="0" width="'+geometry.logical_size.width+'" height="'+geometry.logical_size.height+'" preserveAspectRatio="none" href="data:image/png;base64,'+photo+'"/>');
const photoRenderer=new Resvg(photoSvg,{font:{loadSystemFonts:true,fontFiles:['/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf','/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf'],defaultFontFamily:'DIN Alternate'}});
fs.writeFileSync(path.join(__dirname,'front-photo@1x.png'),photoRenderer.render().asPng());
console.log('Rendered selected photo material plus code-native overlays at1x.');
