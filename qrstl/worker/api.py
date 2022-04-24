from redis import Redis
from rq import Queue
from rq.job import Job

from qrstl.qr import QrCodeParams


def get_queue() -> Queue:
    return Queue("qrstl", connection=Redis())


def enqueue_code_job(params: QrCodeParams) -> Job:
    q = get_queue()
    job_id = f"code.{params.sha}"

    job = q.fetch_job(job_id)
    if not job:
        job = q.enqueue("qrstl.worker.jobs.generate_scad_code", params, job_id=job_id)

    return job


def enqueue_preview_job(params: QrCodeParams) -> Job:
    q = get_queue()
    job_id = f"preview.{params.sha}"

    code_job = enqueue_code_job(params)

    job = q.fetch_job(job_id)
    if not job:
        job = q.enqueue(
            "qrstl.worker.jobs.generate_scad_preview",
            params,
            job_id=job_id,
            depends_on=code_job,
        )

    return job
