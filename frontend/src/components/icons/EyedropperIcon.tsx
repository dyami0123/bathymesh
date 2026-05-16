type EyedropperIconProps = {
    className?: string;
};

export function EyedropperIcon({ className }: EyedropperIconProps) {
    return (
        <svg
            viewBox="0 0 24 24"
            className={className}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            <path d="M15.586 3.586a2 2 0 0 1 2.828 0l2 2a2 2 0 0 1 0 2.828l-8.793 8.793a4 4 0 0 1-1.414.943l-2.262.904a.5.5 0 0 1-.65-.65l.904-2.262a4 4 0 0 1 .943-1.414z" />
            <path d="m13.5 5.5 5 5" />
        </svg>
    );
}
