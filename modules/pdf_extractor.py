import os
import hashlib
import tempfile
import pdfplumber
import fitz  # PyMuPDF
from PyPDF2 import PdfReader


def extract_text(pdf_path):
    pages = []
    fallback_reader = None

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                tables = page.extract_tables() or []
                if not text.strip():
                    if fallback_reader is None:
                        try:
                            fallback_reader = PdfReader(pdf_path)
                        except Exception:
                            pass
                    if fallback_reader and i < len(fallback_reader.pages):
                        fallback_text = fallback_reader.pages[i].extract_text() or ""
                        text = fallback_text.replace("\x00", "")

                pages.append({
                    "page_num": i + 1,
                    "text": text.strip(),
                    "tables": tables
                })
    except Exception as e:
        print(f"Failed to read {pdf_path}: {e}")
        return []

    return pages


def extract_images(pdf_path, output_dir=None):

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="ddr_images_")
    os.makedirs(output_dir, exist_ok=True)

    images = []
    seen_hashes = set()

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Can't open {pdf_path}: {e}")
        return images

    img_counter = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        img_list = page.get_images(full=True)

        for img_info in img_list:
            xref = img_info[0]
            try:
                base_img = doc.extract_image(xref)
            except Exception:
                continue

            img_bytes = base_img.get("image")
            ext = base_img.get("ext", "png")
            width = base_img.get("width", 0)
            height = base_img.get("height", 0)

            if not img_bytes:
                continue

            # skip tiny stuff — icons, bullets, decorations, small logos
            if width < 300 or height < 300:
                continue
                
            # skip logos/headers which usually have extreme aspect ratios
            aspect_ratio = width / height if height > 0 else 0
            if aspect_ratio > 2.5 or aspect_ratio < 0.4:
                continue

            # deduplicate: same image bytes = same image
            img_hash = hashlib.md5(img_bytes).hexdigest()
            if img_hash in seen_hashes:
                continue
            seen_hashes.add(img_hash)

            img_counter += 1
            filename = f"page{page_num + 1}_img{img_counter}.{ext}"
            filepath = os.path.join(output_dir, filename)

            try:
                with open(filepath, "wb") as f:
                    f.write(img_bytes)

                images.append({
                    "path": filepath,
                    "filename": filename,
                    "page_num": page_num + 1,
                    "width": width,
                    "height": height,
                    "format": ext,
                    "size_kb": round(len(img_bytes) / 1024, 1)
                })
            except Exception as e:
                print(f"Couldn't save {filename}: {e}")

    doc.close()
    return images


def process_pdf(pdf_path, image_output_dir=None):
    # Main entry point — extracts both text and images from a single PDF.
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    fname = os.path.basename(pdf_path)
    print(f"Processing: {fname}")

    text_data = extract_text(pdf_path)
    print(f"  -> Extracted text from {len(text_data)} pages")

    img_data = extract_images(pdf_path, output_dir=image_output_dir)
    print(f"  -> Extracted {len(img_data)} unique images")

    return {
        "filename": fname,
        "total_pages": len(text_data),
        "pages": text_data,
        "images": img_data,
        "full_text": "\n\n".join(p["text"] for p in text_data if p["text"])
    }


# quick sanity check
if __name__ == "__main__":
    sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_inputs")

    report_path = os.path.join(sample_dir, "Sample Report.pdf")
    thermal_path = os.path.join(sample_dir, "Thermal Images.pdf")

    print("=" * 50)
    print("Testing PDF Extractor")
    print("=" * 50)

    for label, path in [("Inspection Report", report_path), ("Thermal Report", thermal_path)]:
        if not os.path.exists(path):
            print(f"{label} not found at {path}")
            continue

        tag = "report_images" if "Sample" in path else "thermal_images"
        out_dir = os.path.join(sample_dir, "..", "output", tag)
        result = process_pdf(path, image_output_dir=out_dir)

        print(f"\n{label}:")
        print(f"  Pages: {result['total_pages']}")
        print(f"  Images: {len(result['images'])}")
        print(f"  Text length: {len(result['full_text'])} chars")
        if result["full_text"]:
            print(f"  Preview: {result['full_text'][:200]}...")
        else:
            print("  Preview: [no text extracted]")
        print()
