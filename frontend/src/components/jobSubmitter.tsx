import { useProject } from "@/state/projectContext";
import { useState, useEffect, useRef } from "react";
import { getJobStatusApiJobsJobIdGet } from "@/client";
import type { JobStatus } from "@/client";
import { cn } from "@/lib/cn";
import { card, button, select, badge } from "@/components/ui/styles";

// type JobType = "calculate_heightmap" | "generate_mesh";

const POLL_INTERVAL_MS = 1000; // Poll every 1 second

type SubmitJobApi<TBody> = (args: {
    path: { project_id: string };
    throwOnError: true;
    body: TBody;
}) => Promise<{ data: JobStatus }>;

type EndpointMap<TJobType extends string, TBody> = {
    [K in TJobType]: SubmitJobApi<TBody>;
};

export function JobSubmitButton<const TJobType extends string, TBody>({
    endpoints,
    body,
}: {
    // Mapping from "job type" to submit endpoint
    endpoints: EndpointMap<TJobType, TBody>;
    body: TBody;
}) {
    type JobType = TJobType;

    type JobRunState =
        | { type: "idle"; job_type: JobType }
        | { type: "submitting"; job_type: JobType }
        | {
              type: "polling";
              jobId: string;
              jobStatus: JobStatus;
              job_type: JobType;
          }
        | {
              type: "completed";
              jobId: string;
              jobStatus: JobStatus;
              job_type: JobType;
          }
        | { type: "error"; message: string };

    const jobTypes = Object.keys(endpoints) as JobType[];
    const first_endpoint = jobTypes[0] as JobType;

    const project = useProject();
    const [jobType, setJobtype] = useState<JobType>(first_endpoint);

    const [jobState, setJobState] = useState<JobRunState>({
        type: "idle",
        job_type: jobType,
    });
    const [lastJob, setLastJob] = useState<JobRunState | null>(null);

    const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

    const handleSubmitJob = async () => {
        setJobState({ type: "submitting", job_type: jobType });

        const submitJobApi = endpoints[jobType];

        try {
            const response = await submitJobApi({
                path: { project_id: project.project_id },
                throwOnError: true,
                body: body,
            });

            // Successfully submitted - start polling
            setJobState({
                type: "polling",
                jobId: response.data.jobId,
                jobStatus: response.data,
                job_type: jobType,
            });
        } catch (error) {
            setJobState({
                type: "error",
                message: `Failed to submit job: ${error instanceof Error ? error.message : String(error)}`,
            });
        }
    };

    const stopPolling = () => {
        // Stop polling on error
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
        }
        setJobState({ type: "idle", job_type: jobType });
    };

    useEffect(() => {
        if (jobState.type !== "polling") return;

        const checkStatus = async () => {
            try {
                const response = await getJobStatusApiJobsJobIdGet({
                    path: { job_id: jobState.jobId },
                    throwOnError: true,
                });
                const status = response.data;
                const job_type = status.jobType as JobType;

                if (status.status === "completed") {
                    const job_state = {
                        type: "completed",
                        jobId: jobState.jobId,
                        jobStatus: status,
                        job_type: job_type,
                    } as JobRunState;
                    setJobState(job_state);
                    setLastJob(job_state);
                    stopPolling();
                } else if (status.status === "failed") {
                    const job_state = {
                        type: "error",
                        message: status.error || "No Error Provided",
                    } as JobRunState;
                    setJobState(job_state);
                    setLastJob(job_state);
                    stopPolling();
                } else {
                    setJobState({
                        type: "polling",
                        jobId: jobState.jobId,
                        jobStatus: status,
                        job_type: job_type,
                    });
                }
            } catch (error) {
                setJobState({
                    type: "error",
                    message: `Failed to check job status: ${error instanceof Error ? error.message : String(error)}`,
                });
                setLastJob(jobState);
                stopPolling();
            }
        };

        // Check immediately
        checkStatus();
        // Set up interval polling
        pollIntervalRef.current = setInterval(checkStatus, POLL_INTERVAL_MS);

        // Cleanup: cancel the interval when component unmounts or state changes
        return stopPolling;
    }, [jobState.type === "polling" ? jobState.jobId : null]);

    return (
        <div className="p-5">
            <div className="mb-5 flex items-center gap-3">
                <strong>Execute Workflows:</strong> {project.project_id}
                <select
                    value={jobType}
                    onChange={(e) => setJobtype(e.target.value as JobType)}
                    className={cn(select(), "ml-2 w-auto")}
                >
                    {jobTypes.map((type) => (
                        <option key={type} value={type}>
                            {type}
                        </option>
                    ))}
                </select>
            </div>

            {jobState.type === "idle" && (
                <button
                    onClick={handleSubmitJob}
                    className={button({ intent: "primary" })}
                >
                    Submit Job
                </button>
            )}

            {jobState.type === "submitting" && (
                <div className="text-gray-500">
                    <p>⏳ Submitting job...</p>
                </div>
            )}

            {jobState.type === "polling" && (
                <div className={cn(card({ variant: "inset" }), "mt-5")}>
                    <p>
                        <strong>Running Job ID:</strong> {jobState.jobId}
                    </p>
                </div>
            )}

            {lastJob && (
                <div className={cn(card(), "mt-5")}>
                    <p>
                        <strong>Last Job:</strong>{" "}
                        <pre className="overflow-auto text-xs">
                            {JSON.stringify(lastJob, null, 2)}
                            {JSON.stringify(jobState, null, 2)}
                        </pre>
                    </p>
                    {lastJob.type === "error" && (
                        <p className="text-sm text-red-700">
                            Error: {lastJob.message}
                        </p>
                    )}
                </div>
            )}

            {lastJob && lastJob.type === "error" && (
                <div className={cn(badge({ intent: "error" }), "mt-5")}>
                    <p>❌ {lastJob.message}</p>
                </div>
            )}

            {lastJob && lastJob.type == "completed" && (
                <div className={cn(card({ variant: "inset" }), "mt-3")}>
                    Last Job Status: {lastJob.jobStatus.status} (Type:{" "}
                    {lastJob.job_type})
                </div>
            )}
        </div>
    );
}
