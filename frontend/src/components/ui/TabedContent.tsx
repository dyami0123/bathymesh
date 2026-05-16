import { useState } from "react";

type TabContent = {
    id: string;
    label: string;
    content: React.ReactNode;
};

export function TabbedContent({ tabs }: { tabs: TabContent[] }) {
    const [activeTab, setActiveTab] = useState(tabs[0]?.id);

    return (
        <div className="w-full mx-auto p-4">
            {/* Tab buttons */}
            <div className="flex border-b mb-4">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-4 py-2 -mb-px border-b-2 transition text-zinc-500 ${
                            activeTab === tab.id
                                ? "border-blue-500 font-semibold "
                                : "border-transparent "
                        }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab content */}
            <div className="w-full p-4 border rounded bg-zinc-50">
                {tabs.find((tab) => tab.id === activeTab)?.content}
            </div>
        </div>
    );
}
