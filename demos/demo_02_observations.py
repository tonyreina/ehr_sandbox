"""Demo 2: Query observations for a patient from the configured EHR."""
import os
import sys
from dotenv import load_dotenv
from ehr import ClientFactory

load_dotenv()

PATIENTS = {
    "camila":   "erXuFYUfucBZaryVksYEcMg3",
    "derrick":  "eq081-VQEgP8drUUqCWzHfw3",
    "theodore": "e63wRTbPfr1p8UW81d8Seiw3",
    "linda":    "eIXesllypH3M9tAA5WdJftQ3",
}

patient_key = sys.argv[1] if len(sys.argv) > 1 else "theodore"
category    = sys.argv[2] if len(sys.argv) > 2 else "laboratory"
patient_id  = PATIENTS.get(patient_key, patient_key)

client = ClientFactory.from_env()
obs    = client.get_observations(patient_id, category=category)

if not obs:
    print("No observations found.")
else:
    print(f"EHR: {client.ehr_name}")
    print(f"{category.capitalize()} results for {patient_key} ({patient_id}):\n")
    for o in obs:
        code  = o.get("code", {}).get("text", "Unknown")
        date  = o.get("effectiveDateTime", "")[:10]
        value = o.get("valueQuantity")
        if value:
            print(f"  {date}  {code}: {value.get('value')} {value.get('unit', '')}")
