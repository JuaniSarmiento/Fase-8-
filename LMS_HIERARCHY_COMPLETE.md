# 🏗️ LMS Hierarchical Architecture - Implementation Complete

## 📋 Executive Summary

The MVP has been refactored from a flat structure to a proper **LMS hierarchical architecture** with:

1. **Module System** - Course → Module → Activity hierarchy
2. **Enrollment System** - Many-to-Many Users ↔ Courses with roles
3. **Gamification System** - XP, levels, streaks, achievements

This replaces the simple `course_id` foreign key in `UserProfile` with a flexible enrollment system supporting multiple courses per user and role-based access control.

---

## 🗂️ Architecture Changes

### Before (Flat Structure)
```
UserProfile
  ├── course_id (FK) → Course
  └── commission_id (FK) → Commission

Activity
  ├── course_id (FK) → Course
  └── exercises[]
```

**Problems:**
- One user = one course (no multi-course enrollment)
- No hierarchical content organization
- No role differentiation (student vs teacher)
- No gamification

### After (LMS Hierarchy)
```
User
  └── Enrollments[] (Many-to-Many with role)
        └── Course
              └── Modules[] (ordered)
                    └── Activities[] (ordered)
                          └── Exercises[]

User
  └── Gamification (1-to-1)
        ├── XP, Level
        ├── Streaks
        └── Achievements
```

**Benefits:**
- ✅ Multi-course enrollment per user
- ✅ Role-based access (STUDENT, TEACHER, TA, OBSERVER)
- ✅ Hierarchical content (Modules group Activities)
- ✅ Ordered content (order_index fields)
- ✅ Gamification integrated
- ✅ Flexible metadata (JSONB fields)

---

## 📦 New Database Tables

### 1. `modules`
Organizes activities within courses.

