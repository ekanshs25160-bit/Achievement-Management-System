# Improvement suggestions for Achievement Management System

Here are concrete improvements you can make, ordered by impact and effort.

---

## 1. Security (high priority)

### 1.1 Hash passwords
Passwords are stored and compared in **plain text**. If the DB is ever exposed, all accounts are compromised.

- **Do:** Use `werkzeug.security.generate_password_hash()` when saving (student/teacher registration) and `check_password_hash()` when logging in.
- **Where:** `student_new`, `teacher_new` (hashing), and `student`, `teacher` (checking).
- **Dependency:** Already available via Flask (Werkzeug).

### 1.2 Stable secret key
`app.secret_key = secrets.token_hex(16)` changes on every restart, so all sessions are invalidated when the app restarts.

- **Do:** In production, set `app.secret_key` from an environment variable (e.g. `SECRET_KEY`) and keep it fixed and secret.
- **Example:** `app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))` so dev still works without env.

### 1.3 Logout
There is no way for users to log out; session data stays until it expires.

- **Do:** Add a `/logout` route that calls `session.clear()` and redirects to home. Add “Logout” links in student and teacher dashboards.

### 1.4 Optional: CSRF and rate limiting
- **CSRF:** Use Flask-WTF and `CSRFProtect` for forms (login, registration, submit achievement) to prevent cross-site request forgery.
- **Rate limiting:** Use Flask-Limiter (or similar) on `/student` and `/teacher` to reduce brute-force login attempts.

---

## 2. Database and config (high priority)

### 2.1 Database path (fixed in code)
- **Done:** `DB_PATH` is now relative (`instance/ams.db`) so it works on any OS. No more hardcoded Windows path.

### 2.2 SQL syntax (fixed in code)
- **Done:** The `FOREIGN KEY teacher_id` typo in the achievements table creation was corrected to `FOREIGN KEY (teacher_id)`.

### 2.3 Connection handling
Many routes open `sqlite3.connect(DB_PATH)` and only close in success paths; on exceptions the connection can be left open.

- **Do:** Use a context manager everywhere, e.g. `with sqlite3.connect(DB_PATH) as connection:` and do all work inside the block. Avoid opening a second connection in the same block (e.g. in `submit_achievements` you have both `with sqlite3.connect(...)` and then `connection = sqlite3.connect(...)` again).

### 2.4 Optional: Use Flask-SQLAlchemy
- **Current:** Raw `sqlite3` everywhere; `requirements.txt` lists Flask-SQLAlchemy but it’s unused.
- **Do either:**  
  - Use Flask-SQLAlchemy and define models (Student, Teacher, Achievement) so schema and migrations are clearer, or  
  - Remove Flask-SQLAlchemy from `requirements.txt` to match the code.

---

## 3. Input validation and errors

### 3.1 Server-side validation
Form data is used with little validation (e.g. email format, required fields, date format).

- **Do:** Validate before DB or file operations: required fields, email format, date format, string lengths. Return clear error messages (e.g. “Email is invalid”) instead of generic “Database error”.

### 3.2 User-facing error messages
Some handlers return raw exception text to the user (e.g. `str(sql_error)`), which can leak internal details.

- **Do:** Log the full error server-side; show a generic message to the user (e.g. “Something went wrong. Please try again.”) unless the error is safe and intentional (e.g. “Student ID not found”).

### 3.3 Flash messages
Many routes pass `error=...` or `success=...` into `render_template`. That works but is easy to forget on redirects.

- **Do:** Use Flask’s `flash()` and `get_flashed_messages()` in a base template so success/error messages work consistently across redirects and page reloads.

---

## 4. Code structure and maintainability

### 4.1 Split the monolith
`app.py` is large and mixes config, DB helpers, and all routes.

- **Do:**  
  - `config.py`: DB path, secret key, upload folder, allowed extensions.  
  - `db.py` (or similar): `get_connection()`, `init_db()`, migration helpers.  
  - `routes/` or blueprints: e.g. `auth.py` (student/teacher login, logout, registration), `achievements.py`, `dashboard.py`.  
  - Keep `app.py` as app creation, config loading, and registering blueprints.

