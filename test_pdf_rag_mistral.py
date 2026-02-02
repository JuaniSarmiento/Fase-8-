"""
Test completo del flujo PDF -> RAG -> Mistral
==============================================

Este script prueba:
1. Subir un PDF de prueba
2. Procesarlo con RAG (extracción y vectorización)
3. Generar ejercicios con Mistral usando el contenido del PDF

Autor: Test E2E
Fecha: 2026-01-27
"""

import requests
import time
import json
from pathlib import Path
from io import BytesIO


# ====================== CONFIGURACIÓN ======================

BASE_URL = "http://localhost:8000/api/v3"
TEACHER_ID = "550e8400-e29b-41d4-a716-446655440001"  # UUID de profesor de prueba
COURSE_ID = "course_python_101"

# PDF de prueba (creamos uno simple)
PDF_CONTENT = """
CURSO DE PYTHON - PROGRAMACIÓN BÁSICA
=====================================

TEMA: Listas y Estructuras de Datos en Python

1. INTRODUCCIÓN A LAS LISTAS
-----------------------------
Las listas en Python son estructuras de datos mutables que pueden contener
elementos de diferentes tipos. Se definen usando corchetes [].

Ejemplo básico:
    mi_lista = [1, 2, 3, 4, 5]
    frutas = ["manzana", "banana", "naranja"]
    mixta = [1, "texto", 3.14, True]

2. OPERACIONES BÁSICAS
-----------------------
- Acceso por índice: lista[0] devuelve el primer elemento
- Slicing: lista[1:3] devuelve elementos desde índice 1 hasta 3 (sin incluir 3)
- Append: lista.append(elemento) añade al final
- Insert: lista.insert(indice, elemento) inserta en posición específica
- Remove: lista.remove(elemento) elimina la primera ocurrencia
- Pop: lista.pop() elimina y devuelve el último elemento

Ejemplos:
    numeros = [1, 2, 3, 4, 5]
    numeros.append(6)  # [1, 2, 3, 4, 5, 6]
    numeros.insert(0, 0)  # [0, 1, 2, 3, 4, 5, 6]
    numeros.remove(3)  # [0, 1, 2, 4, 5, 6]

3. LIST COMPREHENSIONS
----------------------
Las list comprehensions son una forma elegante y concisa de crear listas.

Sintaxis básica:
    nueva_lista = [expresion for item in iterable if condicion]

Ejemplos:
    # Cuadrados de números del 1 al 10
    cuadrados = [x**2 for x in range(1, 11)]
    
    # Números pares
    pares = [x for x in range(20) if x % 2 == 0]
    
    # Transformar strings
    mayusculas = [s.upper() for s in ["hola", "mundo"]]

4. MÉTODOS IMPORTANTES
----------------------
- len(lista): devuelve la longitud
- sorted(lista): devuelve una copia ordenada
- lista.sort(): ordena in-place
- lista.reverse(): invierte el orden
- lista.count(elemento): cuenta ocurrencias
- lista.index(elemento): devuelve índice de primera ocurrencia

5. EJERCICIOS PRÁCTICOS
------------------------
Ejercicio 1: Crear una función que tome una lista y devuelva solo los números positivos.
Ejercicio 2: Implementar una función que elimine duplicados de una lista.
Ejercicio 3: Escribir una función que ordene una lista de tuplas por el segundo elemento.

6. CASOS AVANZADOS
------------------
- Listas anidadas: matrices y estructuras complejas
- Iteración con enumerate(): acceso a índice y valor simultáneamente
- zip(): combinar múltiples listas
- map() y filter(): programación funcional con listas

CONCEPTOS CLAVE PARA RECORDAR:
- Las listas son mutables (se pueden modificar)
- Los índices empiezan en 0
- Los índices negativos cuentan desde el final (-1 es el último)
- Las list comprehensions son más eficientes que loops tradicionales
- Siempre verificar si la lista está vacía antes de acceder elementos
"""


