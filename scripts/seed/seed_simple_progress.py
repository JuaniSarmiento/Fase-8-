"""
Simple script to populate student progress for Bucles activities.
Uses raw SQL to work with actual database tables.
"""
import asyncio
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, "/app/backend")

from src_v3.infrastructure.persistence.database import get_db_session
from sqlalchemy import text


# Students from our previous seed
STUDENTS = [
    "Juan Martínez", "María García", "Carlos López", "Ana Rodríguez",
    "Luis González", "Laura Fernández", "Diego Pérez", "Sofía Sánchez",
    "Santiago Flores", "Valentina Torres", "Mateo Romero", "Isabella Ruiz",
    "Nicolás Alvarez", "Camila Díaz", "Benjamín Castro"
]


async def main():
    print("🎯 Populating student progress for Bucles activities...")
    print("=" * 60)
    
    async for db in get_db_session():
        try:
            # Find Bucles activities
            result = await db.execute(
                text("SELECT activity_id, title FROM activities WHERE title LIKE :pattern ORDER BY title"),
                {"pattern": "%Bucle%"}
            )
            activities = result.fetchall()
            
            if not activities:
                print("❌ No Bucles activities found")
                return
            
            print(f"✅ Found {len(activities)} activities:")
            for act in activities:
                print(f"   - {act[1]}")
            print()
            
            # Find students
            result = await db.execute(
                text("SELECT id, full_name FROM users WHERE full_name = ANY(:names)"),
                {"names": STUDENTS}
            )
            students = result.fetchall()
            
            print(f"✅ Found {len(students)} students")
            print()
            
            # Performance distribution
            performance_levels = ["excellent"] * 3 + ["good"] * 6 + ["passing"] * 4 + ["at_risk"] * 2
            
            total_exercises = 0
            total_attempts = 0
            
            # Process each activity
            for activity_id, activity_title in activities:
                print(f"📚 {activity_title}")
                
                # Create 12 exercises for this activity
                exercise_ids = []
                for i in range(12):
                    exercise_id = f"ex-{activity_id[:8]}-{i+1:02d}"
                    
                    await db.execute(
                        text("""
                            INSERT INTO exercises (
                                exercise_id, activity_id, title, description,
                                difficulty, exercise_type, language
                            )
                            VALUES (:id, :activity_id, :title, :desc, :diff, 'coding', 'python')
                            ON CONFLICT (exercise_id) DO NOTHING
                        """),
                        {
                            "id": exercise_id,
                            "activity_id": activity_id,
                            "title": f"Ejercicio {i+1}: Bucles",
                            "desc": f"Practica bucles con este ejercicio",
                            "diff": random.choice(["easy", "medium", "hard"])
                        }
                    )
                    exercise_ids.append(exercise_id)
                
                await db.commit()
                total_exercises += 12
                print(f"   ✅ Created 12 exercises")
                
                # Shuffle performance
                random.shuffle(performance_levels)
                
                # Create attempts for each student
                activity_attempts = 0
                for i, (student_id, student_name) in enumerate(students):
                    perf = performance_levels[i]
                    
                    # Determine how many exercises based on performance
                    if perf == "excellent":
                        num_to_complete = 12  # All
                        pass_rate = 0.95
                    elif perf == "good":
                        num_to_complete = 10  # 83%
                        pass_rate = 0.85
                    elif perf == "passing":
                        num_to_complete = 8  # 67%
                        pass_rate = 0.70
                    else:  # at_risk
                        num_to_complete = 4  # 33%
                        pass_rate = 0.40
                    
                    # Select exercises to attempt
                    attempted = random.sample(exercise_ids, num_to_complete)
                    
                    for ex_id in attempted:
                        # Decide if passed
                        passed = random.random() < pass_rate
                        
                        # Create 1-2 attempts
                        for attempt_num in range(random.randint(1, 2)):
                            days_ago = random.randint(1, 7)
                            submitted_at = datetime.now() - timedelta(days=days_ago)
                            
                            await db.execute(
                                text("""
                                    INSERT INTO exercise_attempts_v2 (
                                        user_id, exercise_id, code, passed,
                                        feedback, submitted_at, execution_time_ms
                                    )
                                    VALUES (:user_id, :exercise_id, :code, :passed,
                                            :feedback, :submitted_at, :exec_time)
                                """),
                                {
                                    "user_id": student_id,
                                    "exercise_id": ex_id,
                                    "code": f"# Código de {student_name}\nfor i in range(10):\n    print(i)",
                                    "passed": passed,
                                    "feedback": "¡Bien!" if passed else "Intenta de nuevo",
                                    "submitted_at": submitted_at,
                                    "exec_time": random.randint(100, 1000)
                                }
                            )
                            activity_attempts += 1
                            total_attempts += 1
                
                await db.commit()
                print(f"   📝 Created {activity_attempts} attempts for {len(students)} students")
                print()
            
            print("=" * 60)
            print(f"✅ COMPLETED!")
            print(f"   - {len(activities)} activities processed")
            print(f"   - {total_exercises} exercises created")
            print(f"   - {total_attempts} attempts created")
            print(f"   - Average: {total_attempts / len(activities) / len(students):.1f} attempts per student per activity")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(main())
