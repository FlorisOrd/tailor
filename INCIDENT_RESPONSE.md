# Incident Response

## Purpose and Record

This framework applies to suspected security, privacy, availability, integrity, deployment, or data incidents. Create a private, durable GitHub-centered incident record when sensitivity permits; restrict access and keep secrets, exploit details, and unnecessary personal data out of issues and chat. Preserve timestamps, revision/deployment identity, decisions, commands, and evidence provenance.

## Severity

- **SEV-1:** active compromise, material data exposure/loss, unsafe authorization, payment impact, or critical outage with no safe workaround.
- **SEV-2:** serious degradation, contained high-risk vulnerability, or material integrity/recovery risk.
- **SEV-3:** limited impact with a safe workaround and no evidence of sensitive-data compromise.
- **SEV-4:** low-impact operational defect or warning requiring tracked follow-up.

When uncertain, classify at the higher severity until evidence supports reduction. Finding severity in `WORKFLOW.md` governs repair approval; incident severity governs response urgency.

## Responsibilities and Flow

1. **Detection and triage:** Operations opens the record, timestamps detection, identifies affected revisions/environments, assigns provisional severity, and alerts the Lead and Security Review when security or privacy may be involved.
2. **Containment:** Release owns deployment containment or rollback; Security owns credential revocation, access restriction, and security containment. No role acts outside its authorization. Preserve evidence before destructive cleanup when safe.
3. **Escalation:** Notify the product owner promptly for product/customer impact, spending, privacy, legal/compliance questions, public communication, irreversible actions, or external commitments. Do not invent legal duties; obtain appropriate advice through the owner when needed.
4. **Recovery:** Implementation repairs in isolated work. Independent Code Review, QA, triggered Security Review, and Release reapply the required gates to the recovery candidate. Verify data, access boundaries, health signals, and user-visible behavior before normal operation.
5. **Continuity:** Use the documented rollback/roll-forward and backup/recovery procedures. If neither is demonstrably safe, keep the affected capability contained and escalate the business tradeoff to the owner.
6. **Closure:** Operations records recovery verification, monitoring results, remaining risk, and follow-up owners.

## Evidence Handling

Minimize access, preserve originals, hash/export volatile artifacts where proportionate, record collection time and collector, and avoid altering logs unnecessarily. Never paste live credentials or personal data into the record. Credential exposure requires revocation/rotation and downstream impact assessment; deleting a visible value alone is not remediation.

## Postmortem

SEV-1 and SEV-2 incidents require a blameless postmortem; SEV-3 requires one when recurrence risk is material. Record timeline, impact, detection and containment, root and contributing causes, recovery evidence, control gaps, and corrective actions with owners and target dates. Update tests, monitoring, rollback/recovery documentation, governance, and `DECISIONS.md` where lessons are durable. Track actions to closure.
