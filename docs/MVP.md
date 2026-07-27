# MVP acceptance record

## Observable signal

- The native engine captures a five-step local agent run ending in a dialect error.
- The debugger branches from a checkpoint, mutates the prompt, and resumes at the
  earliest affected step.
- The corrected branch completes with PostgreSQL syntax.
- Tests confirm that unchanged logical pages have identical physical page IDs and
  changed logical pages have different IDs.
- Closing and reopening the workspace reconstructs byte-identical state.

## Inference

Page-level CoW can substantially reduce snapshot storage when agent state changes
sparsely. The included scenario avoids about 75.7% of bytes versus copying every
complete state. This result does not predict VRAM savings until a real model
adapter is measured.

## Automated decision

The demo adapter invalidates state from dialect selection onward when the prompt
changes. Earlier parsing and schema pages remain reusable. In a production
adapter, dependency declarations must come from the workflow/model integration;
the storage engine does not guess semantic dependencies.

## Acceptance commands

```bash
npm test
npm run build
./build/timeweaver demo /tmp/timeweaver-demo
./build/timeweaver validate /tmp/timeweaver-demo
npm start
```

The MVP is accepted when the tests pass, the demo reports a failed and a
successful branch, validation succeeds, and the browser can create another
successful fork through `/api/fork`.
# Phase boundary

This MVP does not load GGUF models or generate model tokens. Those claims belong
to the separately preregistered llama.cpp bridge and require a real-model run.
