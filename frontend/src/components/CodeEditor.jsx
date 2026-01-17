import { useEffect, useRef } from "react";
import { Play } from "./icons";

export default function CodeEditor({
  code,
  setCode,
  runCode,
  isRunning,
  error,
  executionLog,
  currentStep,
  currentStepData,
}) {
  const codeLines = code.split("\n");
  const lineRefs = useRef({});

  const isExecutionMode = executionLog.length > 0;

  // Auto-scroll to current line
  useEffect(() => {
    if (currentStepData?.lineno && lineRefs.current[currentStepData.lineno]) {
      lineRefs.current[currentStepData.lineno].scrollIntoView({
        block: "center",
        behavior: "smooth",
      });
    }
  }, [currentStepData]);

  return (
    <div className="h-full rounded-md bg-neutral-800 p-4 flex flex-col">
      {/* HEADER */}
      <div className="mb-2">
        <div className="font-semibold text-gray-100">Code Editor</div>
        <div className="text-xs text-gray-500">Python 3 • Execution-aware</div>
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
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            spellCheck={false}
            className="h-full w-full resize-none bg-transparent border-none outline-none p-3 font-mono text-[13px] text-green-400"
            placeholder="Enter your Python code here..."
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
