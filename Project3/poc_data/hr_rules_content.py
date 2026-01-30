"""
HR Policy document content for POC (Project3).
Includes Leave, Attendance, Code of Conduct, Asset Distribution, Expense, Grievance.
Used by generate_poc_data.py to create PDFs. Section titles aid RAG retrieval.
"""

# =============================================================================
# LEAVE POLICY
# =============================================================================
LEAVE_POLICY = """
HR POLICY DOCUMENT
Leave & Time-Off Policy
Effective: January 2025 | Version 1.0

1. PURPOSE
This policy outlines the leave entitlements, application process, and guidelines for all employees.

2. LEAVE TYPES
- Annual Leave: 20 days per year (pro-rated for joiners)
- Sick Leave: 10 days per year (medical certificate required after 3 consecutive days)
- Casual Leave: 5 days per year (no prior approval for 1 day)
- Maternity/Paternity: As per statutory requirements

3. ANNUAL LEAVE RULES
- Leave balance must be between 0 and 30 days at any time
- Leave application must be submitted at least 7 days in advance for planned leave
- Emergency leave: notify manager and HR within 24 hours
- Unused leave up to 5 days may be carried forward to next year (subject to approval)
- Leave cannot be encashed except at separation

4. APPLICATION PROCESS
- Submit leave request via HR portal or email to manager and HR
- Manager approval required for leave of 1-3 days
- Manager + HR approval required for leave of 4+ days
- Leave is deducted only upon approval

5. BLACKOUT PERIODS
- No leave during month-end closure (last 3 working days of month) except emergency
- Department-specific blackout periods may apply (e.g., audit season)

6. CONTACT
HR Helpdesk: hr@company.com | Leave queries: leave@company.com
"""

# =============================================================================
# ATTENDANCE POLICY
# =============================================================================
ATTENDANCE_POLICY = """
HR POLICY DOCUMENT
Attendance & Timesheet Policy
Effective: January 2025 | Version 1.0

1. PURPOSE
This policy defines attendance expectations, working hours, and timesheet requirements.

2. WORKING HOURS
- Standard hours: 9:00 AM to 6:00 PM (including 1 hour break)
- Flexible window: Check-in between 8:00 AM - 10:00 AM; Check-out 8 hours from check-in
- Core hours (mandatory): 10:00 AM - 4:00 PM for collaboration

3. ATTENDANCE MARKING
- All employees must mark attendance daily (check-in and check-out)
- Attendance can only be marked if employee license/access is valid
- Mark attendance via HR portal, biometric, or approved system
- Default check-in: 09:00, Default check-out: 17:00 if not specified

4. TIMESHEET RULES
- Weekly timesheet submission by Friday EOD for the week
- Minimum 40 hours per week (excluding leave/public holidays)
- Overtime: Pre-approval required; compensatory leave or payment as per policy
- Future-dated attendance is not allowed

5. LATE ARRIVAL / EARLY DEPARTURE
- Late up to 3 times per month: No penalty (inform manager)
- Pattern of late arrival: Discussion with manager and HR
- Half-day: Minimum 4 hours to be marked as present

6. REMOTE WORK
- As per department policy; attendance and timesheet still mandatory
- Same check-in/check-out rules apply

7. CONTACT
HR Helpdesk: hr@company.com | Attendance issues: attendance@company.com
"""

# =============================================================================
# CODE OF CONDUCT
# =============================================================================
CODE_OF_CONDUCT = """
HR POLICY DOCUMENT
Code of Conduct & Ethics
Effective: January 2025 | Version 1.0

1. PURPOSE
This code outlines expected behavior, ethics, and standards for all employees.

2. CORE VALUES
- Integrity: Honest and transparent in all dealings
- Respect: Treat everyone with dignity and respect
- Accountability: Take responsibility for actions and outcomes
- Excellence: Strive for quality in work and conduct

3. WORKPLACE CONDUCT
- No discrimination on basis of gender, race, religion, or any protected characteristic
- No harassment (including sexual harassment); zero tolerance policy
- Confidentiality: Do not disclose company or customer information without authorization
- Conflict of interest must be disclosed to manager and HR

4. IT & ASSETS
- Company assets (laptop, ID, access) are for official use only
- License/access must be kept valid; report loss or misuse immediately
- Use of company systems must comply with IT policy

5. DISCIPLINARY ACTION
- Violations may result in warning, suspension, or termination
- Serious violations (fraud, harassment) may lead to immediate termination and legal action

6. REPORTING
- Report concerns to manager, HR, or ethics@company.com
- Whistleblower policy protects good-faith reporters

7. CONTACT
HR: hr@company.com | Ethics: ethics@company.com
"""

