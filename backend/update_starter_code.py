"""
Script para actualizar el código inicial de todos los ejercicios a solo comentarios.
Ejecutar: python update_starter_code.py
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v3"
ACTIVITY_ID = "497b3fc2-fd0b-42b2-90e8-2a00dc737b64"

# Código inicial con solo comentarios para cada ejercicio
STARTER_CODES = {
    "Imprimir Números Impares": '''# Ejercicio: Imprimir Números Impares
# 
# Objetivo: Crear un programa que imprima los números impares del 1 al 10.
#
# Tu código aquí:
''',
    "Suma de Números Pares": '''# Ejercicio: Suma de Números Pares
#
# Objetivo: Calcular la suma de todos los números pares del 1 al 20.
#
# Tu código aquí:
''',
    "Tabla de Multiplicar": '''# Ejercicio: Tabla de Multiplicar
#
# Objetivo: Crear una función que imprima la tabla de multiplicar de un número.
#
# Tu código aquí:
''',
    "Factorial de un Número": '''# Ejercicio: Factorial de un Número
#
# Objetivo: Crear una función que calcule el factorial de un número.
#
# Tu código aquí:
''',
    "Contar Vocales": '''# Ejercicio: Contar Vocales
#
# Objetivo: Contar cuántas vocales hay en una cadena de texto.
#
# Tu código aquí:
''',
    "Invertir Cadena": '''# Ejercicio: Invertir Cadena
#
# Objetivo: Crear una función que invierta una cadena de texto.
#
# Tu código aquí:
''',
    "Números Fibonacci": '''# Ejercicio: Números Fibonacci
#
# Objetivo: Generar los primeros N números de la serie Fibonacci.
#
# Tu código aquí:
''',
    "Verificar Palíndromo": '''# Ejercicio: Verificar Palíndromo
#
# Objetivo: Verificar si una palabra es un palíndromo.
#
# Tu código aquí:
''',
    "Buscar Elemento en Lista": '''# Ejercicio: Buscar Elemento en Lista
#
# Objetivo: Buscar un elemento en una lista y devolver su índice.
#
# Tu código aquí:
''',
    "Iteración sobre Cadena con enumerate": '''# Ejercicio: Iteración sobre Cadena con enumerate
#
# Objetivo: Iterar sobre una cadena mostrando índice y carácter.
#
# Tu código aquí:
''',
}

async def update_starter_codes():
    """Actualiza los códigos iniciales via SQL directo."""
    import subprocess
    
    print("=" * 60)
    print("ACTUALIZANDO CÓDIGOS INICIALES DE EJERCICIOS")
    print("=" * 60)
    
    for title, code in STARTER_CODES.items():
        # Escapar comillas simples para SQL
        escaped_code = code.replace("'", "''")
        
        sql = f"""UPDATE exercises_v2 SET starter_code = '{escaped_code}' 
                  WHERE title LIKE '%{title.split()[0]}%' 
                  AND activity_id = '{ACTIVITY_ID}';"""
        
        cmd = f'docker exec -i ai_native_postgres psql -U postgres -d ai_native -c "{sql}"'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if "UPDATE" in result.stdout:
            print(f"✅ {title}")
        else:
            print(f"⚠️ {title}: {result.stderr or result.stdout}")
    
    print("\n✅ Códigos iniciales actualizados!")

if __name__ == "__main__":
    asyncio.run(update_starter_codes())
