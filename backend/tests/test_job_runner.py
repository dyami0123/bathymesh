"""Tests for queue-backed async job runner."""

from __future__ import annotations

import time
from threading import Event

from bathy.workflows.job_runner import JobRunner


def _wait_for_terminal_status(
    runner: JobRunner,
    job_id: str,
    timeout_seconds: float = 2.0,
) -> str:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        status = runner.get_job_status(job_id)
        if status is None:
            raise AssertionError("Expected job status to exist")

        if status.status in {"completed", "failed"}:
            return status.status

        time.sleep(0.01)

    raise AssertionError("Timed out waiting for job to complete")


def test_job_runner_completes_job() -> None:
    runner = JobRunner()
    runner.start()

    try:
        submitted = runner.submit_job(
            job_type="test_success",
            task=lambda: {"ok": "true"},
        )
        final_state = _wait_for_terminal_status(runner, submitted.jobId)

        assert final_state == "completed"
        status = runner.get_job_status(submitted.jobId)
        assert status is not None
        assert status.result == {"ok": "true"}
        assert status.error is None
        assert status.startedAt is not None
        assert status.completedAt is not None
    finally:
        runner.stop()


def test_job_runner_processes_queue_in_order() -> None:
    runner = JobRunner()
    runner.start()

    gate = Event()

    try:
        first = runner.submit_job(
            job_type="first",
            task=lambda: gate.wait(timeout=1.0) or {"first": "done"},
        )
        second = runner.submit_job(
            job_type="second",
            task=lambda: {"second": "done"},
        )

        time.sleep(0.05)

        first_status = runner.get_job_status(first.jobId)
        second_status = runner.get_job_status(second.jobId)
        assert first_status is not None
        assert second_status is not None
        assert first_status.status == "processing"
        assert second_status.status == "pending"

        gate.set()

        assert _wait_for_terminal_status(runner, first.jobId) == "completed"
        assert _wait_for_terminal_status(runner, second.jobId) == "completed"
    finally:
        runner.stop()


def test_job_runner_captures_failures() -> None:
    runner = JobRunner()
    runner.start()

    def failing_task() -> None:
        raise RuntimeError("boom")

    try:
        submitted = runner.submit_job(
            job_type="test_failure",
            task=failing_task,
        )
        final_state = _wait_for_terminal_status(runner, submitted.jobId)

        assert final_state == "failed"
        status = runner.get_job_status(submitted.jobId)
        assert status is not None
        assert status.error is not None
        assert "boom" in status.error
        assert status.completedAt is not None
    finally:
        runner.stop()
