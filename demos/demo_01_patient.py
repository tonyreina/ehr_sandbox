"""Demo 1: Retrieve a patient by ID from the configured EHR."""
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

patient_id = PATIENTS.get(sys.argv[1]) if len(sys.argv) > 1 else PATIENTS["camila"]

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
