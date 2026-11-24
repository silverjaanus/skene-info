from PIL import Image
import glob
fs = ['postitused/nadal-2026-11-20.jpg'] + ['postitused/nadal-2026-11-20-%d.jpg' % i for i in range(2, 11)]
ims = [Image.open(f) for f in fs]
w, h = 324, 405
sheet = Image.new('RGB', (w * 5, h * 2), 'white')
for i, im in enumerate(ims):
    sheet.paste(im.resize((w, h)), ((i % 5) * w, (i // 5) * h))
sheet.save('.swtmp/sheet.jpg', quality=80)
print('ok')
