/**
 * This file is the entry point for the React app, it sets up the root
 * element and renders the App component to the DOM.
 *
 * It is included in `src/index.html`.
 */

// Polyfill Node's `global` for libraries like plotly.js that reference it
if (typeof globalThis !== "undefined" && typeof global === "undefined") {
    (window as any).global = globalThis;
}

import { StrictMode } from "react";
import { createRoot, type Root } from "react-dom/client";
import { App } from "./App";

const elem = document.getElementById("root")!;
let root: Root;

if (import.meta.hot) {
    root = import.meta.hot.data.root ?? createRoot(elem);
    import.meta.hot.data.root = root;
} else {
    root = createRoot(elem);
}

root.render(
    <StrictMode>
        <App />
    </StrictMode>
);
