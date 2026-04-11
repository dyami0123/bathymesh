import "./index.css";

import logo from "./logo.svg";
import reactLogo from "./react.svg";
import { ShowConfig } from "./components/ShowConfig";

export function App() {
  return (
    <div className="max-w-7xl mx-auto p-8 text-center relative z-10">
      <ShowConfig />
    </div>
  );
}

export default App;
