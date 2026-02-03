"""
Seed exercise attempts for students in Bucles activities.
This will populate the "Estudiantes Inscritos" table with real progress data.
"""
import asyncio
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, "/app/backend")

from src_v3.infrastructure.persistence.database import get_db_session
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession


# Students from our previous seed
STUDENTS = [
    "Juan Martínez", "María García", "Carlos López", "Ana Rodríguez",
    "Luis González", "Laura Fernández", "Diego Pérez", "Sofía Sánchez",
    "Santiago Flores", "Valentina Torres", "Mateo Romero", "Isabella Ruiz",
    "Nicolás Alvarez", "Camila Díaz", "Benjamín Castro"
]


async def get_or_create_exercises(session: AsyncSession, activity_id: str, num_exercises: int = 10):
    """Get or create exercises for an activity."""
    result = await session.execute(
        text("SELECT exercise_id FROM exercises_v2 WHERE activity_id = :activity_id LIMIT :limit"),
        {"activity_id": activity_id, "limit": num_exercises}
    )
    existing = result.fetchall()
    
    if existing and len(existing) >= num_exercises:
        return [row[0] for row in existing]
    
    # Create exercises if they don't exist (without position field)
    exercise_ids = []
    for i in range(num_exercises):
        exercise_id = f"ex-{activity_id[:8]}-{i+1:02d}"
        
        # Check if exercise exists
        result = await session.execute(
            text("SELECT exercise_id FROM exercises_v2 WHERE exercise_id = :id"),
            {"id": exercise_id}
        )
        if result.fetchone():
            exercise_ids.append(exercise_id)
            continue
        
        await session.execute(
            text("""
                INSERT INTO exercises_v2 (
                    exercise_id, activity_id, title, prompt_text, 
                    difficulty, expected_output
                )
                VALUES (
                    :exercise_id, :activity_id, :title, :prompt,
                    :difficulty, :expected
                )
                ON CONFLICT (exercise_id) DO NOTHING
            """),
            {
                "exercise_id": exercise_id,
                "activity_id": activity_id,
                "title": f"Ejercicio {i+1}",
                "prompt": f"Resuelve el ejercicio {i+1} usando bucles",
                "difficulty": random.choice(["easy", "medium", "hard"]),
                "expected": "Código correcto con bucles"
            }
        )
        exercise_ids.append(exercise_id)
    
    await session.commit()
    print(f"✅ Created/verified {num_exercises} exercises for activity")
    return exercise_ids


async def create_exercise_attempts(
    session: AsyncSession,
    student_id: str,
    exercise_ids: list,
    performance_level: str
):
    """Create exercise attempts for a student based on performance level."""
    
    # Determine how many exercises to complete based on performance
    if performance_level == "excellent":
        num_completed = len(exercise_ids)  # All exercises
        pass_rate = 0.95  # 95% pass rate
    elif performance_level == "good":
        num_completed = int(len(exercise_ids) * 0.85)  # 85% of exercises
        pass_rate = 0.80
    elif performance_level == "passing":
        num_completed = int(len(exercise_ids) * 0.65)  # 65% of exercises
        pass_rate = 0.70
    else:  # at_risk
        num_completed = int(len(exercise_ids) * 0.30)  # 30% of exercises
        pass_rate = 0.40
    
    # Shuffle and select exercises to attempt
    attempted_exercises = random.sample(exercise_ids, min(num_completed, len(exercise_ids)))
    
    attempts_created = 0
    exercises_passed = 0
    
    for i, exercise_id in enumerate(attempted_exercises):
        passed = random.random() < pass_rate
        if passed:
            exercises_passed += 1
        
        # Create 1-3 attempts per exercise
        num_attempts = random.randint(1, 3)
        
        for attempt_num in range(num_attempts):
            # Last attempt should match the passed status
            is_last = attempt_num == num_attempts - 1
            attempt_passed = passed if is_last else False
            
            # Generate submission time (in the past 7 days)
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            submitted_at = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
            
            await session.execute(
                text("""
                    INSERT INTO exercise_attempts_v2 (
                        user_id, exercise_id, code, passed, feedback,
                        submitted_at, execution_time_ms
                    )
                    VALUES (
                        :user_id, :exercise_id, :code, :passed, :feedback,
                        :submitted_at, :execution_time
                    )
                """),
                {
                    "user_id": student_id,
                    "exercise_id": exercise_id,
                    "code": f"# Intento {attempt_num + 1} del ejercicio\nfor i in range(10):\n    print(i)",
                    "passed": attempt_passed,
                    "feedback": "¡Excelente!" if attempt_passed else "Intenta de nuevo",
                    "submitted_at": submitted_at,
                    "execution_time": random.randint(50, 500)
                }
            )
            attempts_created += 1
    
    return attempts_created, exercises_passed, len(attempted_exercises)


