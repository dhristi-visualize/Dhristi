// Import all components and utilities
const { ArrayVisualization } = window.Components;
const { MatrixVisualization } = window.Components;
const { DictVisualization } = window.Components;
const { CodeEditor } = window.Components;
const { VisualCanvas } = window.Components;
const { Controls } = window.Components;
const { detectType } = window.Utils;
const { renderFormula } = window.Utils;

const { useState, useEffect } = React;

const PythonVisualizer = () => {
  const [code, setCode] = useState(`import numpy as np\n\nlist1 = [1, 2, 3]\nx = np.array([[1.0, 2.0], [3.0, 4.0]])\npass`);
  const [executionLog, setExecutionLog] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);
  const [autoPlay, setAutoPlay] = useState(false);

  const currentStepData = executionLog[currentStep];
  const locals = (currentStepData && (currentStepData.after || currentStepData.before)) || {};

  useEffect(() => {
    if (autoPlay && currentStep < executionLog.length - 1) {
      const timer = setTimeout(() => setCurrentStep(prev => prev + 1), 1000);
      return () => clearTimeout(timer);
    } else if (autoPlay && currentStep === executionLog.length - 1) {
      setAutoPlay(false);
    }
  }, [autoPlay, currentStep, executionLog.length]);

  const changedVars = (() => {
    if (!currentStepData || currentStep === 0) return new Set();
    const prev = executionLog[currentStep - 1]?.after || executionLog[currentStep - 1]?.before || {};
    const curr = currentStepData?.after || currentStepData?.before || {};
    const changed = new Set();
    Object.keys(curr).forEach(key => {
      if (JSON.stringify(prev[key]) !== JSON.stringify(curr[key])) changed.add(key);
    });
    return changed;
  })();

  const runCode = async () => {
    setIsRunning(true);
    setError(null);
    setCurrentStep(0);
    setAutoPlay(false);
    
    try {
      const response = await fetch('http://127.0.0.1:5000/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });

      const data = await response.json();
      if (data.success) {
        setExecutionLog(data.steps);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to connect to backend. Make sure Flask server is running on port 5000.');
      console.error('Error:', err);
    }
    
    setIsRunning(false);
  };

  const codeLines = code.split('\n');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
      <div className="max-w-[1800px] mx-auto">
        <div className="text-center mb-6">
          <h1 className="text-4xl font-bold text-white mb-2">Python Execution Visualizer</h1>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mb-4">
          <CodeEditor 
            code={code}
            setCode={setCode}
            runCode={runCode}
            isRunning={isRunning}
            error={error}
          />
          
          <VisualCanvas
            executionLog={executionLog}
            currentStepData={currentStepData}
            locals={locals}
            changedVars={changedVars}
            detectType={detectType}
          />
        </div>

        {executionLog.length > 0 && (
          <Controls
            currentStep={currentStep}
            setCurrentStep={setCurrentStep}
            executionLog={executionLog}
            autoPlay={autoPlay}
            setAutoPlay={setAutoPlay}
            currentStepData={currentStepData}
            codeLines={codeLines}
          />
        )}
      </div>
    </div>
  );
};

ReactDOM.render(<PythonVisualizer />, document.getElementById('root'));