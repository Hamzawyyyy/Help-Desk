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
  branch `feature/ticket-edit-assign`, [PR #7](https://github.com/Hamzawyyyy/Help-Desk/pull/7).
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


## November 20 integration session: performed November 21, 2026

The session was completed on November 21; no earlier execution is claimed.
Baseline main was `a5950f3` (merged PR #7), with a clean local checkout, no
new teammate changes, and no open Issues or PRs at inspection. Its 78 tests
passed on Python 3.12.10 and its latest GitHub Actions run was successful.

The integration review reproduced a shared CSRF defect: a non-ASCII submitted
form token raised TypeError in the string comparison, causing a server error
instead of rejecting the form. The fix rejects non-ASCII tokens with HTTP 400.
Six regression cases exercise authentication, logout, creation, editing and
assignment POST endpoints. Work is tracked in
[Issue #8](https://github.com/Hamzawyyyy/Help-Desk/issues/8) and its linked PR
on `fix/phase1-integration`.

`tests/test_workflow_http.py` runs the documented demo over real localhost HTTP
with separate cookie sessions and a disposable SQLite database. It covers actual
registration/login, creation, owner editing, another user's denied access,
support assignment/unassignment, creator-visible assignment, logout, invalid
CSRF input and persisted relationships. Support setup is deliberate test-only
role configuration matching the README. No production database, real accounts,
or owner manual testing are used or claimed.

Validation after the fix: **85 tests passed** on Python 3.12.10, including the
real-HTTP journey and all six Unicode-token regression cases.

Reproduce with `python -m pytest -q`; run just the HTTP journey with
`python -m pytest -q tests/test_workflow_http.py`. The integration work does not
complete GitHub Projects setup or the other members' individual contributions.
At inspection, `git shortlog -sne origin/main` showed only one Git author
(Hamza Hossam). Projects access remains unverified: no Projects connector tools
are available, and previously declined browser access was not bypassed.
The November 23 readiness session should recheck these remaining requirements
before the November 24 target.
