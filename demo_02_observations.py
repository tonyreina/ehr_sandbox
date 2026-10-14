"""Demo 2: Query lab observations for a patient from the Epic sandbox."""
import os
import sys
from dotenv import load_dotenv
from epic_auth import authed_session

load_dotenv()

FHIR_BASE = os.getenv('EPIC_FHIR_BASE')

PATIENTS = {
    'theodore': 'e63wRTbPfr1p8UW81d8Seiw3',
    'derrick':  'eq081-VQEgP8drUUqCWzHfw3',
    'camila':   'erXuFYUfucBZaryVksYEcMg3',
    'linda':    'eIXesllypH3M9tAA5WdJftQ3',
}

patient_id = PATIENTS.get(sys.argv[1]) if len(sys.argv) > 1 else PATIENTS['theodore']

session  = authed_session()
response = session.get(f"{FHIR_BASE}/Observation", params={
    'patient':  patient_id,
    'category': 'laboratory',
    '_sort':    '-date',
    '_count':   '20',
})
response.raise_for_status()

entries = response.json().get('entry', [])

if not entries:
    print("No lab observations found.")
else:
    print(f"Lab results for patient {patient_id}:\n")
    for entry in entries:
        obs   = entry['resource']
        code  = obs.get('code', {}).get('text', 'Unknown')
        date  = obs.get('effectiveDateTime', '')[:10]
        value = obs.get('valueQuantity')
        if value:
            print(f"  {date}  {code}: {value.get('value')} {value.get('unit', '')}")
