import { useProject } from "@/state/projectContext";
import { useState, useEffect, useRef } from "react";
import { getJobStatusApiJobsJobIdGet } from "@/client";
import type { JobStatus } from "@/client";

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
        <div style={{ padding: "20px", fontFamily: "sans-serif" }}>
            <div style={{ marginBottom: "20px" }}>
                <strong>Execute Workflows:</strong> {project.project_id}
                <select
                    value={jobType}
                    onChange={(e) => setJobtype(e.target.value as JobType)}
                    style={{
                        marginLeft: "10px",
                        padding: "8px",
                        fontSize: "16px",
                        cursor: "pointer",
                    }}
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
                    style={{
                        padding: "10px 20px",
                        fontSize: "16px",
                        cursor: "pointer",
                        backgroundColor: "#4CAF50",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                    }}
                >
                    Submit Job
                </button>
            )}

            {jobState.type === "submitting" && (
                <div style={{ color: "#666" }}>
                    <p>⏳ Submitting job...</p>
                </div>
            )}

            {jobState.type === "polling" && (
                <div
                    style={{
                        marginTop: "20px",
                        padding: "15px",
                        borderRadius: "4px",
                    }}
                >
                    <p>
                        <strong>Running Job ID:</strong> {jobState.jobId}
                    </p>
                </div>
            )}

            {lastJob && (
                <div
                    style={{
                        marginTop: "20px",
                        padding: "15px",
                        borderRadius: "4px",
                        border: "1px solid #ddd",
                    }}
                >
                    <p>
                        <strong>Last Job:</strong>{" "}
                        <pre style={{ fontSize: "12px", overflow: "auto" }}>
                            {JSON.stringify(lastJob, null, 2)}
                            {JSON.stringify(jobState, null, 2)}
                        </pre>
                    </p>
                    {lastJob.type === "error" && (
                        <p style={{ color: "#c62828" }}>
                            Error: {lastJob.message}
                        </p>
                    )}
                </div>
            )}

            {lastJob && lastJob.type === "error" && (
                <div
                    style={{
                        marginTop: "20px",
                        padding: "15px",
                        backgroundColor: "#ffebee",
                        color: "#c62828",
                        borderRadius: "4px",
                    }}
                >
                    <p>❌ {lastJob.message}</p>
                </div>
            )}

            {lastJob && lastJob.type == "completed" && (
                <div
                    style={{
                        marginTop: "10px",
                        padding: "8px 16px",
                        cursor: "pointer",
                        borderRadius: "4px",
                    }}
                >
                    Last Job Status: {lastJob.jobStatus.status} (Type:{" "}
                    {lastJob.job_type})
                </div>
            )}
        </div>
    );
}
