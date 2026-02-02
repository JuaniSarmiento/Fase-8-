# Actualización del Frontend - Sistema de Ejercicios

## Backend Completado ✅

Se agregaron los siguientes endpoints:

1. **GET `/student/activities/{activity_id}/exercises`**
   - Devuelve todos los ejercicios de una actividad ordenados
   - Incluye: exercise_id, title, difficulty, mission_markdown, starter_code, order_index, total_exercises

2. **POST `/student/activities/{activity_id}/exercises/{exercise_id}/submit`**
   - Envía la solución de un ejercicio individual  
   - Retorna: next_exercise_id, is_activity_complete
   - Permite avanzar automáticamente al siguiente ejercicio

## Cambios Necesarios en el Frontend

### 1. Modificar `/frontend/app/student/activities/[id]/page.tsx`

Agregar estados para ejercicios:
```tsx
const [exercises, setExercises] = useState<Exercise[]>([]);
const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
```

Cargar ejercicios al inicio:
```tsx
const exercisesResponse = await api.get(`/student/activities/${activityId}/exercises?student_id=${studentId}`);
setExercises(exercisesResponse.data);
```

Mostrar ejercicio actual en lugar de instrucciones de actividad:
```tsx
const currentExercise = exercises[currentExerciseIndex];
// Mostrar: currentExercise.mission_markdown en el panel izquierdo
// Usar: currentExercise.starter_code como código inicial
```

Modificar handleSubmit para usar el nuevo endpoint:
```tsx
const response = await api.post(
  `/student/activities/${activityId}/exercises/${currentExercise.exercise_id}/submit?student_id=${user.id}`,
  { code, is_final_submission: true }
);

if (response.data.next_exercise_id) {
  // Avanzar al siguiente ejercicio
  setCurrentExerciseIndex(prev => prev + 1);
  toast.success('¡Ejercicio completado! Pasando al siguiente...');
} else {
  // Actividad completada
  toast.success('¡Felicitaciones! Completaste toda la actividad');
  router.push('/student/activities');
}
```

Agregar navegación entre ejercicios:
```tsx
<div className="flex items-center justify-between mb-4">
  <Button 
    onClick={() => setCurrentExerciseIndex(prev => prev - 1)}
    disabled={currentExerciseIndex === 0}
  >
    <ChevronLeft /> Anterior
  </Button>
  
  <span className="text-sm text-muted-foreground">
    Ejercicio {currentExerciseIndex + 1} de {exercises.length}
  </span>
  
  <Button 
    onClick={() => setCurrentExerciseIndex(prev => prev + 1)}
    disabled={currentExerciseIndex === exercises.length - 1}
  >
    Siguiente <ChevronRight />
  </Button>
</div>
```

### 2. Actualizar el tipo Exercise

```tsx
interface Exercise {
  exercise_id: string;
  title: string;
  difficulty: string;
  mission_markdown: string;
  starter_code: string;
  language: string;
  order_index: number;
  total_exercises: number;
}
```

### 3. Panel Izquierdo - Mostrar Ejercicio Actual

```tsx
<div className="h-full overflow-auto p-6">
  <Badge variant="outline" className="mb-2">
    {currentExercise.difficulty}
  </Badge>
  
  <h2 className="text-2xl font-bold mb-4">
    {currentExercise.title}
  </h2>
  
  <div className="prose prose-sm dark:prose-invert max-w-none">
    <ReactMarkdown>{currentExercise.mission_markdown}</ReactMarkdown>
  </div>
  
  <div className="mt-6 p-4 bg-muted rounded-lg">
    <p className="text-sm text-muted-foreground">
      Ejercicio {currentExerciseIndex + 1} de {exercises.length}
    </p>
    <div className="flex gap-1 mt-2">
      {exercises.map((_, idx) => (
        <div
          key={idx}
          className={`h-2 flex-1 rounded ${
            idx < currentExerciseIndex ? 'bg-green-500' :
            idx === currentExerciseIndex ? 'bg-blue-500' :
            'bg-gray-300'
          }`}
        />
      ))}
    </div>
  </div>
</div>
```

## Flujo Completo

1. Usuario entra a actividad "Bucles"
2. Frontend carga los 10 ejercicios
3. Muestra el primero (Iteración Básica con Bucle for)
4. Usuario escribe código y envía
5. Backend guarda el intento
6. Frontend avanza automáticamente al ejercicio 2
7. Repite hasta completar los 10 ejercicios
8. Al terminar el último, redirige a lista de actividades

## Testing

Probar con:
- Activity ID: `e5a83dce-c813-4c9f-acba-53438de9b004` (Bucles)
- Student ID: `70ed9d32-7bf5-4ae2-9aa9-d40ffeba4aea` (alumno1@test.com)

Endpoint de prueba:
```bash
curl http://localhost:8000/api/v3/student/activities/e5a83dce-c813-4c9f-acba-53438de9b004/exercises?student_id=70ed9d32-7bf5-4ae2-9aa9-d40ffeba4aea
```