async def main():
    print("🎯 Seeding exercise attempts for Bucles activities...")
    print("=" * 60)
    
    async for db in get_db_session():
        try:
            # Find all Bucles activities
            result = await db.execute(
                text("SELECT activity_id, title FROM activities WHERE title LIKE :pattern ORDER BY title"),
                {"pattern": "%Bucle%"}
            )
            activities = result.fetchall()
            
            if not activities:
                print("❌ No Bucles activities found")
                return
            
            print(f"✅ Found {len(activities)} Bucles activities:")
            for act in activities:
                print(f"   - {act[1]} (ID: {act[0]})")
            print()
            
            # Find all students
            result = await db.execute(
                text("SELECT id, full_name, email FROM users WHERE full_name = ANY(:names) ORDER BY full_name"),
                {"names": STUDENTS}
            )
            students = result.fetchall()
            
            if not students:
                print("❌ No students found")
                return
            
            print(f"✅ Found {len(students)} students")
            print()
            
            # Define performance distribution (same as sessions)
            performance_levels = (
                ["excellent"] * 3 +
                ["good"] * 6 +
                ["passing"] * 4 +
                ["at_risk"] * 2
            )
            
            total_attempts = 0
            
            # For each activity, create exercise attempts
            for activity in activities:
                activity_id = activity[0]
                activity_title = activity[1]
                
                print(f"📚 Processing: {activity_title}")
                
                # Create/get exercises for this activity
                exercise_ids = await get_or_create_exercises(db, activity_id, num_exercises=12)
                print(f"   📝 {len(exercise_ids)} exercises available")
                
                # Shuffle performance levels for variety
                random.shuffle(performance_levels)
                
                activity_stats = {
                    "total_attempts": 0,
                    "students_processed": 0,
                    "avg_completion": 0
                }
                
                # Create attempts for each student
                for i, student in enumerate(students):
                    student_id = student[0]
                    student_name = student[1]
                    performance = performance_levels[i]
                    
                    attempts, passed, attempted = await create_exercise_attempts(
                        db,
                        student_id,
                        exercise_ids,
                        performance
                    )
                    
                    completion_rate = (passed / len(exercise_ids) * 100) if len(exercise_ids) > 0 else 0
                    
                    activity_stats["total_attempts"] += attempts
                    activity_stats["students_processed"] += 1
                    activity_stats["avg_completion"] += completion_rate
                    
                    total_attempts += attempts
                
                await db.commit()
                
                avg_completion = activity_stats["avg_completion"] / len(students) if students else 0
                print(f"   ✅ {activity_stats['total_attempts']} attempts created")
                print(f"   📊 Average completion: {avg_completion:.1f}%")
                print()
            
            print("=" * 60)
            print(f"✅ SEED COMPLETED!")
            print(f"📊 Total Statistics:")
            print(f"   - {len(activities)} activities processed")
            print(f"   - {len(students)} students")
            print(f"   - {total_attempts} total exercise attempts created")
            print(f"   - Average: {total_attempts / (len(activities) * len(students)):.1f} attempts per student per activity")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(main())
