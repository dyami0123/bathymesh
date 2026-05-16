import { useState, useRef, useEffect } from "react";

export function DropdownExample() {
    const [open, setOpen] = useState(false);
    const dropdownRef = useRef();

    // Close when clicking outside
    useEffect(() => {
        function handleClickOutside(e) {
            if (
                dropdownRef.current &&
                !dropdownRef.current.contains(e.target)
            ) {
                setOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () =>
            document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const items = [
        { label: "Profile", content: "User profile info." },
        { label: "Settings", content: "Account settings panel." },
        { label: "Logout", content: "Confirm logout action." },
    ];

    const [selected, setSelected] = useState(items[0]);

    return (
        <div className="relative w-64 mx-auto" ref={dropdownRef}>
            {/* Trigger */}
            <button
                onClick={() => setOpen(!open)}
                className="w-full px-4 py-2 border rounded bg-white text-left"
            >
                {selected.label}
            </button>

            {/* Dropdown menu */}
            {open && (
                <div className="absolute mt-1 w-full border rounded bg-white shadow">
                    {items.map((item) => (
                        <div
                            key={item.label}
                            onClick={() => {
                                setSelected(item);
                                setOpen(false);
                            }}
                            className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
                        >
                            {item.label}
                        </div>
                    ))}
                </div>
            )}

            {/* Content display */}
            <div className="mt-4 p-4 border rounded bg-gray-50">
                {selected.content}
            </div>
        </div>
    );
}
