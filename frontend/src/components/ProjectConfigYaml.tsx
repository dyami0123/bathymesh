import { useMemo } from "react";
import { dump } from "js-yaml";
import { useProject } from "@/state/projectContext";

export function ProjectConfigYaml() {
  const project = useProject();

  const yaml = useMemo(() => {
    return dump(project, { indent: 2 });
  }, [project]);

  return (
    <section className="rounded-xl border border-white/20 bg-black/20 p-5 text-left">
      <h2 className="mb-3 text-lg font-semibold">
        Current Project Config (YAML)
      </h2>
      <pre className="overflow-x-auto rounded-md bg-black/30 p-4 text-sm leading-6 text-slate-100">
        {yaml}
      </pre>
    </section>
  );
}
