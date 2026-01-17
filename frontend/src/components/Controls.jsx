import { SkipBack, SkipForward } from "./icons";

export default function Controls({
  currentStep,
  setCurrentStep,
  executionLog,
  setExecutionLog,
  setCurrentStepData,
  autoPlay,
  setAutoPlay,
  currentStepData,
}) {
  return (
    <div className="flex items-center justify-between w-full h-full">
      {/* LEFT */}
      <div className="flex gap-2">
        <button
          disabled={currentStep === 0}
          onClick={() => {
            setExecutionLog([]);
            setCurrentStep(0);
            setCurrentStepData(null);
            setAutoPlay(false);
          }}
          className="px-3 py-1.5 text-sm rounded-md bg-neutral-700 hover:bg-neutral-600 disabled:opacity-50 disabled:cursor-not-allowed text-white"
        >
          Reset
        </button>

        <button
          onClick={() => setAutoPlay(!autoPlay)}
          className={`px-3 py-1.5 text-sm rounded-md text-white ${
            autoPlay
              ? "bg-red-600 hover:bg-red-500"
              : "bg-neutral-700 hover:bg-neutral-600"
          }`}
        >
          {autoPlay ? "Pause" : "Auto Play"}
        </button>
      </div>

      {/* CENTER */}
      <div className="flex items-center gap-4">
        <button
          disabled={currentStep === 0}
          onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
          className="p-2 rounded-md bg-neutral-700 hover:bg-neutral-600 disabled:opacity-50 disabled:cursor-not-allowed text-white"
        >
          <SkipBack />
        </button>

        <span className="font-semibold text-gray-100">
          {currentStep + 1} / {executionLog.length}
        </span>

        <button
          disabled={currentStep === executionLog.length - 1}
          onClick={() =>
            setCurrentStep(Math.min(executionLog.length - 1, currentStep + 1))
          }
          className="p-2 rounded-md bg-neutral-700 hover:bg-neutral-600 disabled:opacity-50 disabled:cursor-not-allowed text-white"
        >
          <SkipForward />
        </button>
      </div>

      {/* RIGHT */}
      <div className="text-xs text-gray-500 whitespace-nowrap">
        {currentStepData?.event === "call" && `CALL ${currentStepData.func}()`}

        {currentStepData?.event === "return" &&
          `RETURN ${currentStepData.func}()`}

        {currentStepData?.event === "line" && `Line ${currentStepData.lineno}`}
      </div>
    </div>
  );
}
