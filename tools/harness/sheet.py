"""Contact sheets of a movie segment: python3 sheet.py lib rom fm2 start end step out.png"""
import sys, pickle
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import rm2
from PIL import Image, ImageDraw


def contact_sheet(e, pads, start, end, step, out, cols=6, scale=1, states=None, label_fn=None):
    if states:
        k = max(s for s in states if s <= start)
        e.load(states[k])
        f = k
    else:
        e.poweron()
        f = 0
    while f < start:
        e.frame(pads[f]); f += 1
    shots = []
    while f < end:
        if (f - start) % step == 0:
            img = Image.new("RGB", (256, 240))
            img.putdata([rm2.NES_PAL[b & 0x3F] for b in e.screen()])
            d = ImageDraw.Draw(img)
            txt = str(f) + (" " + label_fn(e) if label_fn else "")
            d.rectangle([0, 0, 8 * len(txt) + 4, 12], fill=(0, 0, 0))
            d.text((2, 1), txt, fill=(255, 255, 0))
            shots.append(img)
        e.frame(pads[f] if f < len(pads) else 0); f += 1
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 256, rows * 240))
    for i, im in enumerate(shots):
        sheet.paste(im, ((i % cols) * 256, (i // cols) * 240))
    if scale != 1:
        sheet = sheet.resize((int(sheet.width * scale), int(sheet.height * scale)))
    sheet.save(out)
