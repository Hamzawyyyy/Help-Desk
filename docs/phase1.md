# Phase 1 evidence and handover

## Scope and ownership

Member 3 requested Ticket Creation & Viewing, with a dedicated feature branch and
PR. The owner additionally authorized authentication as a separate prerequisite
because the baseline had no User model, login routes, or role definitions.
This prerequisite is not presented as a contribution made by Member 2.
All implementation is AI-assisted; no teammate review, testing, meeting, or
contribution is fabricated.

## Work records

- Prerequisite: [Issue #2](https://github.com/Hamzawyyyy/Help-Desk/issues/2),
  branch `feature/user-auth`, [PR #4](https://github.com/Hamzawyyyy/Help-Desk/pull/4).
- Member 3 Feature 1: [Issue #3](https://github.com/Hamzawyyyy/Help-Desk/issues/3),
  branch `feature/ticket-creation`, [PR #5](https://github.com/Hamzawyyyy/Help-Desk/pull/5).
- Member 3 Feature 2: [Issue #6](https://github.com/Hamzawyyyy/Help-Desk/issues/6),
  branch `feature/ticket-edit-assign`, separate linked PR.
- Implementation and tests/documentation are recorded in focused commits.
- CI uses Python 3.12 and runs on both pushes and PRs.
- The repository owner is the final tester. Automated checks and implementation
  self-review do not constitute an independent teammate approval.

## Ticket acceptance checks

`tests/test_tickets.py` covers persisted creation and server-selected ownership,
initial status and timestamps; required fields, length limits and allowed choices;
list/detail visibility for users, support and admins; unknown-role denial;
anonymous requests; nonexistent and malformed IDs; CSRF; HTML escaping;
permission-aware pagination; and preserving fields after validation errors.
`tests/test_auth.py` covers the authentication prerequisite. Tests use isolated,
temporary SQLite databases rather than the demo database.

## Editing and assignment acceptance checks

`tests/test_ticket_edit_assign.py` verifies owner/staff edits, required fields and
validation failures without persistence, denied edits, staff-only assignment and
unassignment, invalid/non-support agent IDs, saved relationships/timestamps,
CSRF, missing tickets and HTML escaping. Protected creator/status/creation time
and assignment fields cannot be overwritten through editing. No schema change
or status/history logging is introduced. The README documents permissions and
manual demo steps. Automated/self-review evidence does not imply owner testing.

## Current schema contract

User: id, username, email, password_hash, role (`user`, `support`, `admin`).
Ticket: id, title, description, category, priority, status, creator_id,
assigned_to_id (nullable), created_at, updated_at.
Relationships distinguish creator and assignee explicitly. Creation initializes
Open status and UTC timestamps. No Comment or TicketHistory model is added here.
Role management and schema migration tooling remain separate team work.

## Remaining Phase 1 team requirements

- Add the Issues and PRs to a real GitHub Project and maintain its status columns.
  Project setup was blocked by unavailable CLI authentication and declined browser
  access during this implementation. Issues alone do not satisfy the Projects rule.
- Each of the five members must contribute actual code using their own identity.
  This change alone does not meet the whole-team contribution requirement.
- Have the owner run the README demo before the Phase 1 evaluation.

## Later work

Member 3 Feature 2 (editing/assignment) follows merged Feature 1 on its own
branch and linked PR. Members 1, 2, 4, and 5 should continue
their agreed responsibilities and avoid duplicating the shared models.
The Phase 2 requirements for two features per student, comprehensive specifications,
UML, milestones, Scrum notes, deployment pipeline and live deployment are not claimed
as completed by this Phase 1 change. No meeting summaries or dates are invented.
