import re
import os


def parse_inspection_report(pages_data):
    # parse the raw text from pdf_extractor into structured dicts
    result = {
        "site_details": {},
        "impacted_areas": [],
        "checklists": {},
        "summary_table": [],
        "photo_refs": []
    }

    full_text = "\n".join(p["text"] for p in pages_data if p["text"])

    # pull different sections
    result["site_details"] = _parse_site_details(full_text)
    result["impacted_areas"] = _parse_impacted_areas(full_text)
    result["checklists"] = _parse_checklists(full_text)
    result["summary_table"] = _parse_summary_table(pages_data)
    result["photo_refs"] = _find_photo_refs(full_text)

    return result


def _parse_site_details(text):
    """Grab property info from the first page."""
    details = {}

    patterns = {
        "property_type": r"Property\s+Type:\s*(.+?)(?:\n|$)",
        "floors": r"Floors:\s*(\d+)",
        "property_age": r"Property\s+Age\s*\(In years\):\s*(.+?)(?:\n|$)",
        "inspection_date": r"Inspection\s+Date\s+and\s+Time:\s*(.+?)(?:\n|$)",
        "inspected_by": r"Inspected\s+By:\s*(.+?)(?:\n|$)",
        "score": r"Score\s+([\d.]+%)",
        "flagged_items": r"Flagged\s+items\s+(\d+)",
        "previous_audit": r"Previous\s+Structural\s+audit\s+done\s+(Yes|No)",
        "previous_repair": r"Previous\s+Repair\s+work\s+done\s+(Yes|No)",
        "customer_name": r"Customer\s+Name\s+(.+?)(?:\n|Mobile)",
        "mobile": r"Mobile:\s*(.+?)(?:\n|$)",
        "email": r"Email:\s*(.+?)(?:\n|$)",
        "address": r"Address:\s*(.+?)(?:\n|Property)",
    }

    for key, pat in patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            details[key] = val if val else "Not Available"
        else:
            details[key] = "Not Available"

    # impacted rooms — appears as a list after "Impacted Areas/Rooms"
    rooms_match = re.search(
        r"Impacted\s+Areas/Rooms\s+(.+?)(?=Impacted\s+Area\s+\d|$)",
        text, re.DOTALL | re.IGNORECASE
    )
    if rooms_match:
        rooms_raw = rooms_match.group(1).strip()
        # clean up newlines and extra whitespace
        rooms = [r.strip() for r in re.split(r"[,\n]+", rooms_raw) if r.strip()]
        details["impacted_rooms"] = rooms
    else:
        details["impacted_rooms"] = []

    return details


def _parse_impacted_areas(text):
    """
    Each impacted area has a negative side (the problem) and
    positive side (the source/cause). Pull them all out.
    """
    areas = []

    # split on "Impacted Area N" headers
    chunks = re.split(r"Impacted\s+Area\s+(\d+)", text, flags=re.IGNORECASE)

    i = 1
    while i < len(chunks) - 1:
        area_num = chunks[i].strip()
        area_text = chunks[i + 1]

        area = {
            "area_number": int(area_num),
            "negative_side": {},
            "positive_side": {}
        }

        # negative description — everything between "Description" and "photographs"
        neg_desc = re.search(
            r"Negative\s+side\s+Description\s+(.*?)(?=Negative\s+side\s+photograph)",
            area_text, re.DOTALL | re.IGNORECASE
        )
        if neg_desc:
            desc = re.sub(r"\s+", " ", neg_desc.group(1)).strip()
            area["negative_side"]["description"] = desc

        # negative side photos
        neg_photos_section = re.search(
            r"Negative\s+side\s+photographs?(.*?)(?=Positive\s+side\s+Description|Positive\s+side\s+photograph|$)",
            area_text, re.DOTALL | re.IGNORECASE
        )
        if neg_photos_section:
            photos = re.findall(r"Photo\s+(\d+)", neg_photos_section.group(1))
            area["negative_side"]["photos"] = [int(p) for p in photos]

        # positive description
        pos_desc = re.search(
            r"Positive\s+side?\s+Description\s+(.*?)(?=Positive\s+side\s+photograph)",
            area_text, re.DOTALL | re.IGNORECASE
        )
        if pos_desc:
            desc = re.sub(r"\s+", " ", pos_desc.group(1)).strip()
            area["positive_side"]["description"] = desc

        # positive side photos — stop before any checklist/appendix/next-area text
        pos_photos_section = re.search(
            r"Positive\s+side\s+photographs?(.*?)(?=Checklist|Appendix|Inspection\s+Checklists|SUMMARY|$)",
            area_text, re.DOTALL | re.IGNORECASE
        )
        if pos_photos_section:
            photos = re.findall(r"Photo\s+(\d+)", pos_photos_section.group(1))
            # safety cap — no single area should have 15+ positive side photos
            area["positive_side"]["photos"] = [int(p) for p in photos[:15]]

        areas.append(area)
        i += 2

    return areas


