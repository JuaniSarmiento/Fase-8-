"""
Test E2E: Evaluar sistema de corrección con los 10 ejercicios
Envía código correcto para cada ejercicio y verifica que las notas sean apropiadas.

Ejecutar: python test_all_exercises.py
"""
import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000/api/v3"
ACTIVITY_ID = "497b3fc2-fd0b-42b2-90e8-2a00dc737b64"
STUDENT_ID = "test-evaluacion-001"

# Soluciones correctas para cada ejercicio
CORRECT_SOLUTIONS = {
    "Imprimir Números Impares": '''
# Imprimir números impares del 1 al 10
for i in range(1, 11):
    if i % 2 != 0:
        print(i)
''',
    "Suma de Números Pares": '''
# Calcular suma de números pares del 1 al 20
suma = 0
for i in range(2, 21, 2):
    suma += i
print(f"La suma de pares es: {suma}")
''',
    "Tabla de Multiplicar": '''
def tabla_multiplicar(numero):
    """Imprime la tabla de multiplicar de un número."""
    for i in range(1, 11):
        print(f"{numero} x {i} = {numero * i}")

tabla_multiplicar(5)
''',
    "Factorial de un Número": '''
def factorial(n):
    """Calcula el factorial de un número."""
    if n == 0 or n == 1:
        return 1
    resultado = 1
    for i in range(2, n + 1):
        resultado *= i
    return resultado

print(f"Factorial de 5: {factorial(5)}")
''',
    "Contar Vocales": '''
def contar_vocales(texto):
    """Cuenta las vocales en una cadena."""
    vocales = "aeiouAEIOU"
    contador = 0
    for char in texto:
        if char in vocales:
            contador += 1
    return contador

print(f"Vocales en 'Hola Mundo': {contar_vocales('Hola Mundo')}")
''',
    "Invertir Cadena": '''
def invertir_cadena(texto):
    """Invierte una cadena de texto."""
    return texto[::-1]

print(invertir_cadena("Hola"))
''',
    "Números Fibonacci": '''
def fibonacci(n):
    """Genera los primeros n números de Fibonacci."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

print(f"Fibonacci 10: {fibonacci(10)}")
''',
    "Verificar Palíndromo": '''
def es_palindromo(texto):
    """Verifica si una palabra es palíndromo."""
    texto_limpio = texto.lower().replace(" ", "")
    return texto_limpio == texto_limpio[::-1]

print(f"'ana' es palíndromo: {es_palindromo('ana')}")
print(f"'hola' es palíndromo: {es_palindromo('hola')}")
''',
    "Buscar Elemento en Lista": '''
def buscar_elemento(lista, elemento):
    """Busca un elemento y devuelve su índice."""
    for i, item in enumerate(lista):
        if item == elemento:
            return i
    return -1

mi_lista = [1, 2, 3, 4, 5]
print(f"Índice de 3: {buscar_elemento(mi_lista, 3)}")
''',
    "Iteración sobre Cadena con enumerate": '''
def iterar_cadena(texto):
    """Itera sobre una cadena mostrando índice y carácter."""
    for indice, caracter in enumerate(texto):
        print(f"Índice: {indice}, Carácter: {caracter}")

iterar_cadena("Hola")
''',
}


