# Full DB setup (copy / recreate database)

Use this to set up the whole database from scratch (schema + seed data with emails and passwords).

## 1. Create the database (once)

If `employees_db` does not exist yet:

**PostgreSQL (psql):**
```sql
CREATE DATABASE employees_db;
```

**Or from shell:**
```bash
createdb -h localhost -U postgres employees_db
```

## 2. Configure connection

Ensure `.env` in the project root has:

- `PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE=employees_db`

(Or `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.)

## 3. Run setup

From the **Project3** folder:

```bash
python setup_db.py
```

This will:

- Create tables: `employees` (with email, password, employee_code), `attendance`
- Add 6-digit Employee ID (`employee_code`: 100001, 100002, …)
- Create trigger for new rows
- Insert seed employees with **email** and **password**
- Insert sample attendance rows

## 4. Seed data (passwords and emails)

| Name             | Email                      | Password | Role   |
|------------------|----------------------------|----------|--------|
| James Garcia     | james.garcia@gmail.com     | 11111111 | HR     |
| John Smith       | john.smith@gmail.com       | 00000000 | Employee |
| Sarah Johnson    | sarah.johnson@gmail.com    | 00000000 | Employee |
| Mike Davis       | mike.davis@gmail.com       | 00000000 | Employee |
| Emily Brown      | emily.brown@gmail.com      | 00000000 | Employee |
| David Wilson     | david.wilson@gmail.com     | 00000000 | Employee |
| Lisa Anderson    | lisa.anderson@gmail.com    | 00000000 | Employee |
| Robert Taylor    | robert.taylor@gmail.com    | 00000000 | Employee |
| Jennifer Martinez | jennifer.martinez@gmail.com| 00000000 | Employee |
| Amanda Lee       | amanda.lee@gmail.com       | 00000000 | Employee |
| Test Employee    | test.employee@gmail.com    | 00000000 | Employee |

**HR login:** `james.garcia@gmail.com` / `11111111`  
**All others:** use email or name, password `00000000`.

## 5. Verify

```bash
python show_db.py
```

## Manual SQL

To run the SQL yourself (e.g. in Azure Data Studio or psql):

```bash
psql -h localhost -U postgres -d employees_db -f setup_db.sql
```

Or open `setup_db.sql` and run it against `employees_db`.
