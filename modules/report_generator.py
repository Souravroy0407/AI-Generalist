import os
from fpdf import FPDF
from datetime import datetime

class DDRReport(FPDF):
    """
    Custom PDF class using FPDF2 to generate a professional 
    Detailed Diagnostic Report (DDR).
    """
    def __init__(self):
        super().__init__()
        # Set up some standard fonts and colors
        self.set_auto_page_break(auto=True, margin=15)
        self.brand_color = (41, 128, 185) # A nice professional blue
        self.base_text_color = (50, 50, 50)
        self.light_gray = (240, 240, 240)

    def header(self):
        # We don't want a header on the very first page (title page)
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*self.brand_color)
            self.cell(0, 10, "Detailed Diagnostic Report (DDR)", border=False, align="L")
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"Page {self.page_no()}", border=False, align="R", new_x="LMARGIN", new_y="NEXT")
            self.line(10, 20, 200, 20)
            self.ln(5)

    def footer(self):
        # We don't want a footer on the title page
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, "AI-Generated Diagnostic Report - Confidential", align="C")

    def _add_section_title(self, title):
        """Helper to print consistent section headers."""
        self.ln(10)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*self.brand_color)
        self.cell(0, 10, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*self.base_text_color)
        self.ln(2)

    def _add_paragraph(self, text):
        """Helper to print normal paragraph text."""
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*self.base_text_color)
        self.multi_cell(0, 6, text)
        self.ln(4)

    def create_title_page(self, site_details):
        """Generates the clean, professional cover page."""
        self.add_page()
        
        # Big title
        self.ln(50)
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(*self.brand_color)
        self.cell(0, 15, "DETAILED DIAGNOSTIC REPORT", align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("Helvetica", "", 14)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "Site Inspection & Thermal Analysis", align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.ln(30)
        
        # Site details box
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.base_text_color)
        
        details = [
            f"Customer Name: {site_details.get('customer_name', 'N/A')}",
            f"Property Type: {site_details.get('property_type', 'N/A')}",
            f"Inspection Date: {site_details.get('inspection_date', 'N/A')}",
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Inspected By: {site_details.get('inspected_by', 'N/A')}"
        ]
        
        # Center the details block roughly
        for line in details:
            self.set_x(60)
            self.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")

    def build_report(self, ai_data, parsed_data, output_path):
        site_details = parsed_data.get("inspection", {}).get("site_details", {})
        self.create_title_page(site_details)
        
        self.add_page()
        self._add_section_title("1. Executive Summary")
        self._add_paragraph(ai_data.get("property_issue_summary", "No summary provided."))

        severity = ai_data.get("severity_assessment", {})
        level = severity.get("level", "Unknown").upper()
        
        self.ln(5)
        self.set_font("Helvetica", "B", 12)
        
        if level == "HIGH":
            self.set_fill_color(255, 200, 200)
        elif level == "MEDIUM":
            self.set_fill_color(255, 235, 190)
        else:
            self.set_fill_color(200, 255, 200)
            
        self.cell(0, 10, f" OVERALL SEVERITY: {level} ", fill=True, new_x="LMARGIN", new_y="NEXT")
        self._add_paragraph(severity.get("reasoning", ""))

        self._add_section_title("2. Probable Root Cause")
        self._add_paragraph(ai_data.get("probable_root_cause", ""))
        
        self._add_section_title("3. Recommended Actions")
        actions = ai_data.get("recommended_actions", [])
        self.set_font("Helvetica", "", 11)
        for i, action in enumerate(actions, 1):
            self.multi_cell(0, 6, f"  {i}. {action}")
            self.ln(2)

        self.add_page()
        self._add_section_title("4. Area-Wise Observations")
        
        inspection_images = parsed_data.get("inspection_images", [])
        
        for area in ai_data.get("area_wise_observations", []):
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(0, 0, 0)
            self.cell(0, 8, area.get("area_name", "Unknown Area"), new_x="LMARGIN", new_y="NEXT")
            
            self._add_paragraph(area.get("observations", ""))
            
            photo_ids = area.get("associated_photos", [])
            if photo_ids:
                valid_paths = []
                for pid in photo_ids[:3]:
                    matched_img = next((img["path"] for img in inspection_images if f"img{pid}." in img["filename"]), None)
                    if matched_img and os.path.exists(matched_img):
                        valid_paths.append(matched_img)
                
                if valid_paths:
                    from PIL import Image
                    self.ln(2)
                    img_w = 50
                    start_x = self.get_x()
                    curr_y = self.get_y()
                    
                    max_h = 0
                    calculated_heights = []
                    for img_path in valid_paths:
                        try:
                            with Image.open(img_path) as pil_img:
                                ratio = pil_img.height / pil_img.width
                                h = img_w * ratio
                                calculated_heights.append(h)
                                max_h = max(max_h, h)
                        except Exception:
                            calculated_heights.append(img_w * 0.75)
                            max_h = max(max_h, img_w * 0.75)
                            
                    if curr_y + max_h > self.page_break_trigger:
                        self.add_page()
                        curr_y = self.get_y()
                        
                    for idx, img_path in enumerate(valid_paths):
                        try:
                            x_pos = start_x + (idx * (img_w + 5))
                            self.image(img_path, x=x_pos, y=curr_y, w=img_w)
                        except Exception as e:
                            print(f"Error adding image {img_path}: {e}")
                            
                    self.set_y(curr_y + max_h + 10)
            
            self.ln(5)

        self.add_page()
        self._add_section_title("5. Additional Notes & Disclaimers")
        self._add_paragraph(ai_data.get("additional_notes", ""))
        
        missing = ai_data.get("missing_or_unclear_information", "")
        if missing and missing.lower() != "none":
            self.set_font("Helvetica", "B", 11)
            self.cell(0, 8, "Missing Information Noted:", new_x="LMARGIN", new_y="NEXT")
            self._add_paragraph(missing)

        self.output(output_path)
        print(f"PDF successfully generated at: {output_path}")
        return output_path


