import { useMemo } from "react";
import { dump } from "js-yaml";
import { useProject } from "@/state/projectContext";
import { Card } from "./ui/Card";
import { Heading } from "./ui/Heading";

export function ProjectConfigYaml() {
    const project = useProject();

    const yaml = useMemo(() => {
        return dump(project, { indent: 2 });
    }, [project]);

    return (
        <Card variant="dark" as="section" className="rounded-xl p-5 text-left">
            <Heading className="mb-3 text-gray-100">
                Current Project Config (YAML)
            </Heading>
            <pre className="overflow-x-auto rounded-md bg-black/30 p-4 text-sm leading-6 text-slate-100">
                {yaml}
            </pre>
        </Card>
    );
}
