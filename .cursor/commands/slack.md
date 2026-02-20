Read the git log for the current branch and create a brief Slack message for my team. Use this exact format:

[PR Ready for Review] <PR_URL>
<TASK_ID> <Short title>
<One-liner describing the main change>
others: <brief list of secondary changes if any>
New env vars: <list any new environment variables with defaults>

Rules:
- Keep it very brief, no bullet points or markdown formatting
- Use plain language (no HTTP status codes or jargon)
- Main change gets one line, secondary changes go under "others:"
- Only include "New env vars:" section if there are new configuration options
- Skip "others:" if there are no notable secondary changes