def generate_pdf(ai_data, parsed_data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    pdf = DDRReport()
    try:
        return pdf.build_report(ai_data, parsed_data, output_path)
    except Exception as e:
        print(f"PDF generation failed: {e}")
        raise e


# quick test
if __name__ == "__main__":
    import json
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from modules.pdf_extractor import process_pdf
    from modules.data_parser import parse_both_reports
    
    print("=" * 50)
    print("Testing Report Generator")
    print("=" * 50)
    
    sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_inputs")
    out_dir = os.path.join(sample_dir, "..", "output")
    report_path = os.path.join(sample_dir, "Sample Report.pdf")
    thermal_path = os.path.join(sample_dir, "Thermal Images.pdf")
    
    # 1. Get raw data
    print("Extracting...")
    r_raw = process_pdf(report_path, image_output_dir=os.path.join(out_dir, "report_images"))
    t_raw = process_pdf(thermal_path, image_output_dir=os.path.join(out_dir, "thermal_images"))
    parsed = parse_both_reports(r_raw, t_raw)
    
    # 2. Mock AI Data (so we don't have to hit the API just to test the PDF layout)
    mock_ai_data = {
        "property_issue_summary": "Extensive dampness and leakage issues were identified across multiple areas of Flat 103, particularly in the hall, bedrooms, and parking area below. Thermal imaging confirmed significant moisture presence.",
        "area_wise_observations": [
            {
                "area_name": "Area 1: Hall",
                "observations": "Dampness observed at the skirting level. This correlates with hollowness found in adjacent tile joints. Thermal scans showed a 5.4 degree differential.",
                "associated_photos": [1, 2, 3]
            },
            {
                "area_name": "Area 6: Parking Area",
                "observations": "Seepage clearly visible in the parking ceiling directly below Flat 103's common bathroom, indicating a plumbing failure above.",
                "associated_photos": [49, 50]
            }
        ],
        "probable_root_cause": "Concealed plumbing leaks in the bathrooms combined with degraded tile grout and damaged nahani traps are allowing water to migrate into the structural elements.",
        "severity_assessment": {
            "level": "High",
            "reasoning": "Active water ingress affecting multiple rooms and the floor below poses a risk to structural integrity and indoor air quality."
        },
        "recommended_actions": [
            "Immediate pressure testing of concealed plumbing in both bathrooms.",
            "Regrouting of all bathroom floor tiles.",
            "Repairing or replacing damaged nahani traps."
        ],
        "additional_notes": "Inspection was limited to visual and thermal non-destructive methods.",
        "missing_or_unclear_information": "Customer contact details were missing."
    }
    
    # 3. Generate PDF
    print("Generating PDF...")
    final_pdf_path = os.path.join(out_dir, "Final_DDR_Report.pdf")
    generate_pdf(mock_ai_data, parsed, final_pdf_path)
