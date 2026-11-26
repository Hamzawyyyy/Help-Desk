# Phase 1 readiness snapshot — November 23, 2026

**Member 3's implementation is ready. Overall team Phase 1 readiness is not yet verified.**
Target: November 24. Evaluation window supplied by the instructor: November 28–December 3.
This snapshot records observed evidence, not a claim that every team requirement is finished.

## Verified baseline

Fetched `main` was `a7ffedc4c5dd9ca765231b3e7849d0cb6128730f`, unchanged since the
November 21 integration fix. The local working tree was clean at inspection.
No new teammate PRs were present. An existing unmerged testing contribution
was identified separately below. The full Python 3.12.10 suite passed again:
**85 passed**, including the real-HTTP demo. No new application defect was found.

## Contribution and merge evidence

| Work / source branch | Issue and merged PR | PR head / merge commit |
|---|---|---|
| Foundation: [`setup/project-foundation`](https://github.com/Hamzawyyyy/Help-Desk/tree/setup/project-foundation) | [PR #1](https://github.com/Hamzawyyyy/Help-Desk/pull/1) | [`9927d31`](https://github.com/Hamzawyyyy/Help-Desk/commit/9927d31) / [`9413ab1`](https://github.com/Hamzawyyyy/Help-Desk/commit/9413ab1) |
| Authentication prerequisite: [`feature/user-auth`](https://github.com/Hamzawyyyy/Help-Desk/tree/feature/user-auth) | [Issue #2](https://github.com/Hamzawyyyy/Help-Desk/issues/2), [PR #4](https://github.com/Hamzawyyyy/Help-Desk/pull/4) | [`86cb829`](https://github.com/Hamzawyyyy/Help-Desk/commit/86cb829) / [`3f5bcb8`](https://github.com/Hamzawyyyy/Help-Desk/commit/3f5bcb8) |
| Member 3 Feature 1: [`feature/ticket-creation`](https://github.com/Hamzawyyyy/Help-Desk/tree/feature/ticket-creation) | [Issue #3](https://github.com/Hamzawyyyy/Help-Desk/issues/3), [PR #5](https://github.com/Hamzawyyyy/Help-Desk/pull/5) | [`a260f50`](https://github.com/Hamzawyyyy/Help-Desk/commit/a260f50) / [`a17cefe`](https://github.com/Hamzawyyyy/Help-Desk/commit/a17cefe) |
| Member 3 Feature 2: [`feature/ticket-edit-assign`](https://github.com/Hamzawyyyy/Help-Desk/tree/feature/ticket-edit-assign) | [Issue #6](https://github.com/Hamzawyyyy/Help-Desk/issues/6), [PR #7](https://github.com/Hamzawyyyy/Help-Desk/pull/7) | [`5b7e030`](https://github.com/Hamzawyyyy/Help-Desk/commit/5b7e030) / [`a5950f3`](https://github.com/Hamzawyyyy/Help-Desk/commit/a5950f3) |
| Integration fix: [`fix/phase1-integration`](https://github.com/Hamzawyyyy/Help-Desk/tree/fix/phase1-integration) | [Issue #8](https://github.com/Hamzawyyyy/Help-Desk/issues/8), [PR #9](https://github.com/Hamzawyyyy/Help-Desk/pull/9) | [`bd689d1`](https://github.com/Hamzawyyyy/Help-Desk/commit/bd689d1) / [`a7ffedc`](https://github.com/Hamzawyyyy/Help-Desk/commit/a7ffedc) |

Each listed PR was verified as merged. Its commits, changes and merge date are
available in the linked PR. Member 3's two required features have separate
branches and PRs. Authentication was an owner-authorized prerequisite, not a
contribution attributed to Member 2. self-review and automated
checks do not constitute teammate approval or owner manual testing.

## Reproduce the demo

From the repository root on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:SECRET_KEY = .\.venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"
.\.venv\Scripts\python -m flask --app run init-db
.\.venv\Scripts\python -m flask --app run run --host 127.0.0.1
```

1. Open http://127.0.0.1:5000, register a regular account, and log in.
2. Create a ticket with a title, description, category and priority. Check the
   detail page for the creator, Open status and UTC creation time.
3. Edit the title/description/priority and save. Confirm that creator and status
   remain unchanged and the update persists when reopening the ticket.
4. Log out and register a second regular account. Its list must not expose the
   first ticket; that ticket's detail/edit URLs must return 404.
5. Use a trusted local support account to assign, unassign and reassign the
   ticket. See the README's explicit local role-setup instructions. The creator
   can see the assigned agent but cannot change assignments.
6. Check blank required fields and invalid choices are rejected, then log out.

Use accounts you control; there are no built-in staff credentials. `init-db`
creates missing tables without deleting existing data. Tests use disposable
SQLite databases and never modify the local demo database. No owner manual
completion of these steps is asserted by this report.

## Automated validation

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m pytest -q tests/test_workflow_http.py
```

The HTTP test uses real localhost HTTP and separate cookie sessions to verify
registration/login, ticket creation/editing, access restrictions, support
assignment/unassignment, logout, malformed CSRF rejection and persisted data.
The full suite additionally covers role flures, invalid/missing IDs, validation
boundaries, server-controlled fields, CSRF and escaped HTML.

Contribution evidence beyond main: [commit 9cc75ae](https://github.com/Hamzawyyyy/Help-Desk/commit/9cc75ae29a70b91f47a7e8346339d71c840b9ae7)
by `heshamhabiba277-dot` on [feature/test-setup](https://github.com/Hamzawyyyy/Help-Desk/tree/feature/test-setup) (November 3) adds `pytest.ini`,
test fixtures and a `.gitignore` change. It is unmerged and has no PR. Preserve
this real authorship; confirm the account's team-member identity and reconcile
its fixtures with current main before integration. Across fetched branches there
are two recorded Git author identities, rather than five verified team members.

Baseline merged-main CI: [successful run for a7ffedc](https://github.com/Hamzawyyyy/Help-Desk/actions/runs/44890915799).
This documentation PR must also pass CI before merging.

## Owner/team actions required by November 24

Track these in [Issue #10](https://github.com/Hamzawyyyy/Help-Desk/issues/10):

- [ ] Verify a real GitHub Project exists, link its URL, and add the existing
  Issues/PRs with accurate statuses. No Projects connector tool was available;
  prior declined browser access was not bypassed. Repository Projects support
  alone does not establish that a populated board exists.
- [ ] Have the existing `feature/test-setup` author update against current main
  and open a PR; preserve their commit attribution and reconcile overlapping fixtures.
- [ ] Every member without contribution evidence must push their own code and
  open a PR. Main records only Hamza Hossam, with a second author on the unmerged
  testing branch. Match authors to the actual roster; five-member evidence is incomplete.
- [ ] Test/integrate teammates' PRs and recheck the submitted branch's individual
  author evidence. Each feature needs its own branch; a single permanent branch
  per member does not satisfy the later two-feature requirement by itself.
- [ ] Owner runs the manual demo and records the actual outcome.

These steps can be coordinated asynchronously through Issues, PRs and the team
group. No in-person work session is required. Phase 2 specifications, UML,
Scrum records and live deployment are outside this readiness session.
