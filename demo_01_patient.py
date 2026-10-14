"""Demo 1: Retrieve a patient by ID from the Epic sandbox."""
import os
import sys
from dotenv import load_dotenv
from epic_auth import authed_session

load_dotenv()

FHIR_BASE = os.getenv('EPIC_FHIR_BASE')

# Known Epic sandbox test patients
PATIENTS = {
    'theodore': 'e63wRTbPfr1p8UW81d8Seiw3',   # Theodore Mychart  1948-07-07 M
    'derrick':  'eq081-VQEgP8drUUqCWzHfw3',    # Derrick Lin        1973-06-03 M
    'camila':   'erXuFYUfucBZaryVksYEcMg3',    # Camila Lopez       1987-09-12 F
    'linda':    'eIXesllypH3M9tAA5WdJftQ3',    # Linda Ross         1969-04-27 F
}

patient_id = PATIENTS.get(sys.argv[1]) if len(sys.argv) > 1 else PATIENTS['camila']

session  = authed_session()
response = session.get(f"{FHIR_BASE}/Patient/{patient_id}")
response.raise_for_status()

patient = response.json()
name    = patient['name'][0]
given   = name['given'][0]
family  = name['family']
dob     = patient['birthDate']
gender  = patient['gender']

print(f"Patient: {given} {family}")
print(f"DOB:     {dob}")
print(f"Gender:  {gender}")
print(f"ID:      {patient_id}")
