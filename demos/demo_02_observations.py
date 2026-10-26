"""Demo 2: Query observations for a patient from the configured EHR."""
import os
import sys
from dotenv import load_dotenv
from ehr import ClientFactory
from ehr.patients import resolve

load_dotenv()

ehr_type    = os.getenv("EHR_TYPE", "epic").lower()
category    = sys.argv[2] if len(sys.argv) > 2 else "laboratory"
patient_key, patient_id = resolve(
    ehr_type, sys.argv[1] if len(sys.argv) > 1 else None, observations=True
)

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
