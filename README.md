# AIChatBot_TeamE


**Branch Structure and Workflow**
This repository follows a structured branching strategy to manage development, testing, and deployment in a Scrum environment. Below is an overview of the branches and their roles:

**Feature Branches:**
- Used by individual  for assigned tasks from scrum master.
- Created from main for new work, where initial development and commits occur.
- Merged into staging after completion via pull request (PR) with code review.

**staging:**
- Integration branch for combining feature branches.
- Used for preliminary reviews, integration checks, and basic testing (e.g., unit tests).
- Developers ensure features work together before moving to test.

**test:**
- Testing branch for comprehensive validation.
- QA teams and automated tests (e.g., end-to-end, performance, UAT) validate the code. (not sure yet.)
- Acts as the final checkpoint before production deployment.

**main (Default Branch):**
- Represents the stable, production-ready code deployed to users.
- Only receives merges from test after successful validation.
- Protected to prevent direct pushes; updates occur via pull requests.
