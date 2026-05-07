# AGENTS.md

## Scope
These instructions apply to the entire repository.

## Mandatory status tracking
- `status.md` is the source of truth for task progress, decisions, validation results, risks, blockers, and next actions.
- Before starting any non-trivial task, read `status.md` and any relevant task/design documents.
- Before finishing any non-trivial task, update `status.md` in the same change set.
- Do not complete a Codex task unless `status.md` reflects the latest work result and validation status.
- Preserve existing history in `status.md`; append a dated entry instead of deleting prior records unless explicitly instructed.

## Required `status.md` entry content
Each update must include concise factual bullets with:
- date or timestamp
- scope or task ID
- completed work
- files added or modified
- validation command(s) and PASS/WARN/FAIL result(s)
- current status: PASS / WARN / FAIL
- risks or blockers
- next actions

Preferred format:

```markdown
#### YYYY-MM-DD HH:MM
- Scope:
- Completed:
- Files changed:
- Validation:
- Status:
- Risks / blockers:
- Next actions:
```

## LAB/W-task requirements
For LAB/W-task work, `status.md` must always show:
- latest completed W-task or subtask
- latest validation result
- whether the repo is in a runnable state
- what Codex should do next if the session stops here

## Current operational priority
- The live Oracle collector path is implemented in `src/lab/commands/collect_db.py` and `src/lab/db/oracle_collector.py`; the next priority is validating it against a real Oracle connection and then tightening `generate db-schema`/`validate_db` coverage for live `db_collection.json` payloads.
