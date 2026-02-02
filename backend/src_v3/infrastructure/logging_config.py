"""
Enhanced Logging Configuration for Production
Guarda errores en archivos y opcionalmente envía a Sentry
"""
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import sys

# Configuración
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = Path(os.getenv("LOG_DIR", "./logs"))
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"
SENTRY_DSN = os.getenv("SENTRY_DSN", "")  # Opcional: Sentry para alertas

# Crear directorio de logs
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging():
    """Configura logging con rotación de archivos"""
    
    # Formato detallado
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Formato simple para consola
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    
    # Limpiar handlers existentes
    root_logger.handlers = []
    
    # 1. CONSOLA (siempre activo)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    if LOG_TO_FILE:
        # 2. ARCHIVO GENERAL (rotación por tamaño)
        general_file = LOG_DIR / "backend.log"
        file_handler = RotatingFileHandler(
            general_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # 3. ARCHIVO DE ERRORES (solo ERROR y CRITICAL)
        error_file = LOG_DIR / "errors.log"
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
        
        # 4. ARCHIVO DIARIO (rotación por día)
        daily_file = LOG_DIR / "daily.log"
        daily_handler = TimedRotatingFileHandler(
            daily_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Mantener 30 días
            encoding='utf-8'
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(daily_handler)
    
    # 5. SENTRY (opcional, para alertas en producción)
    if SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.logging import LoggingIntegration
            
            # Configurar Sentry
            sentry_sdk.init(
                dsn=SENTRY_DSN,
                environment=os.getenv("ENVIRONMENT", "development"),
                traces_sample_rate=0.1,  # 10% de traces
                integrations=[
                    LoggingIntegration(
                        level=logging.INFO,
                        event_level=logging.ERROR  # Solo enviar ERRORs a Sentry
                    )
                ]
            )
            root_logger.info("✅ Sentry integration enabled")
        except ImportError:
            root_logger.warning("⚠️  Sentry DSN provided but sentry-sdk not installed. Install with: pip install sentry-sdk")
        except Exception as e:
            root_logger.warning(f"⚠️  Failed to initialize Sentry: {e}")
    
    # Silenciar loggers ruidosos
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    root_logger.info("=" * 60)
    root_logger.info("🚀 AI-Native MVP V3 - Logging initialized")
    root_logger.info(f"📝 Log Level: {LOG_LEVEL}")
    root_logger.info(f"📁 Log Directory: {LOG_DIR.absolute()}")
    root_logger.info(f"💾 File Logging: {'✅ Enabled' if LOG_TO_FILE else '❌ Disabled'}")
    root_logger.info(f"🔔 Sentry Alerts: {'✅ Enabled' if SENTRY_DSN else '❌ Disabled'}")
    root_logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """Helper para obtener logger configurado"""
    return logging.getLogger(name)


# Auto-setup al importar
if not logging.getLogger().hasHandlers():
    setup_logging()
