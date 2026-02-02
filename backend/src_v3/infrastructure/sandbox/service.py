"""Simple sandbox service for code execution (Fase 8).

This implementation is intentionally lightweight and does **not** depend on
Docker. It executes code in a subprocess with a strict timeout so it can
run in constrained environments (like the Fase 8 container) without
special host configuration.

Security note: this is suitable for controlled environments and
integration tests, but it is not a full production-grade isolation layer
like the Docker-based sandbox from Fase 7.
"""
from __future__ import annotations

import asyncio
import sys
import time
import logging
from dataclasses import dataclass
from typing import Optional

from prometheus_client import Counter, Histogram

try:  # Optional - only needed when using DockerSandboxService
    import docker  # type: ignore
except Exception:  # pragma: no cover - defensive import
    docker = None


logger = logging.getLogger(__name__)


SANDBOX_EXECUTIONS_TOTAL = Counter(
    "sandbox_executions_total",
    "Total sandbox code executions",
    labelnames=["language", "result"],
)

SANDBOX_EXECUTION_SECONDS = Histogram(
    "sandbox_execution_seconds",
    "Duration of sandbox code executions in seconds",
    labelnames=["language"],
)


@dataclass
class ExecutionResult:
    """Result of a sandbox code execution.

    Kept intentionally simple and compatible with what
    ``SubmitCodeForReviewUseCase`` expects (exit_code, stdout, stderr,
    execution_time).
    """

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None

    @property
    def duration(self) -> float:
        """Alias for compatibility with older duration-based APIs."""
        return self.execution_time


class SimpleSandboxService:
    """Minimal sandbox service using a local subprocess.

    Executes Python code using ``python -c`` with a timeout. This avoids the
    need for Docker inside the Fase 8 container while still providing a
    predictable execution environment for tests and basic feedback.
    """

    def __init__(self, default_timeout: int = 5) -> None:
        self.default_timeout = default_timeout

    async def execute_code(
        self,
        code: str,
        language: str = "python",
        timeout: Optional[int] = None,
        **_: object,
    ) -> ExecutionResult:
        """Execute code in a subprocess with timeout.

        Args:
            code: Source code to execute.
            language: Programming language (only ``python`` supported).
            timeout: Optional timeout in seconds.

        Returns:
            ExecutionResult with stdout, stderr, exit_code and timing.
        """
        if not code or not code.strip():
            return ExecutionResult(
                stdout="",
                stderr="Código vacío",
                exit_code=1,
                execution_time=0.0,
                success=False,
                error_message="Código vacío",
            )

        if language not in {"python", "python3"}:
            return ExecutionResult(
                stdout="",
                stderr=f"Lenguaje no soportado: {language}",
                exit_code=1,
                execution_time=0.0,
                success=False,
                error_message=f"Lenguaje no soportado: {language}",
            )

        timeout = timeout or self.default_timeout
        start = time.monotonic()

        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-c",
                code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                elapsed = time.monotonic() - start
                SANDBOX_EXECUTIONS_TOTAL.labels(language=language, result="timeout").inc()
                SANDBOX_EXECUTION_SECONDS.labels(language=language).observe(elapsed)

                logger.warning(
                    "sandbox_timeout",
                    extra={
                        "language": language,
                        "timeout": timeout,
                        "execution_time": elapsed,
                    },
                )

                return ExecutionResult(
                    stdout="",
                    stderr=f"Timeout: el código tardó más de {timeout}s",
                    exit_code=124,
                    execution_time=elapsed,
                    success=False,
                    error_message=f"Timeout tras {timeout}s",
                )

            elapsed = time.monotonic() - start
            stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
            stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
            exit_code = process.returncode or 0
            result_label = "success" if exit_code == 0 else "error"

            SANDBOX_EXECUTIONS_TOTAL.labels(language=language, result=result_label).inc()
            SANDBOX_EXECUTION_SECONDS.labels(language=language).observe(elapsed)

            logger.info(
                "sandbox_execution",
                extra={
                    "language": language,
                    "exit_code": exit_code,
                    "execution_time": elapsed,
                },
            )

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                execution_time=elapsed,
                success=exit_code == 0,
                error_message=None if exit_code == 0 else "Programa terminó con error",
            )

        except Exception as exc:  # pragma: no cover - defensive
            elapsed = time.monotonic() - start

            SANDBOX_EXECUTIONS_TOTAL.labels(language=language, result="exception").inc()
            SANDBOX_EXECUTION_SECONDS.labels(language=language).observe(elapsed)

            logger.error(
                "sandbox_exception",
                extra={
                    "language": language,
                    "execution_time": elapsed,
                    "error": str(exc),
                },
            )

            return ExecutionResult(
                stdout="",
                stderr=str(exc),
                exit_code=1,
                execution_time=elapsed,
                success=False,
                error_message=f"Error durante ejecución: {exc}",
            )


