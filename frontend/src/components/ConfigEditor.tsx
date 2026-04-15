import { ContourOptions } from "./ConfigForms/ContourOptions";
import { PostProcessingConfig } from "./ConfigForms/PostProcessingConfig";
import { ProjectConfigYaml } from "./ProjectConfigYaml";

export function ConfigEditor() {
    return (
        <div>
            <div className="relative z-10 mx-auto grid w-full max-w-7xl gap-8 p-8 text-left lg:grid-cols-2">
                <ContourOptions />
                <PostProcessingConfig />
            </div>
            <ProjectConfigYaml />
        </div>
    );
}
