# Schema Drift Audit Tool

## 🎯 Purpose

This tool verifies that your SQLAlchemy Models (Python code) match EXACTLY the running PostgreSQL Database Schema, detecting "Schema Drift" issues like:
- Primary key mismatches (e.g., `id` vs `activity_id`)
- Missing columns in database
- Extra columns not defined in models
- Nullable constraint mismatches

## 📦 Files Created

| File | Purpose |
|------|---------|
| `audit_schema.py` | Main audit script that compares models vs database |
| `find_db_password.py` | Helper to find correct PostgreSQL password |
| `reset_pg_password.ps1` | PowerShell script to reset PostgreSQL password (requires Admin) |

## 🚀 Quick Start

### Step 1: Check Database Connection

First, verify you can connect to PostgreSQL:

```powershell
# Check if PostgreSQL is running
Get-Service | Where-Object { $_.Name -like "*postgres*" }
```

### Step 2: Find Database Password

If you don't know the password:

```powershell
python find_db_password.py
```

This will try common passwords and tell you which one works.

### Step 3: Run Audit

#### Option A: Dry Run (No Database Connection Required)

```powershell
python audit_schema.py --dry-run
```

This shows what models would be audited without connecting to the database.

#### Option B: Full Audit (Requires Database Connection)

```powershell
python audit_schema.py
```

This connects to the database and performs a full comparison.

## 📊 Understanding Results

### ✅ Green Output (MATCH)
```
✅ SCHEMA MATCHES - All columns and primary keys are correct!
```
Everything is perfect! Your model matches the database exactly.

### ❌ Red Output (MISMATCH)

```
❌ SCHEMA MISMATCH DETECTED:
   ❌ Column 'id' defined in Model but MISSING in Database
   ❌ PRIMARY KEY MISMATCH:
      Model expects: ['id']
      Database has:  ['activity_id']
```

**What this means:**
- Your Python model defines a column `id` as primary key
- The database table has `activity_id` as primary key instead
- **Action needed:** Update your model to match the database (or vice versa)

### ⚠️ Yellow Output (WARNING)

```
⚠️  Column 'created_at' nullable mismatch: Model=False, DB=True
```

**What this means:**
- The column exists in both places but with different constraints
- **Action needed:** Decide which is correct and update accordingly

## 🔧 Troubleshooting

### Problem: "Password authentication failed"

**Solution 1:** Find the correct password
```powershell
python find_db_password.py
```

**Solution 2:** Reset the PostgreSQL password (requires Administrator)
```powershell
# Right-click PowerShell → Run as Administrator
.\reset_pg_password.ps1
```

**Solution 3:** Update .env file with correct password
```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@127.0.0.1:5433/ai_native
```

### Problem: "Database 'ai_native' does not exist"

**Solution:** Create the database
```powershell
# Use Docker Compose
docker-compose up -d postgres

# Wait for it to start, then initialize
python init_db.py
```

### Problem: "Table does not exist in database"

**Solution:** Run database migrations
```powershell
# Initialize database with all tables
python init_db.py

# Or use Docker setup
docker-compose up -d postgres
docker-compose exec postgres psql -U postgres -d ai_native -f /path/to/create_tables.sql
```

## 📝 Models Audited

The script checks these models:

1. **UserModel** → `users` table
2. **UserProfileModel** → `user_profiles` table
3. **SubjectModel** → `subjects` table
4. **CourseModel** → `courses` table
5. **CommissionModel** → `commissions` table
6. **ActivityModel** → `activities` table
7. **SessionModelV2** → `sessions_v2` table
8. **ExerciseModelV2** → `exercises_v2` table
9. **ExerciseAttemptModelV2** → `exercise_attempts_v2` table
10. **CognitiveTraceModelV2** → `cognitive_traces_v2` table
11. **RiskModelV2** → `risks_v2` table

## 🎯 Common Schema Drift Issues

### Issue 1: Primary Key Name Mismatch

**Example:**
```
❌ PRIMARY KEY MISMATCH:
   Model expects: ['id']
   Database has:  ['submission_id']
```

**Fix:** Update your model to use the same primary key name as the database:

```python
# Before (incorrect)
class SubmissionModel(Base):
    __tablename__ = "submissions"
    id = Column(String(36), primary_key=True)  # ❌ Wrong

# After (correct)
class SubmissionModel(Base):
    __tablename__ = "submissions"
    submission_id = Column(String(36), primary_key=True)  # ✅ Correct
```

### Issue 2: Missing Column in Database

**Example:**
```
❌ Column 'new_field' defined in Model but MISSING in Database
```

**Fix:** Add migration to create the column in database:

```sql
ALTER TABLE your_table ADD COLUMN new_field VARCHAR(255);
```

Or remove it from the model if it shouldn't be there.

### Issue 3: Extra Column in Database

**Example:**
```
⚠️  Column 'old_field' exists in Database but NOT in Model
```

**Fix:** Either:
1. Add the column to your model if you need it
2. Drop it from the database if it's obsolete:
```sql
ALTER TABLE your_table DROP COLUMN old_field;
```

## 🔍 Script Details

### audit_schema.py

**What it does:**
1. Imports all SQLAlchemy models
2. Connects to PostgreSQL database
3. Uses `sqlalchemy.inspect()` to get actual database schema
4. Compares model definitions vs database tables
5. Reports all mismatches with detailed information

**Key Checks:**
- ✅ Table existence
- ✅ Column names match
- ✅ Primary key names match
- ✅ Nullable constraints match
- ✅ Foreign key references

**Exit Codes:**
- `0` - All schemas match perfectly
- `1` - Schema mismatches detected or connection error

## 💡 Best Practices

1. **Run audit regularly** - Before deploying changes
2. **Fix mismatches immediately** - Don't let drift accumulate
3. **Use migrations** - Never manually alter production schemas
4. **Version control** - Keep models and migrations in sync
5. **Document changes** - Note why you made schema changes

## 📚 Related Files

- `backend/src_v3/infrastructure/persistence/sqlalchemy/simple_models.py` - Model definitions
- `create_tables.sql` - SQL schema definitions
- `init_db.py` - Database initialization script
- `.env` - Database connection configuration

## 🆘 Getting Help

If the audit tool shows errors:

1. **Read the exact error message** - It tells you precisely what's wrong
2. **Check both model and database** - Determine which is "correct"
3. **Update the incorrect side** - Either model or database
4. **Re-run audit** - Verify the fix worked

---

**Created by:** Schema Audit Tool Generator  
**Last Updated:** January 2026  
**Version:** 1.0
