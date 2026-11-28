# HelpDesk

Support Ticket Management System for a five-member Software Engineering project.

## Local setup (Windows / Python 3.12)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:SECRET_KEY = .\.venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"
.\.venv\Scripts\python -m flask --app run init-db
.\.venv\Scripts\python run.py
```

Open http://127.0.0.1:5000. Register a regular account, then log in.
The SQLite database is created under `instance/` and is ignored by Git.
Keep the same SECRET_KEY between runs to preserve sessions. The fallback key is
for local development only; deployment must supply its own secret and HTTPS.
`init-db` creates missing tables; it does not migrate existing schemas.

## Tests

```powershell
.\.venv\Scripts\python -m pytest -q
```

Tests use temporary SQLite databases. Registration, secure password storage,
login/logout, duplicate accounts, input validation and CSRF protection are covered.
GitHub Actions runs tests with Python 3.12 and 3.13 on pushes and pull requests (see docs/testing.md).

## Shared integration contract

- One shared `User` model lives in `app/models.py`.
- Role values: `user`, `support`, `admin`. Public registration always creates `user`.
- Flask-Login supplies `current_user`, `login_required` and session handling.
- All POST forms must include hidden `csrf_token` with the template-provided value.
- Admins change roles on the Users page (`/admin/users`) or with `flask --app run set-role EMAIL ROLE`.
  `flask --app run seed-demo` creates local demo accounts; there are no built-in credentials.
- Authentication was implemented as an owner-authorized prerequisite because
  the original foundation had no User model or authentication routes.
  The team should coordinate further authentication work with Member 2.

## Contribution workflow

Track work in Issues and the GitHub Project. Use a dedicated branch and PR per
feature; run tests before pushing and check CI before merging. The owner performs
final testing; no independent teammate review is claimed. Each teammate must make
their own contributions. This repository does not attribute work to absent members.

## Ticket creation and viewing demo

1. Run `init-db` again after pulling this feature so the Ticket table exists.
2. Register and log in as a regular user.
3. Choose **Create ticket**, enter a title and description, select a category and
   priority, and submit. The detail page shows the saved ticket with Open status.
4. Open **Tickets** to see your tickets, newest first (20 per page).
5. Log out and register a second account. Its list is separate, and accessing
   the first account's detail URL returns 404.
6. Missing titles/descriptions, invalid choices, and excessive field lengths are
   rejected. Failed forms preserve the entered values.

Categories: General, Technical, Account, Billing. Priorities: Low, Medium, High.
Title limit: 200 characters; description limit: 10,000 characters. All four
fields are required. Creator, initial status, and timestamps are set server-side.
Times display in UTC. `support` and `admin` roles can view all tickets; role
promotion is intentionally not exposed through registration or this ticket feature.
Unknown roles are denied access. Staff fixtures exercise these rules in tests.

Ticket endpoints: `GET /tickets`, `GET /tickets/new`, `POST /tickets/new`, and
`GET /tickets/<id>`. Other users' private tickets return the same 404 as missing
IDs. POSTs require a valid session CSRF token. List queries apply permissions
before pagination. Templates extend the existing Bootstrap layout.

Status transitions, comments and change history are provided by Member 4's workflow panel on the ticket page.
Deployment remains future work.
Editing and assignment use the existing shared schema; no database migration is needed. Coordinate schema changes with Members 2
and 4; `init-db` is not a migration system.

See [Phase 1 evidence and handover](docs/phase1.md) for implementation boundaries,
acceptance checks and the remaining team requirements.


## Ticket editing and assignment

- Regular users can edit their own title, description, category and priority.
- Support and admins can edit any ticket. Other users' edit URLs return 404;
  unknown roles receive 403. Anonymous requests redirect to login.
- Support and admins can assign a ticket to a user whose current role is
  `support`, or choose **Unassigned**. Regular users cannot change assignments.
- Updates preserve the creator, original creation time and status. Assignment
  cannot be changed through the edit form. Successful changes update `updated_at`
  in UTC; unchanged submissions need not change the timestamp.
- The details page displays the assigned agent and last update time. Staff see
  an assignment selector; all authorized viewers see the edit link.
- Validation uses the same required fields, length limits and choices as creation.
  Invalid submissions return 400 without changing the ticket. POSTs require CSRF.

Endpoints: `GET/POST /tickets/<id>/edit` and `POST /tickets/<id>/assign`.
The assignment form sends `assigned_to_id`: an existing support-agent ID, or an
empty string to unassign. Missing, malformed, nonexistent and non-support IDs
are rejected. Status changes and activity history are handled by Member 4's workflow feature.

Manual demo: create a ticket, open its details, select **Edit ticket**, change the
priority/description, and save. Verify the changes and original creator/status.
A second regular account cannot access the edit URL. To exercise assignment,
use a trusted existing support/admin account. There is no public role-promotion
form. A local developer can deliberately configure a previously registered demo
account using `python -m flask --app run shell` inside the virtual environment:

```python
from app import db
from app.models import User
agent = db.session.scalar(db.select(User).where(User.username == "your_agent_username"))
assert agent is not None
agent.role = "support"
db.session.commit()
```

Only use a known account in your local demo database. Log in as that support
account, open the ticket, assign it, then unassign it. Check the persisted result
as the creator. `tests/test_ticket_edit_assign.py` covers these workflows and
failure cases with temporary databases and staff fixtures.

For the November 24 target, see the [Phase 1 readiness snapshot](docs/phase1-readiness.md)
for demo steps, contribution/merge evidence and outstanding team requirements.

## Testing and CI

See [Testing, CI and local setup](docs/testing.md) for the setup commands, the
demo accounts (`flask --app run seed-demo`), how to run the tests with a coverage
report, which test file covers which feature, and what GitHub Actions checks on
every push and pull request (Python 3.12 and 3.13).