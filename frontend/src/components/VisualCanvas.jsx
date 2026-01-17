import ArrayVisualization from "./ArrayVisualization";
import MatrixVisualization from "./MatrixVisualization";
import DictVisualization from "./DictVisualization";
import NeuralNetworkVisualization from "./NeuralNetworkVisualization";
import RecursionTree from "./RecursionTree";

import { detectType } from "../utils/detectType";
import { renderFormula } from "../utils/renderFormula";

export default function VisualCanvas({
  executionLog,
  currentStepData,
  locals,
  changedVars,
  nnModels,
  callTree,
  recursiveFuncs,
  currentStep,
}) {
  const renderValue = (value, name) => {
    const type = detectType(value);

    switch (type) {
      case "array":
        return <ArrayVisualization arr={value} name={name} />;

      case "ndarray":
        return <MatrixVisualization matrix={value} name={name} />;

      case "tensor_scalar": {
        const scalarValue = Array.isArray(value.values)
          ? value.values[0]
          : value.values;

        return (
          <div className="flex items-center gap-2">
            <span className="font-mono text-orange-400 text-xl font-bold">
              {scalarValue}
            </span>
            <span className="text-xs text-gray-500">torch.{value.dtype}</span>
          </div>
        );
      }

      case "tensor_1d":
        return (
          <div className="flex flex-col gap-2">
            <div className="text-xs text-gray-500">
              torch tensor: shape {value.shape.join("x")} | {value.dtype}
            </div>
            <ArrayVisualization arr={value.values} name={name} />
          </div>
        );

      case "tensor_2d":
        return (
          <div className="flex flex-col gap-2">
            <div className="text-xs text-gray-500">
              torch tensor: shape {value.shape.join("x")} | {value.dtype}
            </div>
            <MatrixVisualization
              matrix={{ type: "ndarray", values: value.values }}
              name={name}
            />
          </div>
        );

      case "tensor_nd":
        return (
          <div className="flex flex-col gap-2">
            <div className="text-xs text-yellow-400">
              torch tensor: shape {value.shape.join("x")} | {value.dtype}
            </div>
            <div className="rounded-md bg-neutral-700 p-3">
              {value.summary ? (
                <>
                  <div className="text-sm text-gray-300">
                    Size: {value.summary.size}
                  </div>
                  <div className="text-sm text-gray-300">
                    Min: {value.summary.min?.toFixed(4)}
                  </div>
                  <div className="text-sm text-gray-300">
                    Max: {value.summary.max?.toFixed(4)}
                  </div>
                  <div className="text-sm text-gray-300">
                    Mean: {value.summary.mean?.toFixed(4)}
                  </div>
                </>
              ) : (
                <div className="text-sm text-gray-400">
                  High-dimensional tensor
                </div>
              )}
            </div>
          </div>
        );

      case "matrix":
        return <MatrixVisualization matrix={value} name={name} />;

      case "dict":
        return <DictVisualization dict={value} />;

      case "string":
        return (
          <div className="font-mono text-green-400 text-lg">"{value}"</div>
        );

      case "number":
        return (
          <div className="font-mono text-orange-400 text-xl font-bold">
            {value}
          </div>
        );

      default:
        return (
          <div className="font-mono text-gray-500">{JSON.stringify(value)}</div>
        );
    }
  };

  return (
    <div className="h-full bg-neutral-800 border border-neutral-700 rounded-lg p-4 flex flex-col">
      <div className="mb-3 font-semibold text-gray-100">Visual Canvas</div>

      {executionLog.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-[400px] gap-2">
          <div className="text-5xl opacity-50">🎨</div>
          <div className="text-lg text-gray-500">
            Run your code to see visualizations
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <div className="flex flex-col gap-4 p-2">
            {/* Neural Networks */}
            {nnModels && nnModels.length > 0 && (
              <div className="flex flex-col gap-4">
                <div className="text-sm font-bold text-cyan-400">
                  Detected Neural Networks
                </div>

                {nnModels.map((model, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl border border-cyan-400 p-4 bg-neutral-900"
                  >
                    <NeuralNetworkVisualization model={model} />
                  </div>
                ))}
              </div>
            )}

            {/* Recursion Tree */}
            {callTree &&
              callTree.length > 1 &&
              recursiveFuncs &&
              recursiveFuncs.length > 0 && (
                <RecursionTree
                  callTree={callTree}
                  currentStep={currentStep}
                  executionLog={executionLog}
                />
              )}

            {/* Console Output */}
            {currentStepData?.stdout?.length > 0 && (
              <div className="rounded-xl border border-green-500 bg-neutral-900 p-4">
                <div className="mb-1 text-xs font-bold text-green-400">
                  Console Output
                </div>
                <div className="font-mono text-sm text-green-300 whitespace-pre-wrap">
                  {currentStepData.stdout.join("\n")}
                </div>
              </div>
            )}

            {/* Formula */}
            {currentStepData?.formula && (
              <div className="rounded-xl border border-indigo-500 p-4 bg-neutral-900">
                <div className="mb-1 text-xs font-bold text-indigo-400">
                  📐 Formula at Line {currentStepData.lineno}
                </div>
                <div className="rounded-md bg-neutral-800 p-4">
                  {renderFormula(currentStepData.formula)}
                </div>
              </div>
            )}

            {/* Local Variables */}
            {Object.keys(locals).length > 0 ? (
              Object.entries(locals).map(([name, value]) => (
                <div
                  key={name}
                  className="rounded-xl border p-4"
                  style={{
                    borderColor: changedVars.has(name) ? "#eab308" : "#475569",
                    backgroundColor: changedVars.has(name)
                      ? "rgba(234,179,8,0.15)"
                      : "rgba(30,41,59,0.8)",
                  }}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <span className="font-mono font-bold text-lg text-blue-400">
                      {name}
                    </span>

                    <span className="px-2 py-0.5 text-xs rounded bg-neutral-700 text-gray-200">
                      {detectType(value)}
                    </span>

                    {changedVars.has(name) && (
                      <span className="px-2 py-0.5 text-xs rounded bg-yellow-500 text-black font-semibold">
                        CHANGED
                      </span>
                    )}
                  </div>

                  {renderValue(value, name)}
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-gray-500">
                No variables defined yet
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