async def test_all_exercises():
    """Prueba los 10 ejercicios con código correcto."""
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("=" * 70)
        print("TEST: EVALUACIÓN DE LOS 10 EJERCICIOS CON CÓDIGO CORRECTO")
        print("=" * 70)
        
        # 1. Iniciar sesión
        print("\n📌 Iniciando sesión...")
        session_resp = await client.post(f"{BASE_URL}/student/sessions", json={
            "student_id": STUDENT_ID,
            "activity_id": ACTIVITY_ID,
            "mode": "SOCRATIC"
        })
        
        if session_resp.status_code not in [200, 201]:
            print(f"❌ Error iniciando sesión: {session_resp.status_code}")
            return
        
        session_id = session_resp.json()["session_id"]
        print(f"✅ Sesión: {session_id}\n")
        
        # 2. Obtener ejercicios
        exercises_resp = await client.get(f"{BASE_URL}/student/activities/{ACTIVITY_ID}/exercises")
        exercises = exercises_resp.json()
        print(f"📚 Ejercicios encontrados: {len(exercises)}\n")
        
        # 3. Probar cada ejercicio
        results = []
        
        for i, exercise in enumerate(exercises):
            exercise_id = exercise["exercise_id"]
            title = exercise["title"]
            
            # Buscar código correcto
            code = None
            for key, value in CORRECT_SOLUTIONS.items():
                if key.lower() in title.lower() or title.lower() in key.lower():
                    code = value
                    break
            
            if not code:
                # Fallback - buscar por palabras clave
                for key, value in CORRECT_SOLUTIONS.items():
                    if key.split()[0].lower() in title.lower():
                        code = value
                        break
            
            if not code:
                print(f"⚠️ Ejercicio {i+1}: {title} - Sin código de prueba")
                results.append({"title": title, "grade": None, "error": "Sin código"})
                continue
            
            print(f"📝 Ejercicio {i+1}: {title}")
            
            try:
                submit_resp = await client.post(
                    f"{BASE_URL}/student/sessions/{session_id}/submit",
                    json={
                        "code": code,
                        "language": "python",
                        "exercise_id": exercise_id,
                        "is_final_submission": False
                    }
                )
                
                if submit_resp.status_code == 200:
                    result = submit_resp.json()
                    grade = result.get("grade", 0)
                    tests_passed = result.get("tests_passed", False)
                    feedback = result.get("feedback", "")[:100]
                    
                    emoji = "✅" if grade >= 70 else "⚠️" if grade >= 50 else "❌"
                    print(f"   {emoji} Nota: {grade}/100 | Tests: {'✓' if tests_passed else '✗'}")
                    print(f"   💬 {feedback}...")
                    
                    results.append({
                        "title": title,
                        "grade": grade,
                        "tests_passed": tests_passed,
                        "feedback": feedback
                    })
                else:
                    print(f"   ❌ Error: {submit_resp.status_code}")
                    results.append({"title": title, "grade": None, "error": submit_resp.text[:100]})
                    
            except Exception as e:
                print(f"   ❌ Excepción: {str(e)[:50]}")
                results.append({"title": title, "grade": None, "error": str(e)[:50]})
            
            print()
            await asyncio.sleep(1)  # Rate limiting
        
        # 4. Resumen
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE EVALUACIÓN")
        print("=" * 70)
        
        grades = [r["grade"] for r in results if r.get("grade") is not None]
        
        if grades:
            avg = sum(grades) / len(grades)
            max_grade = max(grades)
            min_grade = min(grades)
            passed = len([g for g in grades if g >= 60])
            
            print(f"\n   📈 Promedio: {avg:.1f}/100")
            print(f"   📊 Máximo: {max_grade}/100")
            print(f"   📉 Mínimo: {min_grade}/100")
            print(f"   ✅ Aprobados (>=60): {passed}/{len(grades)}")
            print(f"   ❌ Reprobados (<60): {len(grades) - passed}/{len(grades)}")
            
            print("\n🔍 ANÁLISIS:")
            if avg >= 70:
                print("   ✅ El sistema evalúa correctamente el código correcto")
            else:
                print(f"   ⚠️ PROBLEMA: El promedio ({avg:.1f}) es bajo para código correcto")
                print("   Posibles causas:")
                print("   - Los tests unitarios son muy estrictos")
                print("   - La IA tiene expectativas diferentes")
                print("   - El código no coincide exactamente con lo esperado")
        
        print("\n📋 DETALLE POR EJERCICIO:")
        for r in results:
            grade = r.get("grade", "N/A")
            emoji = "✅" if grade and grade >= 70 else "⚠️" if grade and grade >= 50 else "❌"
            print(f"   {emoji} {r['title']}: {grade}")


if __name__ == "__main__":
    # Write output to file
    with open("test_all_results.txt", "w", encoding="utf-8") as f:
        class Tee:
            def __init__(self, *files):
                self.files = files
            def write(self, x):
                for file in self.files:
                    file.write(x)
                    file.flush()
            def flush(self):
                for file in self.files:
                    file.flush()
        
        old_stdout = sys.stdout
        sys.stdout = Tee(sys.stdout, f)
        asyncio.run(test_all_exercises())
        sys.stdout = old_stdout
    
    print("\n📁 Resultados guardados en test_all_results.txt")
