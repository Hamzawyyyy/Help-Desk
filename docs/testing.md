# Testing, CI and local setup

Member 5 — Testing & CI/CD. This page explains how to set up the project,
run the tests, and what GitHub Actions checks on every push.

## 1. Set up the project (Windows, once)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m flask --app run init-db
python -m flask --app run seed-demo
python run.py
```

`seed-demo` asks for one password and creates four local demo accounts:
`admin@demo.test` (admin), `support@demo.test` (support), `user1@demo.test`
and `user2@demo.test` (users). Use them only in your own local database.

To give a real account a role without the Python shell:

```powershell
python -m flask --app run set-role someone@example.com support
```

After pulling changes that add new tables (for example comments and history),
run `python -m flask --app run init-db` again. It only adds missing tables.

## 2. Run the tests

```powershell
python -m pytest                                   # everything
python -m pytest tests/member2_auth                 # one member's tests
python -m pytest --cov=app --cov-report=term-missing   # with a coverage report
```

Every test uses its own temporary SQLite database, so the tests never touch
your demo data.

## 3. Which tests cover which feature

Every member keeps their tests in their own folder inside `tests/`.

| Folder / file | Feature | Owner |
| --- | --- | --- |
| `tests/test_home.py`, `tests/test_auth.py` | Foundation, register, login, logout, CSRF | Foundation |
| `tests/test_tickets.py`, `tests/test_ticket_edit_assign.py` | Create, view, edit and assign tickets | Member 3 |
| `tests/member2_auth/` | Admin users page, role rules, demo-account commands | Member 2 |
| `tests/member4_workflow/` | Status rules, change history, comments | Member 4 |
| `tests/member1_frontend/` | Menu, layout, restyled pages, dashboard | Member 1 |
| `tests/member5_testing/` | All features together, following the demo path | Member 5 |
| `tests/test_workflow_http.py` | The demo over real HTTP | Integration |

## 4. Continuous integration

`.github/workflows/tests.yml` runs on every push and every pull request.
It installs the requirements and runs the whole suite with a coverage report
on Python 3.12 and 3.13. A pull request is merged only when both checks are
green.

## 5. Before opening a pull request

1. `git switch main` and `git pull origin main`, then update your branch.
2. Run `python -m pytest` and make sure everything passes.
3. Add or update tests for the feature you changed.
4. Open the pull request and wait for the green CI check and a review.