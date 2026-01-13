# PostgreSQL Setup Guide

## Step 1: Check if PostgreSQL is Running

PostgreSQL is already installed (version 17.5). Let's make sure it's running:

```powershell
# Check PostgreSQL service status
Get-Service -Name "*postgresql*"
```

If it's not running, start it:
```powershell
# Start PostgreSQL service (adjust service name if needed)
Start-Service postgresql-x64-17
# OR
Start-Service postgresql-x64-16
```

## Step 2: Find Your PostgreSQL Password

You need the password for the `postgres` user. This was set during PostgreSQL installation.

**If you forgot the password:**
1. Open pgAdmin (PostgreSQL GUI tool) - it might be installed
2. Or reset it via command line (see below)

## Step 3: Test Connection

Test if you can connect to PostgreSQL:

```powershell
# Try connecting (it will prompt for password)
psql -U postgres -h localhost
```

If successful, you'll see:
```
postgres=#
```

Type `\q` to quit.

## Step 4: Create .env File

Create a `.env` file in `E:\ADK\` with your PostgreSQL credentials:

```env
# PostgreSQL Connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=employees_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_actual_password_here
```

**Important:** Replace `your_actual_password_here` with your actual PostgreSQL password!

## Step 5: Run Database Setup

Once your `.env` file is configured, run:

```powershell
python database_setup.py
```

This will:
- Create the `employees_db` database
- Create the `employees` table
- Insert 12 sample employee records

## Troubleshooting

### "Password authentication failed"
- Check your `.env` file has the correct password
- Try resetting PostgreSQL password (see below)

### "Connection refused" or "Service not running"
- Start PostgreSQL service:
  ```powershell
  Start-Service postgresql-x64-17
  ```

### "Database already exists"
- That's fine! The script will skip creation and continue

### Reset PostgreSQL Password (if needed)

1. Edit `pg_hba.conf` file (usually in `C:\Program Files\PostgreSQL\17\data\`)
2. Change `md5` to `trust` for local connections
3. Restart PostgreSQL service
4. Connect without password: `psql -U postgres`
5. Change password: `ALTER USER postgres WITH PASSWORD 'newpassword';`
6. Change `pg_hba.conf` back to `md5`
7. Restart PostgreSQL service

## Quick Test

After setup, test the connection:

```python
python -c "import psycopg2; from dotenv import load_dotenv; import os; load_dotenv(); conn = psycopg2.connect(host=os.getenv('POSTGRES_HOST'), port=os.getenv('POSTGRES_PORT'), database=os.getenv('POSTGRES_DB'), user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD')); print('✓ Connection successful!'); conn.close()"
```





