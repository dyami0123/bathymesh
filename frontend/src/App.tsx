import "./index.css";

import { ContourOptions } from "./components/ContourOptions";
import { ProjectConfigYaml } from "./components/ProjectConfigYaml";
import type { ProjectConfigOutput } from "./client";

import { defaultsApiConfigDefaultsGet } from "./client";
import { useEffect, useState } from "react";
import { ProjectProvider } from "./state/projectContext";

export function App() {
  const [initialProject, setInitialProject] =
    useState<ProjectConfigOutput | null>(null);

  useEffect(() => {
    defaultsApiConfigDefaultsGet().then((result) => {
      setInitialProject(result.data ?? null);
    });
  }, []);

  if (!initialProject) return <div>Loading...</div>;

  return (
    <ProjectProvider initialProject={initialProject}>
      <div className="relative z-10 mx-auto grid w-full max-w-7xl gap-8 p-8 text-left lg:grid-cols-2">
        <ContourOptions />
        <ProjectConfigYaml />
      </div>
    </ProjectProvider>
  );
}

export default App;
