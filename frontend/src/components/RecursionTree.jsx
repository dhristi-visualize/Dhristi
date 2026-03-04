import React from "react";

export default function RecursionTree({ callTree, currentStep, executionLog }) {
  if (!callTree || callTree.length === 0) {
    return null;
  }

  // CRITICAL: Only show calls that have been ENCOUNTERED by currentStep
  const visibleCallTree = callTree.filter(
    (c) => (c.step_index ?? 0) <= currentStep,
  );

  console.log(
    "visibleCallTree:",
    visibleCallTree.map((c) => ({
      func: c.func,
      call_id: c.call_id,
      step_index: c.step_index,
      return_step: c.return_step,
      parent_id: c.parent_id,
    })),
  );

  // Get currently active call
  const activeCallIds = new Set();
  if (executionLog && currentStep < executionLog.length) {
    const step = executionLog[currentStep];
    if (step?.call_id !== undefined) {
      activeCallIds.add(step.call_id);
    }
  }

  // Find root calls (skip <module> as it's always there)
  // const moduleCall = visibleCallTree.find(c => c.func === "<module>");
  // const rootCalls = moduleCall
  //   ? visibleCallTree.filter(c => c.parent_id === moduleCall.call_id)
  //   : visibleCallTree.filter(c => c.parent_id === null);
  const rootCalls = visibleCallTree.filter((c) => c.parent_id === 0);

  // console.log("moduleCall:", moduleCall);

  // Recursive render function
  const renderCall = (call) => {
    // Only show children that are in visibleCallTree
    const children = visibleCallTree.filter(
      (c) => c.parent_id === call.call_id,
    );

    const isActive = activeCallIds.has(call.call_id);

    // Check if this call has returned (and the return event has been reached)
    const hasReturned =
      call.return_step !== undefined && call.return_step <= currentStep;

    return (
      <div key={call.call_id} className="flex flex-col items-center">
        {/* CALL NODE */}
        <div
          className={`
            px-4 py-3 rounded-lg border-2 font-mono text-sm min-w-[180px]
            transition-all duration-300
            ${
              isActive
                ? "bg-yellow-500 border-yellow-600 text-gray-900 font-bold shadow-lg scale-105"
                : hasReturned
                  ? "bg-green-900/60 border-green-500 text-green-200"
                  : "bg-slate-900 border-purple-500 text-purple-300"
            }
          `}
        >
          <div className="font-semibold">
            {call.func}(
            {Object.entries(call.args || {})
              .map(([k, v]) => {
                const displayValue =
                  typeof v === "object" ? JSON.stringify(v) : v;
                return `${k}=${displayValue}`;
              })
              .join(", ")}
            )
          </div>

          {/* Show return value ONLY after it has returned */}
          {hasReturned &&
            call.return_value !== undefined &&
            call.return_value !== null && (
              <div className="text-xs mt-2 pt-2 border-t border-green-500/30 font-semibold">
                → returns {String(call.return_value)}
              </div>
            )}

          {/* Show computing indicator for active calls */}
          {isActive && !hasReturned && (
            <div className="text-xs mt-2 pt-2 border-t border-yellow-500/30 italic animate-pulse">
              computing...
            </div>
          )}
        </div>

        {/* CONNECTORS AND CHILDREN */}
        {children.length > 0 && (
          <>
            {/* Vertical line down */}
            <div className="h-8 w-0.5 bg-purple-400" />

            {children.length === 1 ? (
              // Single child - direct vertical connection
              renderCall(children[0])
            ) : (
              // Multiple children - branching
              <>
                {/* Horizontal branching line */}
                <div
                  className="relative"
                  style={{ width: `${children.length * 200}px`, height: "1px" }}
                >
                  <div className="absolute top-0 left-0 right-0 h-0.5 bg-purple-400" />
                </div>

                {/* Child nodes */}
                <div className="flex gap-12 mt-0">
                  {children.map((child) => (
                    <div
                      key={child.call_id}
                      className="flex flex-col items-center"
                    >
                      {/* Vertical line up to child */}
                      <div className="h-8 w-0.5 bg-purple-400" />
                      {renderCall(child)}
                    </div>
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>
    );
  };

  // Don't show anything if no recursive calls yet
  if (rootCalls.length === 0) {
    console.log("No root calls yet - returning null");
    return null;
  }

  return (
    <div className="bg-slate-800 border-2 border-purple-500 rounded-xl p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="text-purple-400 font-semibold text-lg">
          Recursion Tree
        </div>
        <div className="text-sm text-gray-400">
          Showing calls up to step {currentStep + 1} / {executionLog.length}
        </div>
      </div>

      <div className="overflow-x-auto pb-4">
        <div className="flex justify-center min-w-max px-4">
          <div className="flex gap-8">
            {rootCalls.map((call) => renderCall(call))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-slate-700 flex gap-6 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-yellow-500 border-2 border-yellow-600 rounded"></div>
          <span className="text-gray-400">Currently executing</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-900/60 border-2 border-green-500 rounded"></div>
          <span className="text-gray-400">Returned</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-slate-900 border-2 border-purple-500 rounded"></div>
          <span className="text-gray-400">Called (computing)</span>
        </div>
      </div>
    </div>
  );
}
