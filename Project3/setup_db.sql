-- =============================================================================
-- Full DB setup for HR Help Service (Project3)
-- Run with: python setup_db.py  (uses .env for connection)
-- Or run this SQL manually against employees_db (create DB first if needed).
-- Includes: schema (employees + attendance), employee_code, trigger, seed data
-- Passwords: James Garcia (HR) = 11111111; all others = 00000000
-- =============================================================================

-- Drop existing objects so we can recreate (optional; comment out if you want to preserve data)
-- DROP TRIGGER IF EXISTS trg_set_employee_code ON employees;
-- DROP FUNCTION IF EXISTS set_employee_code();
-- DROP TABLE IF EXISTS attendance;
-- DROP TABLE IF EXISTS employees;

-- -----------------------------------------------------------------------------
-- 1. Employees table (with email, password, employee_code)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employees (
    employee_id     INTEGER PRIMARY KEY,
    employee_name   VARCHAR(100) NOT NULL,
    department      VARCHAR(50),
    license_valid   SMALLINT DEFAULT 1,
    date_of_joining DATE,
    leave_available INTEGER DEFAULT 0,
    email           VARCHAR(255),
    password        VARCHAR(100),
    employee_code   VARCHAR(6) UNIQUE
);

-- 2. Employee code: 6-digit company ID (100001, 100002, ...)
ALTER TABLE employees ADD COLUMN IF NOT EXISTS employee_code VARCHAR(6);

-- 3. Trigger function for new rows
CREATE OR REPLACE FUNCTION set_employee_code()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.employee_code IS NULL OR NEW.employee_code = '' THEN
    NEW.employee_code := LPAD((100000 + NEW.employee_id)::text, 6, '0');
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_employee_code ON employees;
CREATE TRIGGER trg_set_employee_code
  BEFORE INSERT ON employees
  FOR EACH ROW EXECUTE PROCEDURE set_employee_code();

-- -----------------------------------------------------------------------------
-- 4. Attendance table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id   SERIAL PRIMARY KEY,
    employee_id     INTEGER NOT NULL REFERENCES employees(employee_id),
    date            DATE NOT NULL,
    check_in_time   TIME DEFAULT '09:00',
    check_out_time  TIME DEFAULT '17:00'
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_emp_date ON attendance (employee_id, date);

-- -----------------------------------------------------------------------------
-- 5. Seed employees (email + password for each)
-- HR = James Garcia, password 11111111; all others = 00000000
-- -----------------------------------------------------------------------------
INSERT INTO employees (employee_id, employee_name, department, license_valid, date_of_joining, leave_available, email, password, employee_code)
VALUES
    (1,  'John Smith',         'Engineering', 1, '2022-01-15', 20, 'john.smith@gmail.com',         '00000000', '100001'),
    (2,  'Sarah Johnson',     'Engineering', 1, '2023-03-20', 18, 'sarah.johnson@gmail.com',      '00000000', '100002'),
    (3,  'Mike Davis',        'Engineering', 0, '2024-01-10', 15, 'mike.davis@gmail.com',        '00000000', '100003'),
    (4,  'Emily Brown',       'Sales',       1, '2021-06-01', 22, 'emily.brown@gmail.com',       '00000000', '100004'),
    (5,  'David Wilson',      'Sales',       1, '2023-08-15', 18, 'david.wilson@gmail.com',       '00000000', '100005'),
    (6,  'Lisa Anderson',     'Sales',       0, '2024-02-05', 20, 'lisa.anderson@gmail.com',      '00000000', '100006'),
    (7,  'Robert Taylor',     'Marketing',   1, '2022-09-10', 19, 'robert.taylor@gmail.com',     '00000000', '100007'),
    (8,  'Jennifer Martinez', 'Marketing',   1, '2023-11-01', 17, 'jennifer.martinez@gmail.com', '00000000', '100008'),
    (9,  'James Garcia',      'HR',          1, '2020-04-01', 15, 'james.garcia@gmail.com',      '11111111', '100009'),
    (10, 'Amanda Lee',        'HR',          0, '2023-05-20',  0, 'amanda.lee@gmail.com',        '00000000', '100010'),
    (11, 'Test Employee',     'IT',          1, '2026-01-27', 20, 'test.employee@gmail.com',      '00000000', '100011')
ON CONFLICT (employee_id) DO UPDATE SET
    employee_name   = EXCLUDED.employee_name,
    department      = EXCLUDED.department,
    license_valid   = EXCLUDED.license_valid,
    date_of_joining = EXCLUDED.date_of_joining,
    leave_available = EXCLUDED.leave_available,
    email           = EXCLUDED.email,
    password        = EXCLUDED.password,
    employee_code   = EXCLUDED.employee_code;

-- -----------------------------------------------------------------------------
-- 6. Seed attendance (sample records)
-- -----------------------------------------------------------------------------
INSERT INTO attendance (employee_id, date, check_in_time, check_out_time)
VALUES
    (1, '2026-01-24', '09:01:00', '17:31:00'),
    (1, '2026-01-25', '09:01:00', '17:31:00'),
    (1, '2026-01-26', '09:01:00', '17:31:00'),
    (2, '2026-01-25', '09:02:00', '17:30:00'),
    (2, '2026-01-26', '09:02:00', '17:30:00'),
    (2, '2026-01-27', '09:02:00', '17:30:00'),
    (4, '2026-01-25', '09:01:00', '17:30:00'),
    (4, '2026-01-26', '09:01:00', '17:30:00'),
    (4, '2026-01-27', '09:01:00', '17:30:00'),
    (5, '2026-01-25', '09:02:00', '17:31:00'),
    (5, '2026-01-26', '09:02:00', '17:31:00'),
    (5, '2026-01-27', '09:02:00', '17:31:00'),
    (7, '2026-01-25', '09:01:00', '17:31:00'),
    (7, '2026-01-26', '09:01:00', '17:31:00'),
    (7, '2026-01-27', '09:01:00', '17:31:00')
ON CONFLICT (employee_id, date) DO NOTHING;
