"""Selftest entry point for observability subsystem.

Verifies:
  1. errors.log receives only ERROR and CRITICAL records, with full context.
  2. Context propagation:
     - Record inside bind_context(...) renders bound context and assertion.
     - Record after scope exit reverts to unknown/none.
     - Sequential scopes do not bleed into each other.
  3. Console stdout receives INFO only as single-line message (no context header).
     Console stderr receives WARNING with full context header.
  4. debug.log is absent by default, and created only when --debug is passed.
  5. logs/latest pointer resolves to the run directory (symlink or latest.txt).
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
import sys

from .context import bind_context
from .filter import (
    ContextFilter,
    ContextFormatter,
    ExactLevelFilter,
)
from .setup import init_logging, resolve_latest_run_dir


def _verify_console_stream_isolation() -> None:
    """Verify that stdout stream receives INFO only (single line, no header) and stderr receives WARNING with header."""
    test_logger = logging.getLogger("observability_console_test")
    test_logger.setLevel(logging.DEBUG)
    test_logger.propagate = False

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    ctx_formatter = ContextFormatter()
    plain_formatter = logging.Formatter("%(message)s")
    ctx_filter = ContextFilter()

    h_out = logging.StreamHandler(stdout_capture)
    h_out.setLevel(logging.INFO)
    h_out.addFilter(ctx_filter)
    h_out.addFilter(ExactLevelFilter(logging.INFO))
    h_out.setFormatter(plain_formatter)
    test_logger.addHandler(h_out)

    h_err = logging.StreamHandler(stderr_capture)
    h_err.setLevel(logging.WARNING)
    h_err.addFilter(ctx_filter)
    h_err.addFilter(ExactLevelFilter(logging.WARNING))
    h_err.setFormatter(ctx_formatter)
    test_logger.addHandler(h_err)

    test_logger.debug("console_debug_probe")
    test_logger.info("console_info_probe")
    test_logger.warning("console_warning_probe")
    test_logger.error("console_error_probe")
    test_logger.critical("console_critical_probe")

    out_text = stdout_capture.getvalue()
    err_text = stderr_capture.getvalue()

    if "console_debug_probe" in out_text or "console_debug_probe" in err_text:
        raise AssertionError("DEBUG leaked to console sinks")
    if "console_info_probe" not in out_text:
        raise AssertionError("INFO record missing from stdout sink")
    if "console_info_probe" in err_text:
        raise AssertionError("INFO record leaked to stderr sink")
    if "stage=" in out_text or "request_id=" in out_text:
        raise AssertionError(f"Context header leaked to stdout sink: {out_text!r}")
    if out_text != "console_info_probe\n":
        raise AssertionError(f"stdout output is not a single line: {out_text!r}")
    if "console_warning_probe" not in err_text:
        raise AssertionError("WARNING record missing from stderr sink")
    if "console_warning_probe" in out_text:
        raise AssertionError("WARNING record leaked to stdout sink")
    if "stage=unknown request_id=none" not in err_text:
        raise AssertionError("Context header missing from stderr sink")
    if "console_error_probe" in out_text or "console_error_probe" in err_text:
        raise AssertionError("ERROR leaked to console sinks")


def run_selftest(debug_flag: bool) -> int:
    """Execute selftest suite and exit 0 on success, non-zero on failure."""
    logs_dir = Path("logs")
    run_dir = init_logging(debug=debug_flag, logs_dir=logs_dir)
    logger = logging.getLogger("selftest")

    # 1. Baseline emission before context binding
    logger.debug("selftest_debug_message")
    logger.info("selftest_info_message")
    logger.warning("selftest_warning_message")
    logger.error("selftest_baseline_error")
    logger.critical("selftest_critical_message")

    # 2. Scope 1: bind context and emit
    with bind_context(stage="safety", request_id="request_142", assertion=11):
        logger.error("payments sum 39660.00 != requested 39661.00")

    # 3. Post Scope 1: emit outside scope to prove reversion to default
    logger.error("selftest_post_scope_1_error")

    # 4. Scope 2: sequential scope with different parameters to prove no bleeding
    with bind_context(stage="forecast", request_id="request_001"):
        logger.error("selftest_scope_2_error")

    # 5. Post Scope 2: emit outside scope 2 to prove clean reversion again
    logger.error("selftest_post_scope_2_error")

    # Flush all handlers to disk
    for handler in logging.getLogger().handlers:
        handler.flush()

    # 6. Verify errors.log and context propagation
    errors_log = run_dir / "errors.log"
    if not errors_log.is_file():
        sys.stderr.write(f"FAIL: {errors_log} was not created.\n")
        return 1

    errors_content = errors_log.read_text(encoding="utf-8")

    # Check required error records
    for required in (
        "selftest_baseline_error",
        "selftest_critical_message",
        "payments sum 39660.00 != requested 39661.00",
        "selftest_post_scope_1_error",
        "selftest_scope_2_error",
        "selftest_post_scope_2_error",
    ):
        if required not in errors_content:
            sys.stderr.write(f"FAIL: errors.log is missing expected record: {required}\n")
            return 1

    # Check forbidden non-error records in errors.log
    for forbidden in ("selftest_debug_message", "selftest_info_message", "selftest_warning_message"):
        if forbidden in errors_content:
            sys.stderr.write(f"FAIL: errors.log contains forbidden non-error record: {forbidden}\n")
            return 1

    # Invariant 2a: Scope 1 exact rendered block
    expected_scope_1 = (
        "stage=safety request_id=request_142 assertion=11\n"
        "payments sum 39660.00 != requested 39661.00"
    )
    if expected_scope_1 not in errors_content:
        sys.stderr.write(
            f"FAIL: Scope 1 context mismatch.\nExpected:\n{expected_scope_1}\nIn content:\n{errors_content}\n"
        )
        return 1

    # Invariant 2b: Post Scope 1 reverted block
    expected_post_scope_1 = (
        "stage=unknown request_id=none\n"
        "selftest_post_scope_1_error"
    )
    if expected_post_scope_1 not in errors_content:
        sys.stderr.write(
            f"FAIL: Post-scope-1 context reversion failed.\nExpected:\n{expected_post_scope_1}\n"
        )
        return 1

    # Invariant 2c: Scope 2 sequential non-bleeding block
    expected_scope_2 = (
        "stage=forecast request_id=request_001\n"
        "selftest_scope_2_error"
    )
    if expected_scope_2 not in errors_content:
        sys.stderr.write(
            f"FAIL: Scope 2 context mismatch or prior bleed.\nExpected:\n{expected_scope_2}\n"
        )
        return 1

    # Invariant 2d: Post Scope 2 reverted block
    expected_post_scope_2 = (
        "stage=unknown request_id=none\n"
        "selftest_post_scope_2_error"
    )
    if expected_post_scope_2 not in errors_content:
        sys.stderr.write(
            f"FAIL: Post-scope-2 context reversion failed.\nExpected:\n{expected_post_scope_2}\n"
        )
        return 1

    # 7. Verify debug.log
    debug_log = run_dir / "debug.log"
    if debug_flag:
        if not debug_log.is_file():
            sys.stderr.write("FAIL: debug.log was not created with --debug.\n")
            return 1
        debug_content = debug_log.read_text(encoding="utf-8")
        if "selftest_debug_message" not in debug_content:
            sys.stderr.write("FAIL: debug.log is missing DEBUG record.\n")
            return 1
    else:
        if debug_log.exists():
            sys.stderr.write("FAIL: debug.log exists when --debug was NOT passed.\n")
            return 1

    # 8. Verify pointer resolution
    resolved = resolve_latest_run_dir(logs_dir)
    if resolved is None:
        sys.stderr.write("FAIL: latest pointer could not be resolved.\n")
        return 1
    if resolved.resolve() != run_dir.resolve():
        sys.stderr.write(
            f"FAIL: latest pointer resolved to {resolved}, expected {run_dir.resolve()}.\n"
        )
        return 1

    # 9. Verify programmatic console isolation and single-line format
    _verify_console_stream_isolation()

    return 0


def main() -> None:
    """CLI entrypoint."""
    debug = "--debug" in sys.argv
    exit_code = run_selftest(debug_flag=debug)
    if exit_code == 0:
        sys.stdout.write("observability selftest passed successfully.\n")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
