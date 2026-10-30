# Lesson 1: See the data

**Idea:** an EHR is structured data you can look at, and you can ask a computer for it.

**You will finish with:** a patient dashboard running on your own computer, and the ability to say which parts of a chart come from which kind of record.

## 1. Start the patients

Open the project folder in VS Code and open the terminal (**Terminal > New Terminal**). Docker Desktop must be running. Then run:

```bash
pixi run hapi-up
pixi run hapi-load
pixi run hapi-scenarios
```

`hapi-up` starts your own practice EHR server, `hapi-load` fills it with 25 realistic synthetic patients, and `hapi-scenarios` adds eight teaching patients you will use in the next lessons. The first run downloads some software and takes a few minutes.

## 2. Open the dashboard

```bash
pixi run smart-app --ehr hapi
```

Your browser opens a patient chart. Use the **Patient** menu to pick someone. Stop it any time with **Ctrl + C** in the terminal.

## 3. Learn the vocabulary

Each box on the chart is a kind of FHIR record. FHIR is the standard way EHRs share data.

| On the chart | FHIR resource | What it holds |
|---|---|---|
| Banner | Patient | Name, birth date, sex |
| Vitals, Results | Observation | Measurements and lab results |
| Medications | MedicationRequest | Prescriptions |
| Allergies | AllergyIntolerance | Allergies and reactions |
| Encounters | Encounter | Visits |
| Problem list | Condition | Diagnoses |

## 4. Exercises

1. **Find a patient with an abnormal lab.** Browse the Results panel. Write down the patient, the test and why it caught your eye.
2. **Compare two patients.** Open Maria Alvarez and Robert Kline. What do their problem lists and medications tell you about each?
3. **Look at the same data another way.** In the terminal, run `pixi run patient maria --ehr hapi` and `pixi run observations robert --ehr hapi`. The dashboard and the terminal read the same records.
4. **Spot the gaps.** Open Alex Rivera. What does the chart not tell you? Keep your list for Lesson 2.

## Check yourself

- Which panel would you check before prescribing an antibiotic? Which record type is it?
- If a panel is empty, does that mean the patient has none, or that nothing was recorded?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `docker` errors | Start Docker Desktop and wait until it says it is running, then retry. |
| The patient menu is empty | Run `pixi run hapi-load`, then restart `smart-app`. |
| Port already in use | Another dashboard is running. Press Ctrl + C in its terminal first. |