# =============================================================================
# ASSET DISTRIBUTION & MANAGEMENT POLICY
# =============================================================================
ASSET_DISTRIBUTION_POLICY = """
HR POLICY DOCUMENT
Asset Distribution & Management Policy
Effective: January 2025 | Version 1.0

1. PURPOSE
This policy governs the allocation, use, and return of company assets (laptops, mobiles, ID cards, access devices, and other IT/office equipment).

2. ELIGIBILITY & ALLOCATION
- Full-time employees are eligible for standard asset kit (laptop, ID, access card) on joining
- Role-based assets (mobile, headset, monitor) require manager and IT approval
- Asset distribution is coordinated by IT and Admin; HR maintains records
- New joiners receive assets within 3 working days of completing onboarding

3. ASSET TYPES & STANDARD KIT
- Laptop: Standard issue for all; upgrade on approval
- ID card & access card: Mandatory; replacement fee if lost
- Mobile phone: For roles with field/client contact; optional for others
- Desk equipment: Monitor, keyboard, mouse as per workspace policy

4. CUSTODY & USE
- Assets are for official use only; personal use must comply with IT policy
- Employee is responsible for safekeeping; loss or damage must be reported within 24 hours
- Theft or misuse may result in recovery cost and disciplinary action
- License and system access must remain valid for continued use

5. RETURN & EXIT
- All assets must be returned on separation (resignation, termination, retirement)
- Clearance form signed by IT and Admin before final settlement
- Unreturned or damaged assets may be deducted from dues or pursued legally
- Data on devices must be wiped as per IT checklist

6. REPLACEMENT & UPGRADE
- Replacement: Request via IT portal; approval based on warranty and need
- Upgrade: Manager approval and budget; cycle typically 3–4 years for laptops
- Lost/stolen: Report to IT and Security; replacement may incur cost as per policy

7. CONTACT
IT Asset Desk: assets@company.com | HR (records): hr@company.com
"""

# =============================================================================
# EXPENSE & REIMBURSEMENT POLICY
# =============================================================================
EXPENSE_POLICY = """
HR POLICY DOCUMENT
Expense & Reimbursement Policy
Effective: January 2025 | Version 1.0

1. PURPOSE
This policy defines eligible expenses, approval limits, and reimbursement process for official expenditure.

2. ELIGIBLE EXPENSES
- Travel: Flights, cab, train as per travel policy; economy unless approved
- Meals: Per diem or actuals within limit during official travel
- Conferences & training: Pre-approved with budget code
- Office supplies: Via central procurement; emergency local purchase with manager approval
- Client entertainment: Pre-approval required; within annual limit per employee

3. APPROVAL LIMITS
- Up to INR 5,000: Manager approval
- INR 5,001 – 25,000: Manager + Department head
- Above INR 25,000: Finance approval in addition
- Travel and client entertainment: As per separate delegation matrix

4. SUBMISSION & REIMBURSEMENT
- Submit claims within 30 days of expense; beyond 60 days may not be entertained
- Original receipts and supporting documents mandatory
- Reimbursement via payroll or direct credit within 2 weeks of approval
- Falsification of claims is gross misconduct and may lead to termination

5. NON-REIMBURSABLE
- Personal expenses, fines, penalties
- Expenses without prior approval where policy requires it
- Alcohol (unless explicitly allowed for client events as per policy)

6. CONTACT
Finance: expenses@company.com | HR (policy): hr@company.com
"""

# =============================================================================
# GRIEVANCE REDRESSAL POLICY
# =============================================================================
GRIEVANCE_POLICY = """
HR POLICY DOCUMENT
Grievance Redressal Policy
Effective: January 2025 | Version 1.0

1. PURPOSE
This policy provides a fair and confidential mechanism for employees to raise grievances and seek resolution.

2. SCOPE
- Grievances may relate to work conditions, interpersonal issues, discrimination, harassment, leave, attendance, appraisal, or any policy interpretation
- This does not replace statutory channels (e.g., POSH committee for sexual harassment)

3. CHANNELS FOR RAISING GRIEVANCE
- Primary: Discuss with immediate manager
- Escalation: HR business partner or grievance@company.com
- Anonymous: Whistleblower channel (ethics@company.com) for sensitive cases
- Grievance may be raised in writing (email or portal) with brief description and desired outcome

4. PROCESS & TIMELINES
- Acknowledgement within 2 working days
- Preliminary discussion with employee and relevant parties within 5 working days
- Resolution or written response within 15 working days; complex cases may extend with notice
- Employee may appeal once to the next level (Department head / HR head) within 7 days of response

5. CONFIDENTIALITY & NON-RETALIATION
- Grievances are treated confidentially to the extent possible
- No retaliation against employees for raising grievances in good faith
- Retaliation is a separate violation and may result in disciplinary action

6. RECORDS
- HR maintains summary records (without identity where anonymous) for trend analysis and policy review
- Individual case details are stored as per data retention policy

7. CONTACT
Grievance: grievance@company.com | HR: hr@company.com | Ethics: ethics@company.com
"""

# Export all for generator script
POLICIES = {
    "Leave_Policy": LEAVE_POLICY,
    "Attendance_Policy": ATTENDANCE_POLICY,
    "Code_of_Conduct": CODE_OF_CONDUCT,
    "Asset_Distribution_Policy": ASSET_DISTRIBUTION_POLICY,
    "Expense_Policy": EXPENSE_POLICY,
    "Grievance_Policy": GRIEVANCE_POLICY,
}
