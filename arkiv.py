import os
import base64
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import json
import re

def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', name)

def extract_and_export(arkivfil):
    now = datetime.now().astimezone()
    datestamp = now.strftime("%Y%m%dT%H%M%S.%f%z")  # ISO 8601 with fractional seconds before offset
    output_dir = Path(f"arkiv-{datestamp}")
    output_dir.mkdir(exist_ok=True)

    tree = ET.parse(arkivfil)
    root = tree.getroot()

    for dokument in root.findall("dokument"):
        navn_elem = dokument.find("navn")
        innhold_elem = dokument.find("innhold")

        if navn_elem is None or innhold_elem is None or not innhold_elem.text:
            print("⛔️ Hopper over dokument med manglende navn eller innhold.")
            continue

        navn = sanitize_filename(navn_elem.text)

        try:
            metadata = json.loads(innhold_elem.text)
        except json.JSONDecodeError:
            print(f"⛔️ Klarte ikke å parse JSON for dokument: {navn}")
            continue

        audio_data_uri = metadata.get("audio", "")
        match = re.match(r'data:(.*?);base64,(.*)', audio_data_uri)

        if not match:
            print(f"⛔️ Fant ikke base64-data i dokument: {navn}")
            continue

        mimetype = match.group(1)
        base64_data = match.group(2)
        file_ext = mimetype.split("/")[-1] if "/" in mimetype else "bin"

        # Lagre dekodet fil
        try:
            binary_data = base64.b64decode(base64_data)
            filepath = output_dir / f"{navn}.{file_ext}"
            with open(filepath, "wb") as f:
                f.write(binary_data)
            print(f"✅ Fil lagret: {filepath}")
        except Exception as e:
            print(f"⛔️ Feil ved lagring av {navn}: {e}")
            continue

        # Lagre metadata som JSON
        try:
            json_path = output_dir / f"{navn}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⛔️ Feil ved lagring av metadata for {navn}: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Bruk: python3 arkiv.py arkivfil.xml")
        sys.exit(1)
    
    arkivfil = sys.argv[1]
    extract_and_export(arkivfil)
