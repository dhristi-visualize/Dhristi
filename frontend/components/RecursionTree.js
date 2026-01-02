window.Components = window.Components || {};

window.Components.RecursionTree = ({ callTree, currentStep, executionLog }) => {
  if (!callTree || callTree.length === 0) return null;

  // Find which calls are active at current step
  const activeCallIds = new Set();
  if (executionLog && currentStep < executionLog.length) {
    const currentStepData = executionLog[currentStep];
    if (currentStepData && currentStepData.call_id !== undefined) {
      activeCallIds.add(currentStepData.call_id);
    }
  }

  // Build tree structure
  const rootCalls = callTree.filter(c => c.parent_id === null);
  
  const renderCall = (call) => {
    const children = callTree.filter(c => c.parent_id === call.call_id);

    return (
        <div className="flex flex-col items-center">
        {/* NODE */}
        <div className="px-4 py-3 rounded-lg border-2 bg-green-900/30 border-green-500 text-green-300 font-mono text-sm">
            <div>
            {call.func}(
            {Object.entries(call.args)
                .map(([k, v]) => `${k}=${v}`)
                .join(", ")}
            )
            </div>
            {call.return_value !== null && (
            <div className="text-xs mt-1 opacity-75">
                → returns {call.return_value}
            </div>
            )}
        </div>

        {/* Vertical connector */}
        {children.length > 0 && (
            <div className="h-6 w-px bg-cyan-400" />
        )}

        {/* CHILDREN (HORIZONTAL) */}
        {children.length > 0 && (
            <div className="flex gap-8 mt-2">
            {children.map(child => renderCall(child))}
            </div>
        )}
        </div>
    );
    };


  return (
    <div className="bg-slate-900 border-2 border-cyan-500 rounded-xl p-6">
      <div className="text-cyan-400 font-semibold mb-4 flex items-center gap-2">
        <span className="text-2xl"></span>
        <span>Recursive Call Tree</span>
      </div>
      <div className="overflow-x-auto">
        {rootCalls.map(call => renderCall(call))}
      </div>
    </div>
  );
};