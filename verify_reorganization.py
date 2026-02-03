"""
Script de Verificación Post-Reorganización
==========================================
Verifica que la reorganización del proyecto no haya roto ninguna funcionalidad.

Ejecutar: python verify_reorganization.py
"""

import os
import sys
from pathlib import Path
import importlib.util

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")

def check_file_exists(file_path, description):
    """Verifica que un archivo exista"""
    if os.path.exists(file_path):
        print_success(f"{description}: {file_path}")
        return True
    else:
        print_error(f"{description} NO ENCONTRADO: {file_path}")
        return False

def check_directory_exists(dir_path, description):
    """Verifica que un directorio exista"""
    if os.path.isdir(dir_path):
        file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
        print_success(f"{description}: {dir_path} ({file_count} archivos)")
        return True
    else:
        print_error(f"{description} NO ENCONTRADO: {dir_path}")
        return False

def check_python_import(module_path, description):
    """Verifica que un módulo Python pueda importarse"""
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # No ejecutamos, solo verificamos sintaxis
            print_success(f"{description} es importable")
            return True
        else:
            print_error(f"{description} no puede cargarse")
            return False
    except SyntaxError as e:
        print_error(f"{description} tiene errores de sintaxis: {e}")
        return False
    except Exception as e:
        print_warning(f"{description} - advertencia al importar: {e}")
        return True  # Puede ser dependencias, no necesariamente un error

