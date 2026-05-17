import { useEffect, useRef, useState } from "react";
import { Button } from "./Button";
import { Card } from "./Card";

type MenuPopupAction = {
    id: string;
    label: string;
    popupTitle: string;
    content: React.ReactNode;
};

type MenuPopupProps = {
    menuLabel: string;
    actions: MenuPopupAction[];
};

export function MenuPopup({ menuLabel, actions }: MenuPopupProps) {
    const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);
    const [selectedActionId, setSelectedActionId] = useState<string | null>(
        null
    );
    const [isPopupOpen, setIsPopupOpen] = useState<boolean>(false);
    const menuRef = useRef<HTMLDivElement>(null);

    const selectedAction =
        actions.find((action) => action.id === selectedActionId) ?? null;

    useEffect(() => {
        function handleDocumentClick(event: MouseEvent) {
            if (
                menuRef.current &&
                !menuRef.current.contains(event.target as Node)
            ) {
                setIsMenuOpen(false);
            }
        }

        document.addEventListener("mousedown", handleDocumentClick);
        return () => {
            document.removeEventListener("mousedown", handleDocumentClick);
        };
    }, []);

    useEffect(() => {
        function onKeyDown(event: KeyboardEvent) {
            if (event.key === "Escape") {
                setIsPopupOpen(false);
                setIsMenuOpen(false);
                setSelectedActionId(null);
            }
        }

        if (isPopupOpen || isMenuOpen) {
            document.addEventListener("keydown", onKeyDown);
        }

        return () => {
            document.removeEventListener("keydown", onKeyDown);
        };
    }, [isMenuOpen, isPopupOpen]);

    return (
        <>
            <div className="relative" ref={menuRef}>
                <Button
                    intent="secondary"
                    shape="rounded"
                    aria-haspopup="menu"
                    aria-expanded={isMenuOpen}
                    onClick={() => setIsMenuOpen((previous) => !previous)}
                >
                    {menuLabel}
                </Button>

                {isMenuOpen && (
                    <div
                        role="menu"
                        className="absolute right-0 z-20 mt-2 w-52 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg"
                    >
                        {actions.map((action) => (
                            <button
                                key={action.id}
                                type="button"
                                role="menuitem"
                                onClick={() => {
                                    setSelectedActionId(action.id);
                                    setIsPopupOpen(true);
                                    setIsMenuOpen(false);
                                }}
                                className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                            >
                                {action.label}
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {isPopupOpen && selectedAction && (
                <div
                    className="fixed inset-0 z-40 flex items-center justify-center bg-gray-900/30 p-4"
                    role="dialog"
                    aria-modal="true"
                    aria-label={selectedAction.popupTitle}
                    onClick={(event) => {
                        if (event.target === event.currentTarget) {
                            setIsPopupOpen(false);
                            setSelectedActionId(null);
                        }
                    }}
                >
                    <Card className="w-full max-w-2xl border border-gray-200 bg-white p-4 shadow-xl lg:p-6">
                        <div className="mb-4 flex items-center justify-between">
                            <h2 className="text-lg font-semibold text-gray-900">
                                {selectedAction.popupTitle}
                            </h2>
                            <Button
                                intent="ghost"
                                shape="compact"
                                onClick={() => {
                                    setIsPopupOpen(false);
                                    setSelectedActionId(null);
                                }}
                            >
                                Close
                            </Button>
                        </div>
                        {selectedAction.content}
                    </Card>
                </div>
            )}
        </>
    );
}