def _parse_checklists(text):
    """
    Pull out the checklist findings — WC, External Wall, Structural, etc.
    These are key-value pairs like "Leakage due to concealed plumbing  Yes"
    """
    checklists = {}

    # grab individual checklist items as key-value pairs
    # the format is roughly: "Some condition description   Value"
    checklist_items = [
        ("leakage_adjacent_walls", r"Condition\s+of\s+leakage\s+at\s+adjacent\s+walls\s+(.+?)(?:\n|$)"),
        ("leakage_below_wc", r"Condition\s+of\s+leakage\s+below\s+WC\s+(.+?)(?:\n|$)"),
        ("leakage_timing", r"Leakage\s+during:\s+(.+?)(?:\n|$)"),
        ("concealed_plumbing_leak", r"Leakage\s+due\s+to\s+concealed\s+plumbing\s+(.+?)(?:\n|$)"),
        ("nahani_trap_damage", r"Leakage\s+due\s+to\s+damage\s+in\s+Nahani\s+trap.*?(\w+)\s*$"),
        ("tile_joint_gaps", r"Gaps.*?tile\s+joints\s+(.+?)(?:\n|$)"),
        ("nahani_trap_joints", r"Gaps\s+around\s+Nahani\s+Trap\s+Joints\s+(.+?)(?:\n|$)"),
        ("tiles_broken", r"Tiles\s+Broken.*?(\w+)\s*$"),
        ("loose_plumbing_joints", r"Loose\s+Plumbing\s+joints.*?(\w+)\s*(?:\n|$)"),
        ("rcc_cracks", r"Condition\s+of\s+cracks.*?RCC.*?(\w+)\s*$"),
        ("external_cracks", r"any\s+major\s+or\s+minor\s+cracks.*?external.*?(\w+)\s*$"),
        ("algae_fungus", r"Algae\s+fungus.*?(\w+)\s*$"),
        ("leakage_interior", r"Condition\s+of\s+leakage\s+at\s+interior\s+side\s+(.+?)(?:\n|$)"),
        ("internal_wc_leakage", r"Internal\s+WC.*?leakage\s+observed\s+(.+?)(?:\n|$)"),
        ("ac_frame_condition", r"Condition\s+of\s+wall\s+mounted\s+AC.*?(\w+)\s*$"),
    ]

    for key, pattern in checklist_items:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            val = m.group(1).strip()
            checklists[key] = val
        else:
            checklists[key] = "Not Available"

    return checklists


def _parse_summary_table(pages_data):
    """
    The summary table maps negative side observations to positive side observations.
    Usually on page 10 (the table with Point No columns).
    """
    entries = []

    # look for the summary table page — it has "SUMMARY TABLE" or "Point No"
    for page in pages_data:
        txt = page["text"]
        if "SUMMARY TABLE" not in txt and "Point" not in txt:
            continue
        if "Impacted area" not in txt and "Exposed area" not in txt:
            continue

        # try to grab from extracted tables first (pdfplumber is good at this)
        if page.get("tables"):
            for table in page["tables"]:
                for row in table:
                    if not row or len(row) < 4:
                        continue
                    # skip header rows
                    if row[0] and "Point" in str(row[0]):
                        continue
                    entry = {
                        "point_no": str(row[0] or "").strip(),
                        "negative_observation": str(row[1] or "").strip(),
                        "positive_point_no": str(row[2] or "").strip(),
                        "positive_observation": str(row[3] or "").strip()
                    }
                    if entry["negative_observation"]:
                        entries.append(entry)

        # fallback: parse from raw text if tables didn't work
        if not entries:
            lines = txt.split("\n")
            for line in lines:
                # look for numbered entries like "1 Observed dampness..."
                m = re.match(r"(\d+)\s+(.+)", line.strip())
                if m and "Observed" in m.group(2):
                    entries.append({
                        "point_no": m.group(1),
                        "observation": m.group(2).strip()
                    })

    return entries


def _find_photo_refs(text):
    """Find all photo references mentioned in the text."""
    photos = re.findall(r"Photo\s+(\d+)", text)
    return sorted(set(int(p) for p in photos))


# ============================================================
# Thermal report parser
# ============================================================

