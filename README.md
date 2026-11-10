# AI Olympiad: Research and Design Foundation

Status: **draft for discussion**. This repository provides the evidence and working structure for a future KOAI 2027 preparation course for middle-school students with basic coding experience, planned as 10 weeks of two-hour classes. Creating the week 1–2 lesson materials, running repeated work, and setting up an automated schedule have not yet been authorized. The competition scope and learner level will be confirmed against official announcements and through discussion with the user.

## Getting started

1. Read the [questions and decisions](docs/decisions.md).
2. Review the [design and iteration process](docs/design.md) and [evidence review](docs/evidence.md).
3. Use the [skill contracts](skills/README.md), [work record template](templates/run.json), and [review template](templates/review.json).
4. Example data is fictional and does not represent actual learner information, requests, or completed work.

```sh
python3 -m unittest discover -s tests -v
python3 tools/validate.py examples/graph.json
```

The validator checks only parts of the references and structure. It does not guarantee scholarly validity, accuracy, educational effectiveness, or safety. Do not run the process automatically before the criteria under discussion are agreed.
