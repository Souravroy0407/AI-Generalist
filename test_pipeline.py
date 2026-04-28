import json
from dotenv import load_dotenv
load_dotenv()

from modules.pdf_extractor import process_pdf
from modules.data_parser import parse_both_reports
from modules.llm_client import generate_ddr_content

insp_raw = process_pdf('sample_inputs/Sample Report.pdf')
therm_raw = process_pdf('sample_inputs/Thermal Images.pdf')
parsed_data = parse_both_reports(insp_raw, therm_raw)
ai_data = generate_ddr_content(parsed_data)

with open('test_output.json', 'w') as f:
    json.dump(ai_data, f, indent=2)
