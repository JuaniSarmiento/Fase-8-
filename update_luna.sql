UPDATE submissions 
SET 
    status = 'graded',
    auto_grade = 73.3,
    final_grade = 73.3,
    ai_feedback = 'Bien hecho. Continúa así y mejora en la eficiencia del código. Nota: 73.3/100',
    test_results = jsonb_set(
        COALESCE(test_results, '{}'::jsonb),
        '{risk_level}',
        '"BAJO"'
    )
WHERE student_id = '70ed9d32-7bf5-4ae2-9aa9-d40ffeba4aea'
  AND activity_id = 'e5a83dce-c813-4c9f-acba-53438de9b004';
