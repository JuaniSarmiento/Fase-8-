# Script de Backup Automático para Cron/Tarea Programada
# Linux/Mac: Agregar a crontab con: crontab -e
# 0 2 * * * cd /path/to/project && python backup_database.py >> logs/backup.log 2>&1

# Windows: Crear tarea programada con Task Scheduler
# O usar este script PowerShell:

# ============================================================================
# LINUX/MAC CRON
# ============================================================================
# Backup diario a las 2 AM
# 0 2 * * * cd /path/to/fase8 && /usr/bin/python3 backup_database.py >> logs/backup.log 2>&1

# Backup cada 6 horas
# 0 */6 * * * cd /path/to/fase8 && /usr/bin/python3 backup_database.py >> logs/backup.log 2>&1

# Backup cada domingo a las 3 AM
# 0 3 * * 0 cd /path/to/fase8 && /usr/bin/python3 backup_database.py >> logs/backup.log 2>&1


# ============================================================================
# WINDOWS TASK SCHEDULER (PowerShell)
# ============================================================================
# Ejecutar este script para crear la tarea programada:
#
# $action = New-ScheduledTaskAction -Execute "python" -Argument "backup_database.py" -WorkingDirectory "C:\Users\juani\Desktop\Fase 8"
# $trigger = New-ScheduledTaskTrigger -Daily -At 2am
# $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount
# $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable
# Register-ScheduledTask -TaskName "AI-Native Backup" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Backup diario de la base de datos AI-Native"


# ============================================================================
# DOCKER COMPOSE - BACKUP AUTOMÁTICO
# ============================================================================
# Agregar este servicio a docker-compose.yml:
#
# backup:
#   image: prodrigestivill/postgres-backup-local
#   restart: always
#   volumes:
#     - ./backups:/backups
#   environment:
#     - POSTGRES_HOST=postgres
#     - POSTGRES_DB=ai_native
#     - POSTGRES_USER=postgres
#     - POSTGRES_PASSWORD=postgres
#     - SCHEDULE=@daily  # Backup diario a medianoche
#     - BACKUP_KEEP_DAYS=30
#     - BACKUP_KEEP_WEEKS=8
#     - BACKUP_KEEP_MONTHS=6
#   depends_on:
#     - postgres


# ============================================================================
# SUBIR BACKUPS A LA NUBE (Google Drive, S3, Dropbox)
# ============================================================================
# Instalar rclone: https://rclone.org/install/
#
# Configurar:
# rclone config
#
# Script para subir automáticamente:
#
# #!/bin/bash
# python backup_database.py
# rclone copy ./backups remote:ai-native-backups/$(date +%Y-%m)
# echo "Backup subido a la nube"
