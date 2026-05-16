import { ContourOptions } from "./ConfigForms/ContourOptions";
import { PostProcessingConfig } from "./ConfigForms/PostProcessingConfig";
import { ColorMapConfigEditor } from "./ColorMapConfigEditor";

export function ConfigEditor() {
    return (
        <div>
            <div className="relative z-10 mx-auto w-full max-w-7xl p-8 text-left">
                <ColorMapConfigEditor />
            </div>
            <div className="relative z-10 mx-auto grid w-full max-w-7xl gap-8 p-8 text-left lg:grid-cols-2">
                <ContourOptions />
                <PostProcessingConfig />
            </div>
        </div>
    );
}
