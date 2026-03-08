import { useEffect, useMemo, useState } from "react";
import { Group, Panel, Separator } from 'react-resizable-panels';
import CodeEditor from "./components/CodeEditor";
import Controls from "./components/Controls";
import VisualCanvas from "./components/VisualCanvas";

export default function App() {
  const [code, setCode] = useState(
    `import numpy as np\n\nlist1 = [1, 2, 3]\nx = np.array([[1.0, 2.0], [3.0, 4.0]])\npass`
  );

  const [executionLog, setExecutionLog] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [autoPlay, setAutoPlay] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);
  const [nnModels, setNnModels] = useState([]);
  const [callTree, setCallTree] = useState([]);
  const [recursiveFuncs, setRecursiveFuncs] = useState([]);
  const [language] = useState("python");
  const [fullView, setFullView] = useState(false);


  // // Reset full view as soon as user starts stepping
  // useEffect(() => {
  //   if (currentStep > 0) setFullView(false);
  // }, [currentStep]);

  const currentStepData = executionLog[currentStep] || null;

   const visibleCallTree = callTree.filter(
    (c) => (c.step_index ?? 0) <= currentStep
  );

  const locals = useMemo(() => {
    return currentStepData?.after || currentStepData?.before || {};
  }, [currentStepData]);

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

  const codeLines = useMemo(() => code.split("\n"), [code]);
  const [playSpeed, setPlaySpeed] = useState(".3");

  useEffect(() => {
    if (!autoPlay) return;

    if (currentStep < executionLog.length - 1) {
      const timer = setTimeout(() => {
        setCurrentStep((s) => s + 1);
      }, playSpeed * 1000);
      return () => clearTimeout(timer);
    } else {
      setAutoPlay(false);
    }
  }, [autoPlay, currentStep, executionLog.length, playSpeed]);

  const runCode = async () => {
    setIsRunning(true);
    setError(null);
    setExecutionLog([]);
    setCurrentStep(0);
    setAutoPlay(false);
    setFullView(false);

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

  return (
    <div className="h-screen w-screen bg-neutral-900 flex flex-col overflow-hidden">
      {/* HEADER */}
      <div className="flex h-14 items-center justify-between border-b border-neutral-800 px-4 shrink-0">
        <div className="flex items-center gap-3">
          <img
            src="/dhristilogo.png"
            alt="Dhristi logo"
            className="h-[84px] w-[84px] object-contain"
          />
          <div className="flex h-[84px] items-center">
            <span className="text-base font-semibold text-gray-100">
              Visualise Code
            </span>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT - RESIZABLE AREA */}
      <div className="flex-1 p-2 min-h-0">
        {/* Changed 'PanelGroup' to 'Group' and 'direction' to 'orientation' */}
        <Group orientation="horizontal">
          
          {/* CODE EDITOR PANEL */}
          <Panel defaultSize={60} minSize={30}>
            <div className="h-full rounded-lg border border-neutral-800 bg-neutral-800 overflow-hidden">
              <CodeEditor
                code={code}
                setCode={setCode}
                runCode={runCode}
                isRunning={isRunning}
                error={error}
                executionLog={executionLog}
                currentStep={currentStep}
                currentStepData={currentStepData}
                language={language}
              />
            </div>
          </Panel>

          {/* RESIZE HANDLE - Changed 'PanelResizeHandle' to 'Separator' */}
          <Separator className="w-2 transition-all duration-200 hover:bg-blue-600/30 flex items-center justify-center cursor-col-resize">
            <div className="w-[1px] h-full bg-neutral-700" />
          </Separator>

          {/* VISUAL CANVAS PANEL */}
          <Panel defaultSize={40} minSize={20}>
            <div className="h-full rounded-lg border border-neutral-800 bg-neutral-800 overflow-auto">
              <VisualCanvas
                fullView={fullView}
                setFullView={setFullView}
                executionLog={executionLog}
                currentStep={currentStep}
                currentStepData={currentStepData}
                locals={locals}
                changedVars={changedVars}
                nnModels={nnModels}
                callTree={visibleCallTree}
                recursiveFuncs={recursiveFuncs}
              />
            </div>
          </Panel>

        </Group>
      </div>

      {/* CONTROLS / TIMELINE */}
      <div className="shrink-0">
        <div className="h-px bg-neutral-700" />
        <div className="h-16 px-4">
          <Controls
            currentStep={currentStep}
            setCurrentStep={setCurrentStep}
            executionLog={executionLog}
            setExecutionLog={setExecutionLog}
            autoPlay={autoPlay}
            setAutoPlay={setAutoPlay}
            currentStepData={currentStepData}
            codeLines={codeLines}
            playSpeed={playSpeed}
            setPlaySpeed={setPlaySpeed}
          />
        </div>
      </div>
    </div>
  );
}