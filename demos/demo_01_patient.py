"""Demo 1: Retrieve a patient by ID from the configured EHR."""
import os
import sys
from dotenv import load_dotenv
from ehr import ClientFactory
from ehr.patients import resolve

load_dotenv()

ehr_type = os.getenv("EHR_TYPE", "epic").lower()
_, patient_id = resolve(ehr_type, sys.argv[1] if len(sys.argv) > 1 else None)

client  = ClientFactory.from_env()
patient = client.get_patient(patient_id)

name   = patient["name"][0]
given  = name["given"][0]
family = name["family"]

print(f"EHR:     {client.ehr_name}")
print(f"Patient: {given} {family}")
print(f"DOB:     {patient['birthDate']}")
print(f"Gender:  {patient['gender']}")
print(f"ID:      {patient_id}")