def parse_thermal_report(pages_data):
    """
    Each page of the thermal report has one thermal image with readings.
    Parse out the temperature data from each page.
    """
    readings = []

    for page in pages_data:
        txt = page["text"]
        if not txt:
            continue

        reading = {"page_num": page["page_num"]}

        # hotspot temperature
        m = re.search(r"Hotspot\s*:\s*([\d.]+)\s*°C", txt)
        if m:
            reading["hotspot_c"] = float(m.group(1))

        # coldspot temperature
        m = re.search(r"Coldspot\s*:\s*([\d.]+)\s*°C", txt)
        if m:
            reading["coldspot_c"] = float(m.group(1))

        # emissivity
        m = re.search(r"Emissivity\s*:\s*([\d.]+)", txt)
        if m:
            reading["emissivity"] = float(m.group(1))

        # reflected temperature
        m = re.search(r"Reflected\s+temperature\s*:\s*([\d.]+)\s*°C", txt)
        if m:
            reading["reflected_temp_c"] = float(m.group(1))

        # thermal image filename
        m = re.search(r"Thermal\s+image\s*:\s*(\S+\.JPG)", txt, re.IGNORECASE)
        if m:
            reading["image_file"] = m.group(1)

        # device info
        m = re.search(r"Device\s*:\s*(.+?)(?:Serial|$)", txt)
        if m:
            reading["device"] = m.group(1).strip()

        # serial number
        m = re.search(r"Serial\s+Number\s*:\s*(\S+)", txt)
        if m:
            reading["serial_number"] = m.group(1)

        # date
        m = re.search(r"(\d{2}/\d{2}/\d{2})", txt)
        if m:
            reading["date"] = m.group(1)

        # calculate temperature difference (useful for severity)
        if "hotspot_c" in reading and "coldspot_c" in reading:
            reading["temp_diff_c"] = round(reading["hotspot_c"] - reading["coldspot_c"], 1)

        # only add if we actually got meaningful data
        if "hotspot_c" in reading:
            readings.append(reading)

    return readings


def parse_both_reports(inspection_data, thermal_data):
    """
    Convenience function — parse both reports and bundle the results.
    inspection_data and thermal_data are the output of process_pdf().
    """
    inspection = parse_inspection_report(inspection_data["pages"])
    thermal = parse_thermal_report(thermal_data["pages"])

    return {
        "inspection": inspection,
        "thermal_readings": thermal,
        "inspection_images": inspection_data["images"],
        "thermal_images": thermal_data["images"],
        "stats": {
            "total_impacted_areas": len(inspection["impacted_areas"]),
            "total_thermal_readings": len(thermal),
            "total_inspection_images": len(inspection_data["images"]),
            "total_thermal_images": len(thermal_data["images"]),
            "photos_referenced": len(inspection["photo_refs"]),
        }
    }


# quick test
if __name__ == "__main__":
    import json
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from modules.pdf_extractor import process_pdf

    sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_inputs")
    report_path = os.path.join(sample_dir, "Sample Report.pdf")
    thermal_path = os.path.join(sample_dir, "Thermal Images.pdf")

    print("=" * 50)
    print("Testing Data Parser")
    print("=" * 50)

    report_raw = process_pdf(report_path)
    thermal_raw = process_pdf(thermal_path)

    parsed = parse_both_reports(report_raw, thermal_raw)

    # show site details
    print("\n--- Site Details ---")
    for k, v in parsed["inspection"]["site_details"].items():
        print(f"  {k}: {v}")

    # show impacted areas
    print(f"\n--- Impacted Areas ({len(parsed['inspection']['impacted_areas'])}) ---")
    for area in parsed["inspection"]["impacted_areas"]:
        neg = area["negative_side"].get("description", "N/A")
        pos = area["positive_side"].get("description", "N/A")
        neg_photos = area["negative_side"].get("photos", [])
        pos_photos = area["positive_side"].get("photos", [])
        print(f"  Area {area['area_number']}:")
        print(f"    Problem: {neg}")
        print(f"    Photos: {neg_photos}")
        print(f"    Source: {pos}")
        print(f"    Photos: {pos_photos}")

    # show checklists
    print("\n--- Checklists ---")
    for k, v in parsed["inspection"]["checklists"].items():
        print(f"  {k}: {v}")

    # show summary table
    print(f"\n--- Summary Table ({len(parsed['inspection']['summary_table'])}) ---")
    for entry in parsed["inspection"]["summary_table"]:
        print(f"  {entry}")

    # show thermal readings
    print(f"\n--- Thermal Readings ({len(parsed['thermal_readings'])}) ---")
    for r in parsed["thermal_readings"][:3]:
        print(f"  Page {r['page_num']}: {r.get('hotspot_c')}°C / {r.get('coldspot_c')}°C "
              f"(diff: {r.get('temp_diff_c')}°C) - {r.get('image_file', 'N/A')}")
    if len(parsed["thermal_readings"]) > 3:
        print(f"  ... and {len(parsed['thermal_readings']) - 3} more")

    # stats
    print(f"\n--- Stats ---")
    for k, v in parsed["stats"].items():
        print(f"  {k}: {v}")
