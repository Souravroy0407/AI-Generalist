import json
from modules.pdf_extractor import process_pdf
raw_data, inspection_images, _ = process_pdf('sample_inputs/Sample Report.pdf')
print("Extracted filenames:")
for img in inspection_images[:10]:
    print(img["filename"])
