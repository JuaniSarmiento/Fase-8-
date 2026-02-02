#!/usr/bin/env python3
"""
Script de backup automático para PostgreSQL
Uso: python backup_database.py
"""
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configuración
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "./backups"))
RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "ai_native")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_backup():
    """Crea un backup de la base de datos usando pg_dump"""
    try:
        # Crear directorio si no existe
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Nombre del archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"backup_{DB_NAME}_{timestamp}.sql"
        
        logger.info(f"🔄 Iniciando backup de {DB_NAME}...")
        
        # Comando pg_dump
        env = os.environ.copy()
        env['PGPASSWORD'] = DB_PASSWORD
        
        cmd = [
            "docker", "exec", "-e", f"PGPASSWORD={DB_PASSWORD}",
            "ai_native_postgres", "pg_dump",
            "-h", "localhost",
            "-U", DB_USER,
            "-d", DB_NAME,
            "-F", "c",  # Format custom (más compacto)
            "-b",  # Include blobs
            "-v",  # Verbose
        ]
        
        # Ejecutar backup
        with open(backup_file, 'wb') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                check=True
            )
        
        # Verificar tamaño del backup
        size_mb = backup_file.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Backup completado: {backup_file.name} ({size_mb:.2f} MB)")
        
        return backup_file
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error al crear backup: {e.stderr.decode()}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        raise


def cleanup_old_backups():
    """Elimina backups más antiguos que RETENTION_DAYS"""
    try:
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        deleted_count = 0
        
        for backup_file in BACKUP_DIR.glob("backup_*.sql"):
            # Obtener fecha de modificación
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            if mtime < cutoff_date:
                logger.info(f"🗑️  Eliminando backup antiguo: {backup_file.name}")
                backup_file.unlink()
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"✅ Eliminados {deleted_count} backups antiguos (>{RETENTION_DAYS} días)")
        else:
            logger.info(f"✅ No hay backups para eliminar (retención: {RETENTION_DAYS} días)")
            
    except Exception as e:
        logger.error(f"❌ Error al limpiar backups antiguos: {e}")


def list_backups():
    """Lista todos los backups disponibles"""
    backups = sorted(BACKUP_DIR.glob("backup_*.sql"), reverse=True)
    
    if not backups:
        logger.info("No hay backups disponibles")
        return
    
    logger.info(f"\n📦 Backups disponibles ({len(backups)}):")
    for backup in backups:
        size_mb = backup.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        age_days = (datetime.now() - mtime).days
        logger.info(f"  • {backup.name} - {size_mb:.2f} MB - {age_days} días")


def restore_backup(backup_file: str):
    """Restaura un backup específico"""
    try:
        backup_path = BACKUP_DIR / backup_file
        
        if not backup_path.exists():
            logger.error(f"❌ Backup no encontrado: {backup_file}")
            return False
        
        logger.warning(f"⚠️  RESTAURANDO backup: {backup_file}")
        logger.warning(f"⚠️  Esto REEMPLAZARÁ todos los datos actuales!")
        
        # Confirmar (en producción usar input())
        # confirm = input("¿Continuar? (yes/no): ")
        # if confirm.lower() != 'yes':
        #     logger.info("Restauración cancelada")
        #     return False
        
        # Comando pg_restore
        cmd = [
            "docker", "exec", "-i",
            "-e", f"PGPASSWORD={DB_PASSWORD}",
            "ai_native_postgres", "pg_restore",
            "-h", "localhost",
            "-U", DB_USER,
            "-d", DB_NAME,
            "-c",  # Clean (drop) before restore
            "-v",
        ]
        
        with open(backup_path, 'rb') as f:
            result = subprocess.run(
                cmd,
                stdin=f,
                stderr=subprocess.PIPE,
                check=True
            )
        
        logger.info(f"✅ Backup restaurado exitosamente")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error al restaurar backup: {e.stderr.decode()}")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    logger.info("=" * 60)
    logger.info("🗄️  SISTEMA DE BACKUP - AI-Native MVP")
    logger.info("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            list_backups()
        elif command == "restore" and len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        else:
            logger.error("Uso: python backup_database.py [list|restore <archivo>]")
    else:
        # Backup por defecto
        create_backup()
        cleanup_old_backups()
        list_backups()
    
    logger.info("=" * 60)
