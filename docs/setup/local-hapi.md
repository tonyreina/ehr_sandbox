# Practice patients

Run your own practice EHR with synthetic patients. Docker must be running (see [Install](prerequisites.md)). Run these in the VS Code terminal:

```bash
pixi run hapi-up         # start the server (the first time it downloads it)
pixi run hapi-load       # add 25 realistic synthetic patients (about 2 minutes)
pixi run hapi-scenarios  # add 8 teaching patients
```

Patients are kept between sessions. `pixi run hapi-down` stops the server, and `pixi run hapi-down --delete-data` also erases every patient. Next: [Open the dashboard](../demos/smart-app.md).

## Teaching patients

Each of these eight fictional patients hides one problem for you to find with the AI. Dates are relative to today, so "months ago" stays true.

| Key | Patient | Chart |
|---|---|---|
| `maria` | Maria Alvarez | Type 2 diabetes on metformin |
| `robert` | Robert Kline | Hypertension and heart failure, a year of labs |
| `helen` | Helen Park | Atrial fibrillation on warfarin, recent infection |
| `david` | David Okafor | Seen for sinusitis |
| `susan` | Susan Whitfield | COPD, with a visit note |
| `alex` | Alex Rivera | One visit, almost no data |
| `smith1` | John Smith | Heart failure |
| `smith2` | Jon Smith | Asthma (a look-alike of `smith1`) |

Try `pixi run patient maria --ehr hapi`. Instructors: `pixi run hapi-scenarios --answers` prints each planted problem and a good test question; keep it from learners until they have tried the exercises. The data is teaching data, not for clinical use.

## More patients

`hapi-load` adds more with these options (add `--force` when the server already has patients):

| Option | Meaning |
|---|---|
| `-p 15` | How many patients (default 25) |
| `-c "diabetes mellitus type 2"` | Only patients with a condition whose name contains this text |
| `--age 50-85` | Age range in years |
| `--gender F` | `M` or `F` |

```bash
pixi run hapi-load -p 15 --force -c "diabetes mellitus type 2" --age 50-85
```

With `-c`, patients are generated in batches until enough match, which can take a few minutes. It stops with an error if it cannot find enough, so check the spelling or widen `--age`. `diabetes` also matches *prediabetes*, so use the full name.

| Cohort | `-c` text | Suggested options |
|---|---|---|
| Type 2 diabetes | `diabetes mellitus type 2` | `--age 50-85` |
| Heart failure | `chronic congestive heart failure` | `--age 60-90` |
| Kidney disease | `chronic kidney disease` | `--age 55-90` |
| Sepsis | `sepsis` | |
| Dementia | `alzheimer` | `--age 65-95` |
| Cancer | `malignant neoplasm` | `--age 45-90` |
| Asthma | `asthma` | |
| Pregnancy | `normal pregnancy` | `--gender F --age 18-40` |

Other options: `-s` (random seed; the same seed gives the same patients), `--state` (default Massachusetts) and `--numbered-names` (keeps Synthea's obviously fake digits, like `Erin498`).

## If something goes wrong

| Problem | Fix |
|---|---|
| `Could not start HAPI` | Check `docker ps` and `docker logs ehr-hapi`. Port 8080 must be free. |
| `HAPI is not running` | Run `pixi run hapi-up` first. |
| `The server already has N patients` | Add `--force` to add more, or `pixi run hapi-down --delete-data` to start empty. |
| The dashboard shows the public server | Start the dashboard after `hapi-up`. |
