import { getJobStatusApiJobsJobIdGet } from "@/client";
import type { JobStatus } from "@/client";

const DEFAULT_POLL_INTERVAL_MS = 1000;
const DEFAULT_TIMEOUT_MS = 60_000;

type ApiEndpoint<TBody> = (args: {
    path: { project_id: string };
    throwOnError: true;
    body: TBody;
}) => Promise<{ data: JobStatus }>;

export type BlockingApiCallOptions = {
    pollIntervalMs?: number;
    timeoutMs?: number;
};

/**
 * Submit a job and wait until it reaches a terminal status.
 */
export async function blockingApiCall<TBody>({
    endpoint,
    project_id,
    body,
    options,
}: {
    endpoint: ApiEndpoint<TBody>;
    project_id: string;
    body: TBody;
    options?: BlockingApiCallOptions;
}): Promise<JobStatus> {
    const pollIntervalMs = options?.pollIntervalMs ?? DEFAULT_POLL_INTERVAL_MS;
    const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS;
    const startedAt = Date.now();

    const firstResponse = await endpoint({
        path: { project_id },
        throwOnError: true,
        body,
    });

    const submittedStatus = firstResponse.data;
    const jobId = submittedStatus.jobId;

    while (true) {
        const response = await getJobStatusApiJobsJobIdGet({
            path: { job_id: jobId },
            throwOnError: true,
        });

        const status = response.data;

        if (status.status === "completed") {
            return status;
        }

        if (status.status === "failed") {
            throw new Error(status.error || `Job ${jobId} failed`);
        }

        if (Date.now() - startedAt > timeoutMs) {
            throw new Error(
                `Timed out waiting for job ${jobId} after ${timeoutMs}ms`
            );
        }

        await sleep(pollIntervalMs);
    }
}

function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => {
        setTimeout(resolve, ms);
    });
}
