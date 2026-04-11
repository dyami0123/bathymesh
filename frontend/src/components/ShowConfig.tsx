import { useState, useEffect } from "react";
import { defaultsApiConfigDefaultsGet } from "../client";
import type { ProjectConfigOutput } from "../client";

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
    <div className="rounded-xl p-6">
      <h2 className="text">Hi</h2>
      {config && <div>{}</div>}
      {JSON.stringify(config, null, 2)}
    </div>
  );
}
