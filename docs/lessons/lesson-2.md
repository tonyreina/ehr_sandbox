# Lesson 2: Ask questions in plain English

**Idea:** an AI can read a chart and answer questions about it, but it can be confidently wrong. Your job is to ask well and check every answer.

**You will finish with:** three tested prompts and one example of the AI getting something wrong.

## Setup

Finish [OpenAI Codex](../setup/codex.md) first (`pixi run codex-setup`). Then start the dashboard:

```bash
pixi run smart-app --ehr hapi
```

The terminal line **Ask box: ready** confirms your token was found. If it says it needs a token, run `pixi run codex-setup` and start the dashboard again.

## How the Ask box works

Open the **Ask AI** tab next to **Chart**, just below the patient banner. The AI reads the same chart you see on the **Chart** tab, so pick the patient first. When you press **Ask**:

1. The page copies the text of the chart panels you can see.
2. It sends that text and your question to the AI through the course proxy, together with standing instructions: answer only from the chart, say "Not documented in this chart" if unsure, and name the section each fact comes from.
3. The answer appears below. Open **What the AI sees** to read exactly what it was given: the **system message** (the standing instructions above, shown in green) and the **user message** (the chart text and your question).

Under each answer, four chips show the **model** that answered, the **cost** of the question, and the number of **input tokens** (what you sent: the instructions, the chart and your question) and **output tokens** (what the AI wrote). The course proxy does not report a cost, so the cost is always an estimate (`≈`) from published per-token prices. The request also tells the proxy not to store your chart or the answer.

The AI knows nothing about the patient except that text. If a fact is not on the page, it is not available to the AI.

## Writing a good question

A good question has four parts:

| Part | Example |
|---|---|
| Role or purpose | "I am a nurse preparing for handoff." |
| What to look at | "Using the labs and medications..." |
| What you want | "...list anything that changed this year." |
| The shape of the answer | "Answer in three bullet points." |

## Exercises

1. **Warm up.** Open Maria Alvarez. Click each example question in turn and read the answers. Check each against the panels.
2. **Write three prompts.** Write three questions of your own about Maria using the four parts above. Compare the answers. Which wording gave the most useful one?
3. **Ask about something missing.** Open Alex Rivera and ask: *List this patient's allergies and current medications.* What does the AI say? What should a safe answer say?
4. **Ask something outside the chart.** On any patient, ask: *What is this patient's blood type?* A safe answer says it is not documented.
5. **Check the AI against the chart.** Open Susan Whitfield and ask about her smoking status and allergies. Then read the Allergies panel, the Problem list and the chart text in **What the AI sees** yourself. Does the answer match everything on the page? If the sources disagree, what should the AI do?
6. **Catch a mistake.** Keep asking different questions until the AI says something the chart does not support, or leave out something that is there. Write down the question, the answer and what the chart actually says.

## Discuss

- Which exercise would have caused harm if you had trusted the answer without checking?
- What did the standing instructions (the system message) change? Try the same question in a general chatbot and compare. Then think about how you would reword the system message to make the AI more cautious.
- Which of your questions cost the most, and why? Compare a short question with a long chart against a long question about a short chart. What would it cost to ask this of 1,000 patients?
- Who should be responsible for a wrong AI answer used in care?

## Tips and troubleshooting

| Symptom | Fix |
|---|---|
| "No OPENAI_TOKEN found" | Run `pixi run codex-setup`, then stop the dashboard (Ctrl + C) and start `smart-app` again. |
| "rejected your token" | Check the token, then run `pixi run codex-setup` again. |
| "The course proxy refused the request" | Run `pixi run codex-check` and read the message after `FAILED`. A rejected token needs `pixi run codex-setup` with a correct token; other reasons go to your instructor. |
| A "No token found yet" note under the Ask box | The token was not found when `smart-app` started. Same fix as above. |
| The answer ignores a panel | Wait until the panels finish loading, then ask again. Check **What the AI sees**. |
