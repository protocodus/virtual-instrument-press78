// Rasterize reviewed SVG geometry at exactly 1x. No browser/audio is emulated.
const fs=require('fs'),path=require('path');
const {Resvg}=require(process.env.PRESS78_RESVG_MODULE || '@resvg/resvg-js');
for(const name of ['front','rear','folded-front','folded-rear']) {
 const input=fs.readFileSync(path.join(__dirname,name+'.svg'));
 const renderer=new Resvg(input,{font:{loadSystemFonts:true,fontFiles:['/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf','/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf'],defaultFontFamily:'DIN Alternate'}});
 fs.writeFileSync(path.join(__dirname,name+'@1x.png'),renderer.render().asPng());
}
console.log('Rendered front/rear/folded SVGs at logical 1x dimensions.');
