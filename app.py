import os
import shutil
import tempfile
import streamlit as st

# Import our custom modules
from modules.pdf_extractor import process_pdf
from modules.data_parser import parse_both_reports
from modules.llm_client import generate_ddr_content
from modules.report_generator import generate_pdf

# UI config
st.set_page_config(
    page_title="DDR Generator",
    page_icon="🏢",
    layout="centered"
)

# custom css for a cleaner look
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #2980b9;
        font-weight: 700;
        margin-bottom: 0rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #7f8c8d;
        margin-bottom: 2rem;
    }
    .success-text {
        color: #27ae60;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">DDR Report Generator</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Automated Diagnostic Reporting</p>', unsafe_allow_html=True)

with st.expander("How to use", expanded=False):
    st.write("""
    1. Upload the Site Inspection Report (PDF)
    2. Upload the Thermal Images document (PDF)
    3. Click Generate DDR
    """)

# file uploads
st.markdown("### Upload Documents")
col1, col2 = st.columns(2)

with col1:
    inspection_pdf = st.file_uploader("Site Inspection Report", type=["pdf"])
with col2:
    thermal_pdf = st.file_uploader("Thermal Images Report", type=["pdf"])

if st.button("Generate DDR", type="primary", use_container_width=True):
    if not inspection_pdf or not thermal_pdf:
        st.error("Please upload both PDFs before generating.")
    else:
        # work inside a temp dir to avoid leaving files around
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                insp_path = os.path.join(temp_dir, "inspection.pdf")
                therm_path = os.path.join(temp_dir, "thermal.pdf")
                
                with open(insp_path, "wb") as f:
                    f.write(inspection_pdf.getbuffer())
                with open(therm_path, "wb") as f:
                    f.write(thermal_pdf.getbuffer())
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.info("Extracting data from PDFs...")
                out_dir = os.path.join(temp_dir, "output")
                os.makedirs(out_dir, exist_ok=True)
                
                insp_raw = process_pdf(insp_path, image_output_dir=os.path.join(out_dir, "report_images"))
                progress_bar.progress(20)
                
                therm_raw = process_pdf(therm_path, image_output_dir=os.path.join(out_dir, "thermal_images"))
                progress_bar.progress(40)
                
                status_text.info("Structuring diagnostic data...")
                parsed_data = parse_both_reports(insp_raw, therm_raw)
                progress_bar.progress(55)
                
                status_text.info("AI analyzing findings and generating report...")
                ai_data = generate_ddr_content(parsed_data)
                progress_bar.progress(85)
                
                status_text.info("Formatting final PDF document...")
                final_pdf_path = os.path.join(temp_dir, "Detailed_Diagnostic_Report.pdf")
                generate_pdf(ai_data, parsed_data, final_pdf_path)
                progress_bar.progress(100)
                
                status_text.success("DDR Successfully Generated!")
                
                with open(final_pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_file,
                        file_name="DDR_Generated_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
            except Exception as e:
                st.error(f"Error during processing: {str(e)}")
                progress_bar.empty()
