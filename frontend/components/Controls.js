window.Components = window.Components || {};

const { SkipBack, SkipForward } = window.Icons;
const { renderFormula } = window.Utils;

window.Components.Controls = ({ currentStep, setCurrentStep, executionLog, autoPlay, setAutoPlay, currentStepData, codeLines }) => {
  return (
    <div className="bg-slate-800 rounded-xl shadow-2xl p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-700">
        <div className="flex gap-2">
          <button onClick={() => setCurrentStep(0)} disabled={currentStep === 0} className="px-3 py-1 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded text-sm">
            Reset
          </button>
          <button onClick={() => setAutoPlay(!autoPlay)} className={`px-3 py-1 rounded text-sm ${autoPlay ? 'bg-red-600 hover:bg-red-700 text-white' : 'bg-green-600 hover:bg-green-700 text-white'}`}>
            {autoPlay ? 'Pause' : 'Auto Play'}
          </button>
        </div>
        
        <div className="flex items-center gap-3">
          <button onClick={() => setCurrentStep(Math.max(0, currentStep - 1))} disabled={currentStep === 0} className="p-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded shadow-lg">
            <SkipBack />
          </button>
          
          <div className="text-center">
            <div className="text-xl font-bold text-white">{currentStep + 1} / {executionLog.length}</div>
            <div className="text-xs text-purple-300">Step</div>
          </div>
          
          <button onClick={() => setCurrentStep(Math.min(executionLog.length - 1, currentStep + 1))} disabled={currentStep === executionLog.length - 1} className="p-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded shadow-lg">
            <SkipForward />
          </button>
        </div>
        <div className="w-24"></div>
      </div>

      {currentStepData && (
        <div className="mb-4 bg-yellow-500/10 border-l-4 border-yellow-500 p-3 rounded">
          <div className="text-xs text-yellow-400 mb-1 font-semibold">
            {currentStepData.event === "line" && `Line ${currentStepData.lineno}`}
          </div>
          {currentStepData.code && <code className="text-sm font-mono text-white">{currentStepData.code}</code>}
        </div>
      )}

      <div className="bg-slate-900 rounded-lg p-3 font-mono text-xs overflow-x-auto">
        {codeLines.map((line, idx) => {
          const lineNo = idx + 1;
          const isCurrentLine = currentStepData && currentStepData.lineno === lineNo;
          const isExecuted = executionLog.some((step, stepIdx) => step.lineno === lineNo && stepIdx <= currentStep);
          
          return (
            <div key={idx} className={`px-2 py-1 transition-all ${isCurrentLine ? 'bg-yellow-500 text-slate-900 font-bold' : isExecuted ? 'bg-green-900/30 text-green-300' : 'text-slate-500'}`}>
              <span className="text-slate-600 mr-3 select-none inline-block w-6 text-right">{lineNo}</span>
              {line || ' '}
            </div>
          );
        })}
      </div>
    </div>
  );
};