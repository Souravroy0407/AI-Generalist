import json

# The persona and main instructions for the LLM
SYSTEM_PROMPT = """You are an expert Building Diagnostics Engineer and Technical Report Writer.
Your job is to read raw site inspection data and thermal imaging data, and convert it into a professional, structured Detailed Diagnostic Report (DDR) for a client.

CRITICAL RULES:
1. DO NOT invent or hallucinate any facts, measurements, or observations. Only use the data provided.
2. If the provided information is conflicting (e.g., between the inspection and thermal data), explicitly mention the conflict.
3. If any required information is missing, explicitly write "Not Available".
4. Use clear, professional, client-friendly language. Avoid overly dense technical jargon where simple terms work better.
5. Structure your output EXACTLY according to the requested JSON schema.
"""

# The template for the user prompt
USER_PROMPT_TEMPLATE = """
Here is the raw data from a recent site inspection.

--- SITE DETAILS ---
{site_details}

--- IMPACTED AREAS ---
{impacted_areas}

--- CHECKLISTS ---
{checklists}

--- SUMMARY TABLE ---
{summary_table}

--- THERMAL READINGS ---
{thermal_readings}

Based on this data, generate the content for a Detailed Diagnostic Report (DDR).

Output the report strictly as a JSON object with the following keys. Do not include markdown formatting like ```json in the output, just the raw JSON object.

{{
    "property_issue_summary": "A high-level summary (1-2 paragraphs) of the overall condition of the property and the main issues found.",
    "area_wise_observations": [
        {{
            "area_name": "Name of the area (e.g., 'Area 1: Hall')",
            "observations": "Detailed description of the negative and positive observations for this area. Mention any specific temperature readings from the thermal data if they clearly correspond to this area.",
            "associated_photos": [list of photo IDs (integers) associated with this area based on the raw data]
        }}
        // ... include an entry for EVERY impacted area found in the raw data
    ],
    "probable_root_cause": "An overall assessment of the likely root causes for the observed issues (e.g., plumbing leaks, structural cracks).",
    "severity_assessment": {{
        "level": "Low, Medium, or High",
        "reasoning": "Explanation for why this severity level was chosen."
    }},
    "recommended_actions": [
        "Actionable recommendation 1",
        "Actionable recommendation 2"
        // ...
    ],
    "additional_notes": "Any other relevant observations, limitations of the inspection, or disclaimers.",
    "missing_or_unclear_information": "List any required data that was missing from the provided reports. If none, say 'None'."
}}
"""

def build_prompt(parsed_data):
    # take the parsed dicts and dump them into the prompt template
    inspection = parsed_data.get("inspection", {})
    
    # Format site details
    site_details = json.dumps(inspection.get("site_details", {}), indent=2)
    
    # Format impacted areas
    impacted_areas = json.dumps(inspection.get("impacted_areas", []), indent=2)
    
    # Format checklists
    checklists = json.dumps(inspection.get("checklists", {}), indent=2)
    
    # Format summary table
    summary_table = json.dumps(inspection.get("summary_table", []), indent=2)
    
    # Format thermal readings
    thermal_readings = json.dumps(parsed_data.get("thermal_readings", []), indent=2)

    prompt = USER_PROMPT_TEMPLATE.format(
        site_details=site_details,
        impacted_areas=impacted_areas,
        checklists=checklists,
        summary_table=summary_table,
        thermal_readings=thermal_readings
    )
    
    return prompt
