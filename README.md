# 🏗️ DDR Report Generator — AI-Powered Building Diagnostic Reports

An AI system that reads raw site inspection documents (Inspection Report + Thermal Images) and generates a structured, client-ready **DDR (Detailed Diagnostic Report)**.

## 🎯 What It Does

- **Extracts** text and images from inspection PDFs and thermal scan reports
- **Analyzes** data using Google Gemini 2.5 Flash (multimodal LLM)
- **Generates** a professional DDR PDF with:
  1. Property Issue Summary
  2. Area-wise Observations (with images)
  3. Probable Root Cause
  4. Severity Assessment
  5. Recommended Actions
  6. Additional Notes
  7. Missing/Unclear Information

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Gemini API Key

### Installation

```bash
# Clone the repo
git clone <your-repo-url>
cd "AI Generalist"

# Install dependencies
pip install -r requirements.txt

# Set up environment
# Create a .env file with your Gemini API key:
# GEMINI_API_KEY=your_key_here
```

### Run Locally

```bash
streamlit run app.py
```

### Usage
1. Upload the **Inspection Report PDF**
2. Upload the **Thermal Images PDF**
3. Click **"Generate DDR Report"**
4. Download the generated DDR PDF

## 🏛️ Architecture

```
Upload PDFs → Extract Text & Images → Parse Structured Data
    → Gemini 2.5 Flash (Multimodal Analysis) → Generate DDR PDF
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Google Gemini 2.5 Flash |
| PDF Extraction | pdfplumber + PyMuPDF |
| Report Generation | FPDF2 |
| Frontend | Streamlit |
| Deployment | Streamlit Cloud |

## 📂 Project Structure

```
├── app.py                    # Streamlit main app
├── requirements.txt          # Dependencies
├── modules/
│   ├── pdf_extractor.py      # Text + image extraction
│   ├── data_parser.py        # Structured data parsing
│   ├── gemini_client.py      # Gemini API integration
│   ├── report_generator.py   # DDR PDF assembly
│   └── prompts.py            # LLM prompt templates
├── templates/
│   └── ddr_template.py       # PDF styling config
├── sample_inputs/            # Sample PDFs for demo
└── output/                   # Generated reports
```

## ⚠️ Important Rules
- Does NOT invent facts not present in documents
- Mentions conflicts when information disagrees
- Writes "Not Available" for missing information
- Uses simple, client-friendly language
- Generalizes to work on similar inspection reports

## 📹 Demo Video
[Loom Video Link — Coming Soon]

## 👤 Author
[Your Name]
