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
