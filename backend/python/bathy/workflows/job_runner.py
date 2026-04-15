"""In-process async job runner backed by a blocking queue."""

import logging
from dataclasses import dataclass
from datetime import datetime, UTC
from queue import Queue
from threading import Lock, Thread
from typing import Any, Callable, Union
from uuid import uuid4

from bathy.data_model import JobStatus

logger = logging.getLogger(__name__)


JobCallable = Callable[[], Union[dict[str, Any], None]]


@dataclass(frozen=True)
class _QueuedJob:
    job_id: str
    job_type: str
    task: JobCallable


class JobRunner:
    """Runs submitted jobs on a single background worker thread."""

    _jobs: dict[str, JobStatus]
    _queue: Queue[Union[_QueuedJob, None]]
    _lock: Lock
    _worker_thread: Union[Thread, None]

    def __init__(self) -> None:
        self._jobs = {}
        self._queue = Queue()
        self._lock = Lock()
        self._worker_thread = None

    def start(self) -> None:
        """Start the background worker if it is not already running."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            return

        self._worker_thread = Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("Job runner worker started")

    def stop(self) -> None:
        """Stop the worker thread gracefully."""
        if self._worker_thread is None:
            return

        self._queue.put(None)
        self._worker_thread.join(timeout=5.0)
        self._worker_thread = None
        logger.info("Job runner worker stopped")

    def submit_job(self, job_type: str, task: JobCallable) -> JobStatus:
        """Enqueue a job and return its initial status."""
        self.start()

        job_id = str(uuid4())
        status = JobStatus(
            jobId=job_id,
            status="pending",
            jobType=job_type,
            createdAt=datetime.now(UTC),
        )

        with self._lock:
            self._jobs[job_id] = status

        self._queue.put(_QueuedJob(job_id=job_id, job_type=job_type, task=task))
        return status

    def get_job_status(self, job_id: str) -> Union[JobStatus, None]:
        """Return the current status for a job id if it exists."""
        with self._lock:
            return self._jobs.get(job_id)

    def _worker_loop(self) -> None:
        while True:
            queued_job = self._queue.get()
            if queued_job is None:
                self._queue.task_done()
                break

            self._mark_processing(queued_job.job_id)
            try:
                result = queued_job.task()
                self._mark_completed(queued_job.job_id, result=result)
            except Exception as exc:  # noqa: BLE001 - job errors must be captured.
                logger.exception("Job %s failed", queued_job.job_id)
                self._mark_failed(queued_job.job_id, error=str(exc))
            finally:
                self._queue.task_done()

    def _mark_processing(self, job_id: str) -> None:
        with self._lock:
            status = self._jobs[job_id]
            self._jobs[job_id] = status.model_copy(
                update={
                    "status": "processing",
                    "startedAt": datetime.now(UTC),
                }
            )

    def _mark_completed(
        self, job_id: str, result: Union[dict[str, Any], None] = None
    ) -> None:
        with self._lock:
            status = self._jobs[job_id]
            self._jobs[job_id] = status.model_copy(
                update={
                    "status": "completed",
                    "completedAt": datetime.now(UTC),
                    "result": result,
                }
            )

    def _mark_failed(self, job_id: str, error: str) -> None:
        with self._lock:
            status = self._jobs[job_id]
            self._jobs[job_id] = status.model_copy(
                update={
                    "status": "failed",
                    "completedAt": datetime.now(UTC),
                    "error": error,
                }
            )


job_runner = JobRunner()
