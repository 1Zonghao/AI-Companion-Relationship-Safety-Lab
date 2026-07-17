# Completed Annotations

Place completed reviewer files here:

- `reviewer_a.csv` — Annotator A's completed form
- `reviewer_b.csv` — Annotator B's completed form

Files must be CSV format with all 44 items completed.
Each row must have:
- item_id (matches frozen batch)
- labels (JSON string of label->judgment mapping)
- evidence_spans (JSON string of label->evidence mapping)
- confidence
- short_rationale
- cannot_judge_reason (if applicable)

**DO NOT:**
- Use LLM-generated annotations
- Submit the same file for both annotators
- Modify the item_id field
- Skip any items
