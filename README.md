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
GitHub Actions runs tests with Python 3.12 on pushes and pull requests.

## Shared integration contract

- One shared `User` model lives in `app/models.py`.
- Role values: `user`, `support`, `admin`. Public registration always creates `user`.
- Flask-Login supplies `current_user`, `login_required` and session handling.
- All POST forms must include hidden `csrf_token` with the template-provided value.
- No public role promotion or default staff credentials are provided.
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

Editing, assignment workflows, comments, status transitions, history, and deployment
remain future work. The nullable assignment field prepares the agreed shared
schema without implementing Feature 2. Coordinate schema changes with Members 2
and 4; `init-db` is not a migration system.

See [Phase 1 evidence and handover](docs/phase1.md) for implementation boundaries,
acceptance checks and the remaining team requirements.
