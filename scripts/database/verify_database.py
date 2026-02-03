"""
Verificar si la base de datos fue reconstruida correctamente
"""
import psycopg2

try:
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5433,
        user='postgres',
        password='postgres',
        database='ai_native'
    )
    
    cursor = conn.cursor()
    
    # Contar tablas
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    table_count = cursor.fetchone()[0]
    
    print("\n" + "="*60)
    print("VERIFICACION DE BASE DE DATOS")
    print("="*60)
    print(f"\n✓ Conexion exitosa!")
    print(f"✓ Base de datos: ai_native")
    print(f"✓ Tablas encontradas: {table_count}")
    
    # Listar tablas
    if table_count > 0:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"\nTablas creadas:")
        for i, (table,) in enumerate(tables, 1):
            print(f"  {i:2}. {table}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✓ Base de datos lista para usar!")
    print("="*60)
    print("\nProximo paso:")
    print("  python audit_schema.py")
    print()
    
except psycopg2.OperationalError as e:
    print("\n" + "="*60)
    print("ERROR DE CONEXION")
    print("="*60)
    print(f"\n✗ {e}")
    print("\nPosibles causas:")
    print("  1. El script de reconstruccion aun esta ejecutandose")
    print("  2. La contrasena no se reseteo correctamente")
    print("  3. PostgreSQL no esta corriendo")
    print("\nIntenta:")
    print("  - Esperar unos segundos y ejecutar este script de nuevo")
    print("  - Ejecutar: Get-Service postgresql-x64-18")
    print()
except Exception as e:
    print(f"\n✗ Error inesperado: {e}")
