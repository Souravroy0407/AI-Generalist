import fitz

doc = fitz.open('sample_inputs/Sample Report.pdf')
c = 0
for p in doc:
    for img in p.get_images(full=True):
        b = doc.extract_image(img[0])
        w = b.get('width', 0)
        h = b.get('height', 0)
        if w >= 300 and h >= 300:
            c += 1
print('Total >=300:', c)
