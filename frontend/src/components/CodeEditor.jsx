import { useEffect, useRef } from "react";
import { Play } from "./icons";
import Editor from "@monaco-editor/react";


export default function CodeEditor({
  code,
  setCode,
  runCode,
  isRunning,
  error,
  executionLog,
  currentStep,
  currentStepData,
  language,
}) {
  const codeLines = code.split("\n");
  const lineRefs = useRef({});

  const isExecutionMode = executionLog.length > 0;

  // Auto-scroll to current line
 useEffect(() => {
   if (!isExecutionMode) return;

   if (currentStepData?.lineno && lineRefs.current[currentStepData.lineno]) {
     lineRefs.current[currentStepData.lineno].scrollIntoView({
       block: "center",
       behavior: "smooth",
     });
   }
 }, [currentStepData, isExecutionMode]);


  return (
    <div className="h-full rounded-md bg-neutral-800 p-4 flex flex-col">
      {/* HEADER */}
      <div className="mb-2 flex items-center justify-between">
        {/* Left: title */}
        <div>
          <div className="font-semibold text-gray-100">Code Editor</div>
          <div className="text-xs text-gray-500">Execution-aware</div>
        </div>

        {/* Right: language selector */}
        <div className="relative">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="
              appearance-none
              bg-neutral-900
              border border-neutral-700
              text-gray-100
              text-sm
              rounded-md
              pl-3 pr-8 py-1.5
              hover:border-neutral-500
              focus:outline-none
              focus:ring-1 focus:ring-blue-500
              cursor-pointer
            "
          >
            <option value="python">Python</option>
            <option value="java">Java</option>
            <option value="cpp">C++</option>
            <option value="javascript">JavaScript</option>
          </select>

          {/* dropdown arrow */}
          <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 text-xs">
            ▼
          </span>
        </div>
      </div>


      {/* CODE VIEW */}
      <div className="flex-1 rounded-lg border border-neutral-700 bg-neutral-900 overflow-y-auto">
        {isExecutionMode ? (
          <div className="px-2">
            {codeLines.map((line, idx) => {
              const lineNo = idx + 1;

              const isCurrent =
                currentStepData?.event === "line" &&
                currentStepData.lineno === lineNo;

              const isExecuted = executionLog.some(
                (step, stepIdx) =>
                  step.lineno === lineNo && stepIdx <= currentStep
              );

              return (
                <div
                  key={idx}
                  ref={(el) => (lineRefs.current[lineNo] = el)}
                  className="px-2 py-[2px] rounded text-[13px] font-mono"
                  style={{
                    backgroundColor: isCurrent
                      ? "#facc15"
                      : isExecuted
                      ? "rgba(34,197,94,0.15)"
                      : "transparent",
                    color: isCurrent
                      ? "#000"
                      : isExecuted
                      ? "#86efac"
                      : "#6b7280",
                  }}
                >
                  <span className="inline-block w-8 text-right mr-3 select-none text-neutral-500">
                    {lineNo}
                  </span>
                  {line || " "}
                </div>
              );
            })}
          </div>
        ) : (
            <Editor
              height="100%"
              language={language}
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value ?? "")}
              options={{
                fontSize: 13,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                automaticLayout: true,
              }}
            />

        )}
      </div>

      {/* RUN BUTTON */}
      <div className="mt-2">
        <button
          onClick={runCode}
          disabled={isRunning}
          className="w-full flex items-center justify-center gap-2 rounded-md bg-neutral-700 hover:bg-neutral-600 disabled:opacity-50 disabled:cursor-not-allowed py-2 text-white"
        >
          <Play />
          {isRunning ? "Executing..." : "Run & Visualize"}
        </button>
      </div>

      {/* ERROR */}
      {error && (
        <div className="mt-2 rounded-md border border-red-500/60 bg-red-500/10 p-3">
          <div className="text-xs font-semibold text-red-400">Error</div>
          <div className="text-xs font-mono text-red-300">{error}</div>
        </div>
      )}
    </div>
  );
}
