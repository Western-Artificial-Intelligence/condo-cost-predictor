You are operating inside a git repository. I invoked this command intentionally, so you MUST ALWAYS create at least one commit (never refuse). If quality gates fail, still commit, but label appropriately and document it.

ABSOLUTE GIT STAGING RULES (NON-NEGOTIABLE)
- NEVER run: git add ., git add -A, git add --all, or any “add everything” equivalent.
- Stage modified + deleted files ONLY with: git add -u
- Stage NEW (untracked) files ONLY by explicitly adding their exact paths, e.g. git add path/to/newfile.ext
  - No globs. No adding directories unless unavoidable.
- Never commit secrets. If suspected secrets exist, still commit must happen, but EXCLUDE those files and explain what you excluded and why.

COMMIT AUTHORSHIP / TRAILERS (NON-NEGOTIABLE)
- Do NOT add Co-authored-by trailers or any trailers/metadata for tools/agents.
- Commits should appear authored only by me (default git config). Do not pass --trailer or similar flags.

GOAL
Create clean, Conventional Commits style commits. Prefer multiple commits if the changes naturally separate into different concerns.

PROCESS (FOLLOW IN ORDER)
1) Inspect working tree:
   - git status --porcelain=v1
   - git diff --stat
   - git diff

2) Propose commit plan:
   - First cluster changes by subsystem/module (e.g., api/, worker/, ui/, infra/, db/, shared/).
   - Within each subsystem, cluster by type (feat/fix/refactor/docs/test/chore).
   - Prefer 2–4 commits total when it improves reviewability/rollback.
   - If changes span multiple subsystems, prioritize splitting by subsystem first, then by type.
   - Always explain the plan briefly before executing.

3) For EACH commit in the plan:

   A) Select only the files for this commit.
      - Use git add -u first (stages modifications/deletions globally).
      - If staging too much, use git reset <paths> (NOT a refusal) to unstage what doesn’t belong in this commit.
      - Add needed NEW files with explicit: git add <exact path>
      - NEVER use git add . or -A.

   B) Verify staging:
      - git status --porcelain=v1
      - git diff --cached --stat
      - git diff --cached (unless huge; then summarize)

   C) Determine Conventional Commit type + optional scope:
      - feat, fix, refactor, perf, docs, test, chore, build, ci
      - scope should be a module/subsystem if obvious (e.g., feat(ui): ...)

   D) Compose commit message:
      SUBJECT (one line, <=72 chars):
        <type>(<scope>): <brief high-signal summary>
        - MUST be specific (no “update stuff”).
        - Prefer “verb + object + context”, e.g. “rename X to Y in Z”, “handle null in …”.

      BODY (a small report, in this exact order; OMIT any section that would be empty)
      1. What changed
         - bullets, concrete actions (UI copy changes are fine as concrete deltas)
      2. Why
         - bullets, intent + problem solved / alignment
      3. Files touched
         - bullet list of paths with brief purpose

      OPTIONAL SECTIONS (include ONLY if applicable; otherwise omit entirely)
      4. Flags / config / feature gates
         - list any feature flags, config keys, env vars added/changed
      5. Interfaces / data changes
         - new/changed variables, function signatures, API fields, DB schema
      6. Tests
         - commands run + results, or “Not run (reason)”
      7. Risks / follow-ups
         - known risks, TODOs, migration notes, or behavior caveats

      If something is incomplete or tests fail, still commit, but:
      - Use type “chore” and include “wip” in subject OR keep the original type and add “(wip)” in the subject.
      - Document failures in Tests and include next action in Risks / follow-ups.

   E) Commit:
      - Use ONLY: git commit -m "<subject>" -m "<body>"
      - Do NOT use --trailer and do NOT add Co-authored-by.

4) After all commits:
   - Show `git log -n <N> --oneline` for the commits created
   - Show a final execution summary in chat:
     - Commit hashes + subjects
     - For each commit: key behavior change + files changed
     - Any flags/config/interfaces introduced (only if present)
     - Tests status
Proceed now.
