# Lessons: building AI projects for the hospital

A series for healthcare professionals. You do not need to write code: you describe what you want, run a few commands in the VS Code terminal, and check the results like a clinician.

**Ground rules for every lesson**

- Use **synthetic data only**: the Synthea patients, the teaching scenarios and the public sandboxes. Never type or paste real patient information.
- Each lesson ends with something you can show a colleague.
- You keep the same app all the way through; each lesson adds one idea.

Before Lesson 1, finish [Prerequisites](../setup/prerequisites.md), [Local HAPI Server](../setup/local-hapi.md) and [OpenAI Codex](../setup/codex.md).

| Lesson | Idea | Status |
|---|---|---|
| [1. See the data](lesson-1.md) | An EHR is structured data you can look at | Ready |
| [2. Ask questions in plain English](lesson-2.md) | An AI can read a chart and answer questions, and it can be wrong | Ready |
| 3. Build a single-purpose tool | A narrow task with a clear output beats a general chatbot | Planned |
| 4. Let the AI look things up | Tools and agents: the model decides what data to fetch | Planned |
| 5. Add clinical knowledge | Ground the AI in your guidelines and cite them | Planned |
| 6. Monitor and alert | Move from on-demand to proactive, and manage alert fatigue | Planned |
| 7. Write back with a human in the loop | AI proposes, a clinician approves | Planned |
| 8. Governance and deployment | Privacy, validation and what it takes to reach the hospital | Planned |

## Instructors

`pixi run hapi-scenarios --answers` prints the planted problem and a good test question for each teaching patient. Keep that output away from learners until they have tried the exercises.
