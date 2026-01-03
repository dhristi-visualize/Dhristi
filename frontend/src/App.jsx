import { useEffect, useMemo, useState } from "react";

import CodeEditor from "./components/CodeEditor";
import Controls from "./components/Controls";
import VisualCanvas from "./components/VisualCanvas";

export default function App() {
  /* -------------------------------
     Core State
  -------------------------------- */

  const [code, setCode] = useState(`import numpy as np\n\nlist1 = [1, 2, 3]\nx = np.array([[1.0, 2.0], [3.0, 4.0]])\npass`);

  const [executionLog, setExecutionLog] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [autoPlay, setAutoPlay] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);
  const [nnModels, setNnModels] = useState([]);
  const [callTree, setCallTree] = useState([]);
  const [recursiveFuncs, setRecursiveFuncs] = useState([]);

  /* -------------------------------
     Derived State
  -------------------------------- */

  const currentStepData = executionLog[currentStep] || null;

const locals =
  currentStepData?.after ||
  currentStepData?.before ||
  {};


  const changedVars = useMemo(() => {
    if (currentStep === 0 || !executionLog[currentStep - 1]) {
      return new Set();
    }

    const prev =
      executionLog[currentStep - 1]?.after ||
      executionLog[currentStep - 1]?.before ||
      {};

    const curr = locals;

    const changed = new Set();

    Object.keys(curr).forEach((key) => {
      if (JSON.stringify(prev[key]) !== JSON.stringify(curr[key])) {
        changed.add(key);
      }
    });

    return changed;
  }, [currentStep, executionLog, locals]);

  // const nnModels = useMemo(() => {
  //   return executionLog
  //     .flatMap((step) => step.nn_models || [])
  //     .filter(Boolean);
  // }, [executionLog]);

  // const callTree = useMemo(() => {
  //   return executionLog.filter(
  //     (step) => step.event === "call" || step.event === "return"
  //   );
  // }, [executionLog]);

  // const recursiveFuncs = useMemo(() => {
  //   const counts = {};
  //   callTree.forEach((node) => {
  //     counts[node.func] = (counts[node.func] || 0) + 1;
  //   });
  //   return Object.keys(counts).filter((k) => counts[k] > 1);
  // }, [callTree]);

  const codeLines = useMemo(() => code.split("\n"), [code]);

  /* -------------------------------
     Auto Play
  -------------------------------- */

  useEffect(() => {
    if (!autoPlay) return;

    if (currentStep < executionLog.length - 1) {
      const timer = setTimeout(() => {
        setCurrentStep((s) => s + 1);
      }, 700);
      return () => clearTimeout(timer);
    } else {
      setAutoPlay(false);
    }
  }, [autoPlay, currentStep, executionLog.length]);

  /* -------------------------------
     Run Code
  -------------------------------- */

  const runCode = async () => {
    setIsRunning(true);
    setError(null);
    setExecutionLog([]);
    setCurrentStep(0);
    setAutoPlay(false);

    try {
      const res = await fetch("http://127.0.0.1:5000/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Execution failed");
      }

      if (data.success) {
        setExecutionLog(data.steps || []);
        setNnModels(data.nn_models || []);
        setCallTree(data.call_tree || []);
        setRecursiveFuncs(data.recursive_funcs || []);
      } else {
        throw new Error(data.error || "Execution failed");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsRunning(false);
    }
  };

  /* -------------------------------
     Render
  -------------------------------- */

  return (
  <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
    <div className="max-w-[1800px] mx-auto">
      
      <div className="text-center mb-6">
        <h1 className="text-4xl font-bold text-white mb-2">
          Python Execution Visualizer
        </h1>
      </div>

      {/* TOP: Editor + Visual Canvas */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mb-4">
        <div className="xl:col-span-2">
          <CodeEditor
            code={code}
            setCode={setCode}
            runCode={runCode}
            isRunning={isRunning}
            error={error}
          />
        </div>

        <VisualCanvas
          executionLog={executionLog}
          currentStep={currentStep}
          currentStepData={currentStepData}
          locals={locals}
          changedVars={changedVars}
          nnModels={nnModels}
          callTree={callTree}
          recursiveFuncs={recursiveFuncs}
        />
      </div>

      {/* BOTTOM: Controls */}
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

}