### 4.2 Logging instead of print
Debugging uses `print()` throughout.

- **Do:** Use the `logging` module (e.g. `logging.getLogger(__name__)`). Set level to DEBUG in development and INFO or WARNING in production so you can turn off noisy logs without editing code.

### 4.3 Single init path
`init_db()` is commented out; startup still calls `add_teacher_id_column()` and migrations are scattered.

- **Do:** Have one clear startup path: e.g. call `init_db()` when the app starts (or via a small `init_db.py` script as in the README). Move migration logic (e.g. adding `teacher_id`) into that init or a dedicated migration step so new installs and existing DBs behave consistently.

---

## 5. Project hygiene

### 5.1 init_db.py
README says “Initialize database: python init_db.py” but there is no `init_db.py`.

- **Do:** Add a small script that calls the same `init_db()` used by the app (e.g. import from `app` or from a shared `db` module) so the documented command works.

### 5.2 .gitignore
There is no project-level `.gitignore`, so `venv`, `*.db`, `instance/`, `__pycache__/`, `.env` can be committed.

- **Do:** Add a root `.gitignore` with at least:  
  `venv/`, `venv1/`, `*.db`, `instance/*.db`, `__pycache__/`, `.env`, `static/uploads/*` (or similar if you don’t want to track uploads).

### 5.3 requirements.txt
Only package names are listed (e.g. `Flask`, `Flask_SQLAlchemy`), so installs can change over time.

- **Do:** Pin versions, e.g. `Flask>=2.3.0,<3` and remove Flask_SQLAlchemy if you are not using it.

### 5.4 README vs app
- README says app runs on port 5000; `app.run(..., port=5001)` uses 5001. Either change the code to 5000 or update the README.
- README links like `/student-login` and `/teacher-login` don’t match routes (`/student`, `/teacher`). Update README or routes so they match.

---

## 6. UX and small fixes

### 6.1 Duplicate / similar templates
There are several similar templates (e.g. `student_new_1`, `student_new_2`, `teacher_new_1`, `teacher_new_2`). Hard to maintain and easy to diverge.

- **Do:** Prefer one template per “screen” and pass any variants via variables or includes (e.g. one `student_form.html` for both create and edit if applicable).

### 6.2 File upload limits
Only extension is checked; size is not.

- **Do:** Enforce a max file size (e.g. 5MB) in Flask (e.g. `app.config['MAX_CONTENT_LENGTH']`) and optionally in the frontend, and show a clear message when the limit is exceeded.

### 6.3 Role in session
After login you set `session['logged_in']` but not whether the user is student or teacher. If you ever have a shared page, you’ll need to check both.

- **Do:** Consider storing e.g. `session['role'] = 'student'` or `'teacher'` so protected routes can check `session.get('role')` and redirect accordingly.

---

## Summary

| Area            | Priority | Effort  | Notes                                      |
|-----------------|----------|---------|--------------------------------------------|
| Hash passwords  | High     | Medium  | Big security win                            |
| Logout          | High     | Low     | One route + links                           |
| Secret key      | High     | Low     | Env var for production                      |
| DB path / SQL   | High     | Done    | Fixed in code                               |
| Connection mgr  | High     | Medium  | Prevents leaks and double-connect           |
| Validation      | Medium   | Medium  | Better errors and safety                    |
| Flash messages  | Medium   | Low     | Cleaner UX                                  |
| Split app.py    | Medium   | High    | Easier to maintain and test                 |
| Logging         | Low      | Low     | Replace print with logging                  |
| .gitignore      | Medium   | Low     | Avoid committing secrets and generated files |
| init_db.py      | Medium   | Low     | Matches README and one-click setup          |

If you want to tackle one thing first, hashing passwords and adding logout give the best security gain for relatively little code change.
