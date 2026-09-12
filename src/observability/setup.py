"""Observability initialization and sink configuration."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import sys

from .filter import (
    ContextFilter,
    ContextFormatter,
    ExactLevelFilter,
    MinLevelFilter,
)



def _update_latest_pointer(logs_dir: Path, run_dir: Path) -> None:
    """Point logs/latest to run_dir via symlink; fallback to latest.txt on Windows OSError."""
    latest_symlink = logs_dir / "latest"
    latest_txt = logs_dir / "latest.txt"

    # Clean up existing symlink if possible
    try:
        if latest_symlink.is_symlink() or latest_symlink.exists():
            if latest_symlink.is_dir() and not latest_symlink.is_symlink():
                pass
            else:
                latest_symlink.unlink(missing_ok=True)
    except OSError:
        pass

    try:
        os.symlink(run_dir.resolve(), latest_symlink, target_is_directory=True)
    except OSError as err:
        # Raised on default Windows without Developer Mode / elevated privileges
        logging.getLogger("observability").warning(
            "Could not create symlink '%s' (falling back to latest.txt): %s",
            latest_symlink,
            err,
        )
        try:
            latest_txt.write_text(str(run_dir.resolve()), encoding="utf-8")
        except OSError as txt_err:
            logging.getLogger("observability").warning(
                "Could not write fallback latest pointer '%s': %s",
                latest_txt,
                txt_err,
            )


def resolve_latest_run_dir(logs_dir: Path | str = "logs") -> Path | None:
    """Resolve the latest run directory from either logs/latest or logs/latest.txt."""
    logs_path = Path(logs_dir)
    latest_symlink = logs_path / "latest"
    latest_txt = logs_path / "latest.txt"

    if latest_symlink.is_symlink() or latest_symlink.exists():
        try:
            resolved = latest_symlink.resolve()
            if resolved.is_dir():
                return resolved
        except OSError:
            pass

    if latest_txt.is_file():
        try:
            content = latest_txt.read_text(encoding="utf-8").strip()
            path = Path(content)
            if path.is_dir():
                return path.resolve()
        except OSError:
            pass

    return None


def init_logging(
    debug: bool = False,
    logs_dir: Path | str = "logs",
    run_id: str | None = None,
) -> Path:
    """Initialize structured logging sinks for the current run.

    Sinks:
      - logs/<run_id>/errors.log: ERROR and CRITICAL with full tracebacks. Always written.
      - console (stdout): INFO only.
      - console (stderr): WARNING only. Never DEBUG.
      - logs/<run_id>/debug.log: DEBUG and above. ONLY when debug is True. Absent otherwise.

    Returns:
      Path to the created run directory.
    """
    if run_id is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")

    logs_path = Path(logs_dir)
    run_dir = logs_path / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    # Remove existing handlers to avoid bleed across repeated initializations
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()

    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    formatter = ContextFormatter()
    ctx_filter = ContextFilter()

    # 1. errors.log sink: ERROR and above only. Always written.
    errors_path = run_dir / "errors.log"
    errors_handler = logging.FileHandler(errors_path, encoding="utf-8", mode="a")
    errors_handler.setLevel(logging.ERROR)
    errors_handler.addFilter(ctx_filter)
    errors_handler.addFilter(MinLevelFilter(logging.ERROR))
    errors_handler.setFormatter(formatter)
    root_logger.addHandler(errors_handler)

    # 2. console sink (stdout: INFO only, single line, no context header)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(ctx_filter)
    stdout_handler.addFilter(ExactLevelFilter(logging.INFO))
    stdout_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(stdout_handler)


    # 3. console sink (stderr: WARNING only)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.addFilter(ctx_filter)
    stderr_handler.addFilter(ExactLevelFilter(logging.WARNING))
    stderr_handler.setFormatter(formatter)
    root_logger.addHandler(stderr_handler)

    # 4. debug.log sink: DEBUG and above only when debug is True
    if debug:
        debug_path = run_dir / "debug.log"
        debug_handler = logging.FileHandler(debug_path, encoding="utf-8", mode="a")
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.addFilter(ctx_filter)
        debug_handler.addFilter(MinLevelFilter(logging.DEBUG))
        debug_handler.setFormatter(formatter)
        root_logger.addHandler(debug_handler)

    # Pointer management: latest symlink or latest.txt fallback
    _update_latest_pointer(logs_path, run_dir)

    return run_dir