def create_sample_pdf():
    """Crea un PDF simple de prueba usando reportlab"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import inch
        
        # Crear PDF en memoria
        pdf_buffer = BytesIO()
        
        # Crear documento
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Añadir contenido
        for line in PDF_CONTENT.split('\n'):
            if line.strip():
                if line.startswith('CURSO') or line.startswith('TEMA:'):
                    p = Paragraph(line, styles['Title'])
                elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.')):
                    p = Paragraph(line, styles['Heading2'])
                else:
                    p = Paragraph(line.replace('    ', '&nbsp;&nbsp;&nbsp;&nbsp;'), styles['Normal'])
                story.append(p)
                story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer
        
    except ImportError:
        print("⚠️ reportlab no está instalado. Usando PDF básico alternativo...")
        # Fallback: crear un archivo de texto que simule un PDF
        return BytesIO(PDF_CONTENT.encode('utf-8'))


def test_upload_and_generation():
    """Test principal: subir PDF y generar ejercicios con Mistral + RAG"""
    
    print("\n" + "="*70)
    print("🧪 TEST COMPLETO: PDF -> RAG -> MISTRAL")
    print("="*70 + "\n")
    
    # PASO 1: Verificar que el backend está funcionando
    print("📡 Paso 1: Verificando backend...")
    try:
        # Probar con el endpoint de documentación
        health_response = requests.get("http://localhost:8000/api/v3/docs", timeout=15)
        if health_response.status_code == 200:
            print("✅ Backend está activo y respondiendo")
        else:
            print(f"⚠️ Backend responde con código: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando al backend: {e}")
        print("💡 Asegúrate de que el backend esté corriendo en http://localhost:8000")
        return False
    
    # PASO 2: Crear PDF de prueba
    print("\n📄 Paso 2: Creando PDF de prueba...")
    try:
        pdf_buffer = create_sample_pdf()
        print(f"✅ PDF creado con éxito ({len(pdf_buffer.getvalue())} bytes)")
    except Exception as e:
        print(f"❌ Error creando PDF: {e}")
        return False
    
    # PASO 3: Subir PDF y iniciar generación
    print("\n📤 Paso 3: Subiendo PDF al backend...")
    try:
        # Preparar archivo
        files = {
            'file': ('curso_python_listas.pdf', pdf_buffer, 'application/pdf')
        }
        
        # Preparar parámetros como query params
        params = {
            'teacher_id': TEACHER_ID,
            'course_id': COURSE_ID,
            'topic': 'Listas y List Comprehensions en Python',
            'difficulty': 'INTERMEDIO',  # Must be: FACIL, INTERMEDIO, or AVANZADO
            'language': 'python',
            'concepts': 'listas, list comprehensions, métodos de listas, slicing'
        }
        
        # Hacer request
        upload_url = f"{BASE_URL}/teacher/generator/upload"
        response = requests.post(upload_url, files=files, params=params, timeout=30)
        
        if response.status_code in [200, 201]:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ PDF subido correctamente")
            print(f"   Job ID: {job_id}")
            print(f"   Estado: {result.get('status')}")
        else:
            print(f"❌ Error en la subida: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error subiendo PDF: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # PASO 4: Monitorear el estado del job
    print("\n⏳ Paso 4: Monitoreando procesamiento RAG y generación con Mistral...")
    print("   (Esto puede tomar 30-60 segundos...)")
    
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            status_url = f"{BASE_URL}/teacher/generator/{job_id}/status"
            status_response = requests.get(status_url, timeout=10)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                current_status = status_data.get('status')
                phase = status_data.get('current_phase', 'unknown')
                
                # Mostrar progreso
                if attempt % 3 == 0:  # Cada 3 intentos
                    print(f"   [{attempt+1}/{max_attempts}] Estado: {current_status} | Fase: {phase}")
                
                # Verificar si terminó
                if current_status == 'awaiting_approval':
                    print("\n✅ Generación completada - Esperando aprobación del profesor")
                    print("\n📊 Detalles del resultado:")
                    print(f"   - Fase actual: {phase}")
                    print(f"   - Job ID: {job_id}")
                    
                    # Intentar obtener los ejercicios generados
                    if 'draft_exercises' in status_data:
                        exercises = status_data['draft_exercises']
                        print(f"   - Ejercicios generados: {len(exercises)}")
                        print("\n📝 Primeros 3 ejercicios generados:")
                        for i, ex in enumerate(exercises[:3], 1):
                            print(f"\n   {i}. {ex.get('title', 'Sin título')}")
                            print(f"      Dificultad: {ex.get('difficulty', 'N/A')}")
                            print(f"      Descripción: {ex.get('description', 'N/A')[:100]}...")
                    
                    return True
                    
                elif current_status == 'error':
                    error_msg = status_data.get('error_message', 'Error desconocido')
                    print(f"\n❌ Error en el procesamiento:")
                    print(f"   {error_msg}")
                    return False
                    
                elif current_status in ['completed', 'published']:
                    print(f"\n✅ Proceso completado con estado: {current_status}")
                    return True
                
            else:
                print(f"⚠️ Error obteniendo estado: {status_response.status_code}")
            
            time.sleep(2)  # Esperar 2 segundos entre intentos
            attempt += 1
            
        except Exception as e:
            print(f"⚠️ Error consultando estado: {e}")
            time.sleep(2)
            attempt += 1
    
    print(f"\n⏰ Timeout después de {max_attempts * 2} segundos")
    print("   El proceso puede seguir ejecutándose en segundo plano")
    print(f"   Puedes verificar manualmente el estado con: GET {BASE_URL}/teacher/generator/status/{job_id}")
    return False


def test_rag_directly():
    """Test directo del servicio RAG (sin endpoint)"""
    print("\n" + "="*70)
    print("🧪 TEST DIRECTO: RAG Service (ChromaDB)")
    print("="*70 + "\n")
    
    try:
        # Importar el servicio RAG
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "backend"))
        
        from backend.src_v3.infrastructure.ai.rag.chroma_service import ChromaRAGService
        
        print("📚 Inicializando ChromaRAGService...")
        rag_service = ChromaRAGService()
        print(f"✅ Servicio conectado a colección: {rag_service.collection_name}")
        
        # Test: búsqueda de contexto
        print("\n🔍 Probando búsqueda de contexto sobre 'listas en Python'...")
        contexts = rag_service.search(
            query="listas en Python list comprehensions métodos",
            n_results=3
        )
        
        if contexts:
            print(f"✅ Se encontraron {len(contexts)} fragmentos relevantes:")
            for i, ctx in enumerate(contexts, 1):
                print(f"\n   Fragmento {i}:")
                print(f"   - Contenido: {ctx['content'][:150]}...")
                print(f"   - Metadata: {ctx['metadata']}")
                print(f"   - Distancia: {ctx.get('distance', 'N/A')}")
        else:
            print("⚠️ No se encontraron contextos (la base de datos puede estar vacía)")
        
        return True
        
    except ImportError as e:
        print(f"⚠️ No se puede importar el módulo RAG: {e}")
        print("   Este test requiere que el backend esté en el PYTHONPATH")
        return False
    except Exception as e:
        print(f"❌ Error en test RAG: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "🚀"*35)
    print("SUITE DE PRUEBAS: PDF -> RAG -> MISTRAL")
    print("🚀"*35)
    
    # Test 1: Flujo completo E2E
    success_e2e = test_upload_and_generation()
    
    # Test 2: Test directo de RAG (opcional)
    print("\n\n" + "-"*70)
    test_rag = input("\n¿Deseas ejecutar también el test directo de RAG? (s/n): ").lower()
    if test_rag == 's':
        success_rag = test_rag_directly()
    else:
        success_rag = None
    
    # Resumen final
    print("\n\n" + "="*70)
    print("📋 RESUMEN DE PRUEBAS")
    print("="*70)
    print(f"✓ Test E2E (PDF -> RAG -> Mistral): {'✅ PASS' if success_e2e else '❌ FAIL'}")
    if success_rag is not None:
        print(f"✓ Test RAG directo: {'✅ PASS' if success_rag else '❌ FAIL'}")
    print("="*70 + "\n")
    
    if success_e2e:
        print("🎉 ¡Todas las pruebas principales pasaron exitosamente!")
        print("\n💡 Próximos pasos:")
        print("   1. Revisar los ejercicios generados en el dashboard del profesor")
        print("   2. Aprobar los ejercicios para publicarlos")
        print("   3. Los estudiantes podrán ver los ejercicios publicados")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los logs para más detalles.")
        print("\n💡 Solución de problemas:")
        print("   1. Verifica que el backend esté corriendo: docker-compose up")
        print("   2. Verifica que ChromaDB esté activo")
        print("   3. Verifica que MISTRAL_API_KEY esté configurada en .env")
        print("   4. Revisa los logs del backend: docker logs ai_native_backend")
