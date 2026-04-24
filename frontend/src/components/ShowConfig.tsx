import { useState, useEffect } from "react";
import { defaultsApiConfigDefaultsGet } from "../client";
import type { ProjectConfigOutput } from "../client";
import { Card } from "./ui/Card";
import { Heading } from "./ui/Heading";

export function ShowConfig() {
    const [config, setConfig] = useState<ProjectConfigOutput | null>(null);

    const loadConfig = async () => {
        const retrievedConfig = (await defaultsApiConfigDefaultsGet()).data;
        setConfig(retrievedConfig ?? null);
    };

    useEffect(() => {
        void loadConfig();
    }, []);

    return (
        <Card className="rounded-xl p-6">
            <Heading>Hi</Heading>
            {config && <div>{}</div>}
            {JSON.stringify(config, null, 2)}
        </Card>
    );
}
