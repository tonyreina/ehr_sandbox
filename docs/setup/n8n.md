# Workflows (n8n)

n8n lets you build AI tools by connecting boxes instead of writing code. It runs on your computer in Docker next to the practice patients, and it calls the course AI with your token. You need the practice patients running ([Practice patients](local-hapi.md)) and your token saved ([Connect Codex](codex.md)).

## Start it

```bash
pixi run hapi-up
pixi run n8n-up
```

The first start downloads n8n (about 1 GB) and takes a few minutes. Then open [http://localhost:5678](http://localhost:5678). The first time, n8n asks you to create an account: use any email and password. It stays on your computer.

On the n8n home page, in the list of workflows, open the ready-made one called **Referral letter**. Each box is a step: it receives a request, reads the patient, the visit, problems, medications, allergies and labs from the practice server, builds the text, asks the AI, picks the letter out of the reply with a Python step, and sends the letter back.

## Use it from the dashboard

Start the dashboard with `pixi run smart-app --ehr hapi`, open a patient, and choose the **Referral** tab. Pick the visit, the specialty and how urgent it is, add a reason if you like, and press **Draft referral**. The letter appears in a box you can edit. Nothing is sent or saved.

## Change the workflow

**In n8n:** open **Referral letter**, click a box to see what it does, change it, then press **Publish** so the dashboard uses your version. Your changes are kept when you stop and start n8n. `pixi run n8n-up --reset-workflows` puts the original back (and replaces your edits).

**In VS Code:** the box called **Pick out the letter** runs the Python file `n8n/steps/pick_letter.py`. Open it in VS Code, change it and save. The next draft uses your change; there is nothing to restart or publish. If the file has a mistake, the Referral tab shows Python's error message. Ask Codex to help you edit it.

## Stop it

```bash
pixi run n8n-down                  # stop; your account and workflows are kept
pixi run n8n-down --delete-data    # stop and erase them
```

## If something goes wrong

| Problem | Fix |
|---|---|
| `The practice patient server is not running` | Run `pixi run hapi-up` first. |
| The Referral tab says n8n is not running | Run `pixi run n8n-up`. |
| It says the workflow is not active | Open **Referral letter** in n8n and press **Publish**, or run `pixi run n8n-up --reset-workflows`. |
| The workflow fails at the AI step | Run `pixi run codex-check`. If it says `token invalid`, run `pixi run codex-setup <your-token>` and then `pixi run n8n-up` again so n8n gets the new token. |
| The Referral tab says **The Python step failed** | The message is Python's own. Open `n8n/steps/pick_letter.py`, fix the line it names, and save. |
| You updated the project and the workflow looks old | Run `pixi run n8n-up --reset-workflows` once to get the new starter workflow. |
| Port 5678 is busy | Another program uses it. Stop that program, then run `n8n-up` again. |

n8n needs about 1 to 2 GB of extra memory. It is free to run yourself for learning (it uses a "fair-code" license; check n8n's terms before using it commercially). The token is given to n8n as a setting, so any workflow you run can use it: do not share workflow files you exported.