class DockerSandboxService:
    """Sandbox basado en contenedores Docker efímeros.

    Pensado para entornos endurecidos (pre-producción/producción) donde no
    se desea ejecutar código de alumno en el mismo proceso que el backend.

    Requisitos:
    - Docker accesible vía /var/run/docker.sock
    - Imagen base ligera (por defecto python:3.12-slim)
    - Variable de entorno para seleccionar este backend desde el contenedor

    Nota: El backend Fase 8 sigue usando SimpleSandboxService por defecto.
    Esta clase sólo se activa cuando el contenedor se configura explícitamente
    para ello desde dependencies.py.
    """

    def __init__(
        self,
        image: str = "python:3.12-slim",
        default_timeout: int = 5,
        mem_limit: str = "256m",
        cpu_quota: int = 100000,
    ) -> None:
        if docker is None:  # pragma: no cover - defensive
            raise RuntimeError("Docker SDK no disponible; instala 'docker' o usa SimpleSandboxService")

        self.image = image
        self.default_timeout = default_timeout
        self.mem_limit = mem_limit
        self.cpu_quota = cpu_quota
        self._client = docker.from_env()

    async def execute_code(
        self,
        code: str,
        language: str = "python",
        timeout: Optional[int] = None,
        **_: object,
    ) -> ExecutionResult:
        """Ejecuta código dentro de un contenedor Docker efímero.

        - Contenedor sin red (`network_disabled=True`)
        - Límite de memoria y CPU
        - Sin montajes de volumen de usuario
        """
        if not code or not code.strip():
            return ExecutionResult(
                stdout="",
                stderr="Código vacío",
                exit_code=1,
                execution_time=0.0,
                success=False,
                error_message="Código vacío",
            )

        if language not in {"python", "python3"}:
            return ExecutionResult(
                stdout="",
                stderr=f"Lenguaje no soportado: {language}",
                exit_code=1,
                execution_time=0.0,
                success=False,
                error_message=f"Lenguaje no soportado: {language}",
            )

        timeout = timeout or self.default_timeout
        start = time.monotonic()

        async def _run_in_container() -> ExecutionResult:
            container = None
            try:
                container = self._client.containers.run(
                    self.image,
                    ["python", "-c", code],
                    detach=True,
                    network_disabled=True,
                    mem_limit=self.mem_limit,
                    cpu_quota=self.cpu_quota,
                    stdin_open=False,
                    tty=False,
                )

                try:
                    exit_code = container.wait(timeout=timeout)["StatusCode"]
                except Exception:
                    # Timeout o error durante la espera
                    try:
                        container.kill()
                    except Exception:
                        pass
                    logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace") if container else ""
                    elapsed = time.monotonic() - start
                    SANDBOX_EXECUTIONS_TOTAL.labels(language=language, result="timeout").inc()
                    SANDBOX_EXECUTION_SECONDS.labels(language=language).observe(elapsed)
                    return ExecutionResult(
                        stdout="",
                        stderr=f"Timeout en sandbox Docker (>{timeout}s)\n{logs}",
                        exit_code=124,
                        execution_time=elapsed,
                        success=False,
                        error_message=f"Timeout en sandbox Docker tras {timeout}s",
                    )

                logs = container.logs(stdout=True, stderr=True)
                elapsed = time.monotonic() - start
                stdout = logs.decode("utf-8", errors="replace") if logs else ""

                result_label = "success" if exit_code == 0 else "error"
                SANDBOX_EXECUTIONS_TOTAL.labels(language=language, result=result_label).inc()
                SANDBOX_EXECUTION_SECONDS.labels(language=language).observe(elapsed)

                return ExecutionResult(
                    stdout=stdout,
                    stderr="" if exit_code == 0 else stdout,
                    exit_code=exit_code,
                    execution_time=elapsed,
                    success=exit_code == 0,
                    error_message=None if exit_code == 0 else "Programa terminó con error en sandbox Docker",
                )
            finally:
                if container is not None:
                    try:
                        container.remove(force=True)
                    except Exception:
                        pass

        try:
            # Docker SDK es síncrono; lo envolvemos en un hilo
            result = await asyncio.to_thread(_run_in_container)
            logger.info(
                "docker_sandbox_execution",
                extra={
                    "language": language,
                    "success": result.success,
                    "execution_time": result.execution_time,
                },
            )
            return result
        except Exception as exc:  # pragma: no cover - defensive
            elapsed = time.monotonic() - start
            SANDBOX_EXECUTIONS_TOTAL.labels(language=language, result="exception").inc()
            SANDBOX_EXECUTION_SECONDS.labels(language=language).observe(elapsed)
            logger.error(
                "docker_sandbox_exception",
                extra={
                    "language": language,
                    "execution_time": elapsed,
                    "error": str(exc),
                },
            )
            return ExecutionResult(
                stdout="",
                stderr=str(exc),
                exit_code=1,
                execution_time=elapsed,
                success=False,
                error_message=f"Error en sandbox Docker: {exc}",
            )
