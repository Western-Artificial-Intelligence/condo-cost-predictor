# Contribution Guide

Thank you for contributing to the Toronto Condo Affordability Predictor! 

## Branch Naming Convention
Use clear, scoped branch names based on your role and task:

| Type | Format | Example |
|------|---------|---------|
| Data | `data/<short-description>` | `data/etl-pipeline` |
| ML | `ml/<short-description>` | `ml/baseline-model` |
| Backend | `backend/<short-description>` | `backend/fastapi-setup` |
| Frontend | `frontend/<short-description>` | `frontend/ui-layout` |
| Docs | `docs/<short-description>` | `docs/sprint1-summary` |
| Fix | `fix/<short-description>` | `fix/frontend-api-call` |

Create a new branch before working on any issue:
```bash
git checkout -b backend/fastapi-setup

## making your branch 
# make sure you're on main and up-to-date
git checkout main
git pull origin main

# Now create a new branch from the latest main
git checkout -b settings/contrubutionformat
git add .
git commit -m "Add contribution format and setup"
git push --set-upstream origin settings/contrubutionformat


# SINCE I ALREADY SET UP THE ISSUES USE THIS FORMAT 
#<type>: <short summary> (#issue-number)

# DO NOTTTT PUSH INTO MAINN! MUST PR. 

# chek what you are committing git status

Pull Requests
Each PR should close or link at least one GitHub issue.
Use Closes #<issue-number> in your PR description.
Request a review from another team member before merging.
Keep PRs focused (one logical change per PR).

#just so we all follow this i am sure you guys know but might as well 
git checkout -b "nameit'
git add . 
git commit -m "description"
git push origin "thename"
git status
- On GitHub, open a Pull Request
Go to your repo page → you’ll see a yellow banner “Compare & Pull Request.”
Click it, then add a short description:
This PR initializes the project structure with base folders, .env.example, and CONTRIBUTING.md.
Closes #1


FOR THE .ENV STUFF 🧩
 1. Copy .env.example → .env locally
- Run this in your project root: cp .env.example .env

- Then open it in your editor and fill in the real credentials, like this:
  DB_HOST=localhost
  DB_PORT=5432
  DB_NAME=condo_db
  DB_USER=postgres
  DB_PASSWORD=your_real_password
  API_KEY=super_secret_key
