---
description: Create a single dummy user in database
allowed-tools: Read, Bash(python3:*)
---

Read `database/db.py` to understand the users table schema and the `get_db()` helper.

Then write and execute a Python script using Bash that performs the following steps:

1. Generate a realistic fictional Indian user using a first name and last name from any Indian region.
2. Generate an email address derived from the user's name, followed by a random 2–3 digit suffix (for example, `rahul.sharma91@gmail.com`).
3. Set the password to `password123` and hash it using Werkzeug's `generate_password_hash`.
4. Set `created_at` to the current datetime, following the format and conventions used in the existing project.
5. Check whether the generated email already exists in the `users` table. If it does, generate another email and repeat the check until a unique email is found.
6. Insert exactly one user into the database using the existing `get_db()` helper and the database access pattern found in `database/db.py`.
7. Commit the transaction if required by the existing database implementation.
8. Verify that the user was successfully inserted.
9. Print a confirmation containing only:
   - User ID
   - Name
   - Email

Constraints:
- Do not modify existing application source files or database schemas.
- Do not delete or update existing users.
- Use parameterized SQL queries to prevent SQL injection.
- Do not print the password or its hash.
- If the schema, database connection, or required fields are unclear, ask for clarification rather than guessing.
- Ensure the script closes the database connection or releases resources according to the existing project's conventions.