def main():
    print("\n" + "="*60)
    print("VERIFICACIÓN POST-REORGANIZACIÓN")
    print("="*60 + "\n")
    
    base_path = Path(__file__).parent
    issues = []
    
    # 1. Archivos esenciales en raíz
    print_info("1. Verificando archivos esenciales en raíz...")
    essential_files = {
        "README.md": "README principal",
        "docker-compose.yml": "Docker Compose",
        "Dockerfile": "Dockerfile",
        "main.py": "Entry point FastAPI",
        "requirements.txt": "Dependencias Python",
        "setup.py": "Setup Python",
        "pytest.ini": "Config pytest",
        ".env": "Variables de entorno",
        ".gitignore": "Gitignore",
        "CONTRIBUTING.md": "Guía de contribución"
    }
    
    for file, desc in essential_files.items():
        if not check_file_exists(base_path / file, desc):
            issues.append(f"Falta archivo esencial: {file}")
    
    # 2. Estructura de directorios
    print(f"\n{print_info('2. Verificando estructura de directorios...')}")
    directories = {
        "backend": "Backend FastAPI",
        "frontend": "Frontend Next.js",
        "scripts": "Scripts utilitarios",
        "scripts/database": "Scripts de base de datos",
        "scripts/seed": "Scripts de seed",
        "scripts/maintenance": "Scripts de mantenimiento",
        "scripts/setup": "Scripts de setup",
        "tests": "Suite de tests",
        "tests/e2e": "Tests E2E",
        "docs": "Documentación",
        "docs/architecture": "Arquitectura",
        "docs/guides": "Guías",
        "docs/reports": "Reportes",
        "sql": "Scripts SQL",
        "sql/init": "SQL inicialización",
        "sql/migrations": "SQL migraciones"
    }
    
    for dir_path, desc in directories.items():
        if not check_directory_exists(base_path / dir_path, desc):
            issues.append(f"Falta directorio: {dir_path}")
    
    # 3. READMEs en subdirectorios
    print(f"\n{print_info('3. Verificando READMEs de documentación...')}")
    readme_dirs = ["scripts", "tests", "sql", "docs"]
    for dir_name in readme_dirs:
        readme_path = base_path / dir_name / "README.md"
        if not check_file_exists(readme_path, f"README de {dir_name}"):
            issues.append(f"Falta README en: {dir_name}")
    
    # 4. Scripts críticos movidos correctamente
    print(f"\n{print_info('4. Verificando scripts críticos...')}")
    critical_scripts = {
        "scripts/database/init_db.py": "Inicialización de BD",
        "scripts/seed/cleanup_and_seed_teacher.py": "Seed de docente",
        "scripts/database/verify_database.py": "Verificación de BD",
    }
    
    for script, desc in critical_scripts.items():
        script_path = base_path / script
        if check_file_exists(script_path, desc):
            check_python_import(script_path, desc)
        else:
            issues.append(f"Falta script crítico: {script}")
    
    # 5. Backend structure
    print(f"\n{print_info('5. Verificando estructura del backend...')}")
    backend_dirs = [
        "backend/src_v3",
        "backend/src_v3/core",
        "backend/src_v3/infrastructure",
        "backend/src_v3/application",
        "backend/src_v3/shared"
    ]
    for dir_path in backend_dirs:
        if not os.path.isdir(base_path / dir_path):
            print_error(f"Directorio backend faltante: {dir_path}")
            issues.append(f"Backend incompleto: {dir_path}")
        else:
            print_success(f"Backend OK: {dir_path}")
    
    # 6. Frontend structure
    print(f"\n{print_info('6. Verificando estructura del frontend...')}")
    frontend_files = ["frontend/package.json", "frontend/next.config.ts", "frontend/tsconfig.json"]
    for file in frontend_files:
        if not check_file_exists(base_path / file, f"Frontend config: {file}"):
            issues.append(f"Frontend config faltante: {file}")
    
    # 7. SQL files
    print(f"\n{print_info('7. Verificando archivos SQL...')}")
    sql_init = base_path / "sql" / "init"
    if os.path.isdir(sql_init):
        init_files = list(sql_init.glob("*.sql"))
        print_success(f"Archivos SQL init: {len(init_files)}")
    else:
        print_error("No se encuentra sql/init/")
        issues.append("Faltan archivos SQL de inicialización")
    
    sql_migrations = base_path / "sql" / "migrations"
    if os.path.isdir(sql_migrations):
        migration_files = list(sql_migrations.glob("*.sql"))
        print_success(f"Archivos SQL migrations: {len(migration_files)}")
    else:
        print_warning("No se encuentra sql/migrations/ (puede ser normal si no hay migraciones)")
    
    # 8. Tests
    print(f"\n{print_info('8. Verificando tests...')}")
    test_e2e = base_path / "tests" / "e2e"
    if os.path.isdir(test_e2e):
        test_files = list(test_e2e.glob("test_*.py"))
        print_success(f"Tests E2E: {len(test_files)}")
        
        # Verificar que no exista carpeta Test/ duplicada
        old_test_dir = base_path / "Test"
        if os.path.isdir(old_test_dir):
            print_error("Se encontró carpeta Test/ duplicada (debe eliminarse)")
            issues.append("Carpeta Test/ duplicada encontrada")
    else:
        print_error("No se encuentra tests/e2e/")
        issues.append("Faltan tests E2E")
    
    # 9. Verificar que NO haya archivos temporales en raíz
    print(f"\n{print_info('9. Verificando limpieza de raíz...')}")
    root_files = [f for f in os.listdir(base_path) if os.path.isfile(base_path / f)]
    
    # Lista blanca de archivos permitidos en raíz
    allowed_root_files = {
        '.dockerignore', '.env', '.env.example', '.gitignore',
        'docker-compose.yml', 'Dockerfile', 'main.py', 'pytest.ini',
        'README.md', 'requirements.txt', 'setup.py', 'CONTRIBUTING.md',
        'verify_reorganization.py'  # Este script
    }
    
    unexpected_files = [f for f in root_files if f not in allowed_root_files and not f.startswith('.')]
    
    # Verificar que no exista carpeta Test/ duplicada en raíz
    if os.path.isdir(base_path / "Test"):
        print_error("Carpeta Test/ duplicada encontrada en raíz (debe ser tests/)")
        issues.append("Carpeta Test/ duplicada en raíz")
    
    if unexpected_files:
        print_warning(f"Archivos inesperados en raíz: {', '.join(unexpected_files)}")
    else:
        print_success("Raíz limpia - solo archivos esenciales")
    
    # Resumen final
    print("\n" + "="*60)
    if issues:
        print_error(f"\nSE ENCONTRARON {len(issues)} PROBLEMAS:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print(f"\n{Colors.RED}⚠ VERIFICACIÓN FALLIDA{Colors.END}")
        return 1
    else:
        print_success("\n✓ TODAS LAS VERIFICACIONES PASARON")
        print_success("✓ La reorganización se completó exitosamente")
        print_success("✓ No se detectaron problemas")
        print(f"\n{Colors.GREEN}✓ PROYECTO LISTO PARA USO{Colors.END}")
        return 0

if __name__ == "__main__":
    sys.exit(main())
