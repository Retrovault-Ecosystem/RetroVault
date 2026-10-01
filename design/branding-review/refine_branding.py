"""Reproducible localized branding edits, using preserved pre-edit raster sources."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def registered(image, xy, size, color):
    scale = 4
    font = ImageFont.truetype(FONT, size * scale)
    box = font.getbbox('®')
    glyph = Image.new('RGBA', (box[2]-box[0]+8, box[3]-box[1]+8))
    ImageDraw.Draw(glyph).text((4-box[0], 4-box[1]), '®', font=font, fill=color)
    glyph = glyph.resize((round(glyph.width/scale), round(glyph.height/scale)), Image.Resampling.LANCZOS)
    image.alpha_composite(glyph, xy)

def paired(image, source, box, background_y, top, bottom, height):
    x0,y0,x1,y1 = box
    strip = source.crop(box).resize((x1-x0,height), Image.Resampling.LANCZOS)
    image.paste(source.crop((x0,background_y,x1,background_y+y1-y0)), (x0,y0))
    image.paste(strip,(x0,top))
    image.paste(strip,(x0,bottom))

report = {}
previews = []
for platform in ('NES','SNES','GENESIS'):
    if platform == 'GENESIS':
        source_path = ROOT/'design/genesis-model1/Genesis_Model1_generated.png'
        target = ROOT/'design/genesis-model1/Genesis_Model1_branded.png'
    else:
        source_path = HERE/'before'/f'{platform}.png'
        target = ROOT/f'retrovault/{platform.lower()}/classic/RetroVault_{platform}_Classic_1080p.png'
    source = Image.open(source_path).convert('RGBA')
    edited = source.copy()
    if platform == 'NES':
        for box in ((618,916,787,933),(1131,916,1300,933)):
            paired(edited,source,box,940,907,929,12)
        allowed = [(618,907,787,941),(1131,907,1300,941)]
    elif platform == 'SNES':
        edited.paste(source.crop((1190,995,1213,1011)),(1166,995))
        registered(edited,(1171,991),17,(27,28,39,255))
        # Remove the generated RetroVault registered mark with adjacent housing.
        edited.paste(source.crop((1119,899,1134,917)), (1119,879))
        allowed = [(1166,988,1190,1012),(1119,879,1134,897)]
    else:
        for box in ((525,782,686,794),(987,782,1147,794)):
            paired(edited,source,box,799,772,790,10)
        registered(edited,(1035,846),17,(207,207,204,255))
        # Remove the generated RetroVault TM; keep the platform mark below.
        edited.paste(source.crop((969,769,985,784)), (953,769))
        allowed = [(525,772,686,800),(987,772,1147,800),(1035,846,1055,866),(953,769,969,784)]
    edited.putalpha(source.getchannel('A'))
    assert ImageChops.difference(source.getchannel('A'),edited.getchannel('A')).getbbox() is None
    difference = ImageChops.difference(source.convert('RGB'),edited.convert('RGB'))
    outside = difference.copy()
    draw = ImageDraw.Draw(outside)
    for box in allowed:
        draw.rectangle((box[0],box[1],box[2]-1,box[3]-1), fill=(0,0,0))
    assert outside.getbbox() is None, (platform,outside.getbbox())
    edited.save(target)
    report[platform] = {'file':str(target.relative_to(ROOT)), 'sha256':hashlib.sha256(target.read_bytes()).hexdigest(), 'changed_bounds':difference.getbbox(), 'alpha_unchanged':True, 'outside_branding_unchanged':True}
    crop = edited.crop((440,875,1465,1055) if platform=='SNES' else (575,895,1340,1020) if platform=='NES' else (500,760,1175,910))
    crop.thumbnail((1050,220))
    previews.append((platform,crop))
    if platform=='SNES':
        manifest = target.with_name('RetroVault_SNES_Classic.production.json')
        data=json.loads(manifest.read_text())
        data['sha256']['overlay_png']=report[platform]['sha256']
        data['branding_revision']={'date':'2026-09-29','change':'Bottom platform trademark symbol changed to registered mark; RetroVault legal symbol removed; purple rules and all viewport pixels preserved.'}
        manifest.write_text(json.dumps(data,indent=2)+'\n')
preview = Image.new('RGB',(1120,650),(38,38,40))
draw = ImageDraw.Draw(preview)
for index,(label,crop) in enumerate(previews):
    y=index*215
    draw.text((20,y+8),label,font=ImageFont.truetype(FONT,20),fill='white')
    preview.paste(crop,(int((1120-crop.width)/2),y+35),crop)
preview.save(HERE/'branding-comparison.png')
(HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
