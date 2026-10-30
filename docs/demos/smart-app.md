# Dashboard

A patient chart in your browser, with an **Ask AI** tab. Run it in the VS Code terminal:

```bash
pixi run smart-app --ehr hapi
```

It starts your practice server if needed and opens the chart. Pick a patient from the **Patient** menu, or search by name. Press **Ctrl + C** in the terminal to stop it (patients are kept).

![Dashboard on the local HAPI server](hapi_ehr_app.png)

## Chart tab

- **Banner:** name, age, and allergy and problem chips.
- **Vitals:** latest values and trend charts (hover for values; each chart has a table view), plus a day-by-day flowsheet.
- **Results:** latest value of each lab, flagged H or L when abnormal, with a small history graph.
- **Medications, allergies, encounters, problems:** the screen shows the first 10 rows of each. An empty list means nothing is recorded, not that the patient has none.

## Ask AI tab

1. Pick a patient, open **Ask AI**, and type a question or click an example.
2. Press **Ask**. The answer appears with chips for the model, estimated cost and token counts.
3. Open **What the AI sees** to read exactly what was sent: the system message (green) and the chart text with your question. The AI knows only that text.

The AI is told to answer only from the chart and to say "Not documented" when it is unsure. Check every answer yourself. Use synthetic patients only. Your token stays on your computer; the request also tells the proxy not to store your chart.

If the tab says no token was found, run `pixi run codex-setup <your-token>` (see [Connect Codex](../setup/codex.md)), then press Ctrl + C and start the dashboard again.

## Other EHRs

`--ehr cerner` opens the public Oracle Health sandbox with no login. `--ehr epic` needs your own Epic app. See [Advanced](../advanced.md) and the [dashboard internals](smart-app-internals.md).