```sql
CREATE TABLE modules (
    module_id VARCHAR(36) PRIMARY KEY,
    course_id VARCHAR(36) REFERENCES courses(course_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL DEFAULT 0,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    metadata_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Indexes:**
- `idx_modules_course` - Fast course → modules lookup
- `idx_modules_course_order` - Ordered retrieval
- `idx_modules_published` - Filter published modules

### 2. `enrollments`
Many-to-Many relationship between users and courses with roles.

```sql
CREATE TABLE enrollments (
    enrollment_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    course_id VARCHAR(36) REFERENCES courses(course_id) ON DELETE CASCADE,
    role enrollment_role NOT NULL DEFAULT 'STUDENT',
    status enrollment_status NOT NULL DEFAULT 'ACTIVE',
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    dropped_at TIMESTAMPTZ,
    metadata_json JSONB DEFAULT '{}',
    UNIQUE(user_id, course_id)
);
```

**Enums:**
- `enrollment_role`: `STUDENT`, `TEACHER`, `TA`, `OBSERVER`
- `enrollment_status`: `ACTIVE`, `INACTIVE`, `COMPLETED`, `DROPPED`

**Indexes:**
- `idx_enrollments_user` - User → enrollments
- `idx_enrollments_course` - Course → enrollments
- `idx_enrollments_user_course` (UNIQUE) - Prevent duplicate enrollments
- `idx_enrollments_status` - Filter by status
- `idx_enrollments_role` - Filter by role

### 3. `user_gamification`
Tracks XP, levels, and engagement metrics.

```sql
CREATE TABLE user_gamification (
    user_id VARCHAR(36) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    streak_days INTEGER NOT NULL DEFAULT 0,
    last_activity_date DATE,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    achievements JSONB DEFAULT '[]',
    badges JSONB DEFAULT '[]',
    total_exercises_completed INTEGER NOT NULL DEFAULT 0,
    total_activities_completed INTEGER NOT NULL DEFAULT 0,
    total_hints_used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Indexes:**
- `idx_gamification_user` - User lookup
- `idx_gamification_level` - Leaderboards by level
- `idx_gamification_xp` - Leaderboards by XP

---

## 🔄 Updated Tables

### `activities`
**Added columns:**
```sql
ALTER TABLE activities ADD COLUMN module_id VARCHAR(36) REFERENCES modules(module_id) ON DELETE CASCADE;
ALTER TABLE activities ADD COLUMN order_index INTEGER NOT NULL DEFAULT 0;
```

**Purpose:** Activities now belong to modules for hierarchical organization.

### `exercises_v2`
**Added columns:**
```sql
ALTER TABLE exercises_v2 ADD COLUMN reference_solution TEXT;
ALTER TABLE exercises_v2 ADD COLUMN grading_config JSONB DEFAULT '{}';
```

**Purpose:** Enhanced AI grading with reference solutions and configurable rubrics.

### `user_profiles`
**Deprecated columns (not dropped yet):**
- `course_id` - Use `enrollments` instead
- `commission_id` - Use `enrollments.metadata_json` instead

**Note:** Columns kept for backward compatibility during transition period.

---

## 📄 New Code Files

### Models
1. **`module_model.py`** - ModuleModel SQLAlchemy class
2. **`enrollment_model.py`** - EnrollmentModel with enums
3. **`gamification_model.py`** - UserGamificationModel
4. **Updated `__init__.py`** - Exports new models

### Schemas
1. **`lms_hierarchy_schemas.py`**
   - `ModuleCreate`, `ModuleRead`, `ModuleUpdate`
   - `EnrollmentCreate`, `EnrollmentRead`, `EnrollmentUpdate`
   - `UserGamificationCreate`, `UserGamificationRead`, `UserGamificationUpdate`
   - `CourseWithModules` - Nested structure for student view

### Migration
1. **`migrate_lms_hierarchy.sql`** - Complete SQL migration script
2. **`apply_lms_migration.py`** - Python migration tool with rollback

---

## 🚀 Migration Guide

### 1. Apply Migration

**Option A: Direct SQL**
```bash
psql -U postgres -d inteligencia_artificial -f migrate_lms_hierarchy.sql
```

**Option B: Python Script (Recommended)**
```bash
python apply_lms_migration.py
```

### 2. Verify Migration
```sql
-- Check new tables
SELECT COUNT(*) FROM modules;
SELECT COUNT(*) FROM enrollments;
SELECT COUNT(*) FROM user_gamification;

-- Check enrollment distribution
SELECT role, status, COUNT(*) 
FROM enrollments 
GROUP BY role, status;

-- Check activities with modules
SELECT COUNT(*) FROM activities WHERE module_id IS NOT NULL;
```

### 3. Data Migration Notes
- **Automatic enrollment creation**: Existing `user_profiles.course_id` relationships are migrated to `enrollments` table
- **Gamification initialization**: All existing users get a gamification record with default values (XP=0, Level=1)
- **Backward compatibility**: `course_id` and `commission_id` columns in `user_profiles` are NOT dropped yet

### 4. Rollback (if needed)
```bash
python apply_lms_migration.py --rollback
```

**⚠️ WARNING:** Rollback will delete modules, enrollments, and gamification data!

---

## 🔌 API Updates Needed

### Teacher Router (`teacher_router.py`)

#### New Endpoints to Implement

1. **Create Module**
```python
@router.post("/courses/{course_id}/modules", response_model=ModuleRead)
async def create_module(
    course_id: str,
    module_data: ModuleCreate,
    current_user: UserModel = Depends(get_current_teacher),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new module in a course"""
    # 1. Verify teacher has access to course (via enrollments)
    # 2. Generate module_id = str(uuid.uuid4())
    # 3. Create ModuleModel instance
    # 4. session.add(), session.commit()
    # 5. Return ModuleRead
```

2. **Update Module**
```python
@router.put("/modules/{module_id}", response_model=ModuleRead)
async def update_module(
    module_id: str,
    module_data: ModuleUpdate,
    current_user: UserModel = Depends(get_current_teacher),
    session: AsyncSession = Depends(get_async_session)
):
    """Update module details"""
```

3. **List Course Modules**
```python
@router.get("/courses/{course_id}/modules", response_model=List[ModuleRead])
async def list_course_modules(
    course_id: str,
    include_unpublished: bool = False,
    current_user: UserModel = Depends(get_current_teacher),
    session: AsyncSession = Depends(get_async_session)
):
    """List all modules in a course"""
```

4. **Reorder Modules**
```python
@router.put("/courses/{course_id}/modules/reorder")
async def reorder_modules(
    course_id: str,
    module_ids: List[str],  # Ordered list
    current_user: UserModel = Depends(get_current_teacher),
    session: AsyncSession = Depends(get_async_session)
):
    """Update order_index for all modules"""
```

#### Update Existing Endpoints

1. **Create Activity** - Add `module_id` parameter
```python
@router.post("/activities", response_model=ActivityRead)
async def create_activity(
    activity_data: ActivityCreate,  # Should include module_id
    current_user: UserModel = Depends(get_current_teacher),
    session: AsyncSession = Depends(get_async_session)
):
    """Create activity within a module"""
    # Verify teacher has access via enrollment
```

### Student Router (`student_router.py`)

#### Update Access Control

**OLD (using course_id):**
```python
# Get user's course from profile
user_profile = await session.execute(
    select(UserProfileModel).where(UserProfileModel.user_id == user.id)
)
profile = user_profile.scalar_one()

# Query activities
activities = await session.execute(
    select(ActivityModel).where(ActivityModel.course_id == profile.course_id)
)
```

**NEW (using enrollments):**
```python
# Get user's enrollments
enrollments = await session.execute(
    select(EnrollmentModel).where(
        EnrollmentModel.user_id == user.id,
        EnrollmentModel.status == EnrollmentStatus.ACTIVE
    )
)
user_enrollments = enrollments.scalars().all()

# For specific course
enrollment = await session.execute(
    select(EnrollmentModel).where(
        EnrollmentModel.user_id == user.id,
        EnrollmentModel.course_id == course_id,
        EnrollmentModel.status == EnrollmentStatus.ACTIVE
    )
)
```

#### Update Response Structure

**OLD (flat activities):**
```json
{
  "activities": [
    {"activity_id": "...", "title": "Activity 1"},
    {"activity_id": "...", "title": "Activity 2"}
  ]
}
```

**NEW (grouped by modules):**
```json
{
  "course": {
    "course_id": "...",
    "name": "Programación I",
    "modules": [
      {
        "module_id": "...",
        "title": "Módulo 1: Introducción",
        "order_index": 0,
        "activities": [
          {"activity_id": "...", "title": "Variables", "order_index": 0},
          {"activity_id": "...", "title": "Operadores", "order_index": 1}
        ]
      },
      {
        "module_id": "...",
        "title": "Módulo 2: Control de Flujo",
        "order_index": 1,
        "activities": [...]
      }
    ]
  }
}
```

#### Gamification Endpoints

1. **Get User Gamification**
```python
@router.get("/gamification", response_model=UserGamificationRead)
async def get_user_gamification(
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get current user's gamification stats"""
```

2. **Update Streak (internal)**
```python
async def update_streak(user_id: str, session: AsyncSession):
    """Update user's activity streak"""
    # Get gamification record
    # Check last_activity_date
    # Update streak_days if consecutive
    # Reset to 1 if gap
```

---

## ✅ Testing Checklist

### Database Tests
- [ ] Run migration SQL successfully
- [ ] Verify all 3 new tables exist
- [ ] Check enrollments migrated from user_profiles
- [ ] Verify gamification records created for all users
- [ ] Test unique constraint on (user_id, course_id) in enrollments

### Model Tests
```python
# Test module creation
module = ModuleModel(
    module_id=str(uuid.uuid4()),
    course_id=course.course_id,
    title="Test Module",
    order_index=0
)

# Test enrollment creation
enrollment = EnrollmentModel(
    enrollment_id=str(uuid.uuid4()),
    user_id=user.id,
    course_id=course.course_id,
    role=EnrollmentRole.STUDENT
)

# Test gamification
gamification = UserGamificationModel(
    user_id=user.id,
    xp=100,
    level=2
)
```

### API Tests
- [ ] Teacher can create modules
- [ ] Teacher can update module order
- [ ] Teacher can create activities with module_id
- [ ] Student sees activities grouped by modules
- [ ] Student can access only enrolled courses
- [ ] Gamification endpoints work
- [ ] Multi-course enrollment works (user in 2+ courses)

---

## 📊 Performance Considerations

### Indexes Applied
- **Modules**: 3 indexes (course, course+order, published)
- **Enrollments**: 5 indexes (user, course, user+course unique, status, role)
- **Gamification**: 3 indexes (user, level, xp)
- **Activities**: 2 new indexes (module, module+order)

### Query Optimization

**Nested queries for student view:**
```sql
-- Get course with modules and activities
SELECT 
    c.course_id, c.name,
    m.module_id, m.title, m.order_index,
    a.activity_id, a.title, a.order_index
FROM enrollments e
JOIN courses c ON e.course_id = c.course_id
LEFT JOIN modules m ON c.course_id = m.course_id AND m.is_published = TRUE
LEFT JOIN activities a ON m.module_id = a.module_id
WHERE e.user_id = :user_id AND e.status = 'ACTIVE'
ORDER BY c.course_id, m.order_index, a.order_index;
```

**Use SQLAlchemy `selectinload` for N+1 prevention:**
```python
from sqlalchemy.orm import selectinload

courses = await session.execute(
    select(CourseModel)
    .options(
        selectinload(CourseModel.modules).selectinload(ModuleModel.activities)
    )
    .join(EnrollmentModel)
    .where(EnrollmentModel.user_id == user.id)
)
```

---

## 🎯 Next Steps (Priority Order)

### 1. Update Routers (CRITICAL - Required for API to work)
- [ ] Update `teacher_router.py` with module CRUD endpoints
- [ ] Update `student_router.py` to use Enrollment joins
- [ ] Add enrollment management endpoints (enroll student, change role)
- [ ] Implement module-grouped responses

### 2. Frontend Updates
- [ ] Update student dashboard to show modules
- [ ] Add module management UI for teachers
- [ ] Display gamification stats (XP, level, streak)
- [ ] Add progress bars by module

### 3. Gamification Logic
- [ ] Implement XP calculation rules
- [ ] Define level thresholds (e.g., Level 2 = 100 XP, Level 3 = 300 XP)
- [ ] Create achievement definitions
- [ ] Implement streak tracking (daily activity check)

### 4. Advanced Features
- [ ] Module prerequisites (Module 2 unlocks after Module 1)
- [ ] Adaptive module ordering based on performance
- [ ] Leaderboards (by course, by level)
- [ ] Badge system UI

### 5. Documentation
- [ ] Update API documentation with new endpoints
- [ ] Create teacher guide for module creation
- [ ] Student guide for multi-course navigation

---

## 🔍 Debugging Tips

### Check Enrollment Access
```sql
-- See all user enrollments
SELECT u.name, c.name AS course, e.role, e.status
FROM enrollments e
JOIN users u ON e.user_id = u.id
JOIN courses c ON e.course_id = c.course_id
WHERE u.id = :user_id;
```

### Check Module Hierarchy
```sql
-- See course → module → activity structure
SELECT 
    c.name AS course,
    m.title AS module,
    m.order_index AS m_order,
    a.title AS activity,
    a.order_index AS a_order
FROM courses c
LEFT JOIN modules m ON c.course_id = m.course_id
LEFT JOIN activities a ON m.module_id = a.module_id
WHERE c.course_id = :course_id
ORDER BY m.order_index, a.order_index;
```

### Check Gamification Stats
```sql
-- Top 10 users by XP
SELECT u.name, g.xp, g.level, g.streak_days
FROM user_gamification g
JOIN users u ON g.user_id = u.id
ORDER BY g.xp DESC
LIMIT 10;
```

---

## 📚 References

- **Migration SQL**: `migrate_lms_hierarchy.sql`
- **Migration Script**: `apply_lms_migration.py`
- **Models**: `backend/src_v3/infrastructure/persistence/sqlalchemy/models/`
  - `module_model.py`
  - `enrollment_model.py`
  - `gamification_model.py`
- **Schemas**: `backend/src_v3/application/schemas/lms_hierarchy_schemas.py`
- **Security Improvements**: `SECURITY_IMPROVEMENTS_DONE.md`

---

## ✅ Migration Status

**Completed:**
- ✅ Created ModuleModel, EnrollmentModel, UserGamificationModel
- ✅ Updated ActivityModel (module_id, order_index)
- ✅ Updated ExerciseModel (reference_solution, grading_config)
- ✅ Created Pydantic schemas for all new models
- ✅ Created migration SQL script
- ✅ Created Python migration tool
- ✅ Updated models/__init__.py exports
- ✅ Documented architecture changes

**In Progress:**
- ⚠️ Router updates (teacher + student)
- ⚠️ Frontend integration

**Pending:**
- ❌ Gamification logic implementation
- ❌ Achievement definitions
- ❌ Module prerequisites
- ❌ Leaderboards

---

## 🎉 Success Criteria

The LMS hierarchical architecture refactor is **complete** when:

1. ✅ All 3 new tables created and populated
2. ⏳ Teacher can create/edit modules via API
3. ⏳ Activities are grouped by modules in student view
4. ⏳ Enrollment-based access control works
5. ⏳ Gamification stats are displayed
6. ⏳ Multi-course enrollment is tested

**Current Status: 1/6 Complete (Database layer done, API layer pending)**

---

**Generated:** 2024-01-XX  
**Author:** GitHub Copilot  
**Version:** LMS Hierarchy v1.0
