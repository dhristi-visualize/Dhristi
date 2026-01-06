// export default function RecursionTree({
//   callTree,
//   currentStep,
//   executionLog,
// }) {
//   if (!callTree || callTree.length === 0) {
//     return null;
//   }

//   return (
//     <div className="bg-slate-800 border-2 border-purple-500 rounded-xl p-4 mb-6">
//       <div className="text-sm font-bold text-purple-400 mb-4">
//         Recursion Tree
//       </div>

//       <div className="space-y-2 font-mono text-sm">
//         {callTree.map((node, idx) => {
//           if (!node.func || node.func === "<module>") return null;
//           const isActive =
//             idx === currentStep &&
//             executionLog[currentStep]?.event === "call";

//           const isReturned =
//             idx < currentStep &&
//             executionLog[idx]?.event === "return";

//           return (
//             <div
//               key={idx}
//               className={`flex items-center gap-2 px-3 py-1 rounded transition-all ${
//                 isActive
//                   ? "bg-purple-600 text-white font-bold"
//                   : isReturned
//                   ? "bg-slate-700 text-slate-300"
//                   : "text-slate-400"
//               }`}
//               style={{
//                 marginLeft: `${node.depth * 16}px`,
//               }}
//             >
//               <span className="text-purple-400">↳</span>
//               <span>{node.func}</span>
//               <span className="text-xs text-slate-400">
//                   (
//                   {Array.isArray(node.args)
//                     ? node.args.join(", ")
//                     : node.args && typeof node.args === "object"
//                     ? Object.values(node.args).join(", ")
//                     : ""}
//                   )
//                 </span>
//             </div>
//           );
//         })}
//       </div>
//     </div>
//   );
// }


import React from "react";

export default function RecursionTree({ callTree, currentStep, executionLog }) {
  if (!callTree || callTree.length === 0) return null;

  // -------- ACTIVE CALL (optional highlighting) --------
  const activeCallIds = new Set();
  if (executionLog && currentStep < executionLog.length) {
    const step = executionLog[currentStep];
    if (step?.call_id !== undefined) {
      activeCallIds.add(step.call_id);
    }
  }

  // -------- ROOT CALLS --------
  const moduleCall = callTree.find(c => c.func === "<module>");

  const rootCalls = moduleCall
    ? callTree.filter(c => c.parent_id === moduleCall.call_id)
    : callTree.filter(c => c.parent_id === null);

  // -------- RECURSIVE RENDER --------
  const renderCall = (call) => {
    const children = callTree.filter(c => c.parent_id === call.call_id);
    const isActive = activeCallIds.has(call.call_id);

    return (
      <div key={call.call_id} className="flex flex-col items-center">
        {/* NODE */}
        <div
          className={`
            px-4 py-3 rounded-lg border-2 font-mono text-sm
            ${isActive
              ? "bg-yellow-900/40 border-yellow-400 text-yellow-200"
              : "bg-slate-900 border-purple-500 text-purple-300"}
          `}
        >
          <div>
            {call.func}(
            {Object.entries(call.args || {})
              .map(([k, v]) => `${k}=${v}`)
              .join(", ")}
            )
          </div>

          {call.return_value !== null && (
            <div className="text-xs mt-1 opacity-70">
              → returns {String(call.return_value)}
            </div>
          )}
        </div>

        {/* VERTICAL CONNECTOR */}
        {children.length > 0 && (
          <div className="h-6 w-px bg-purple-400" />
        )}

        {/* CHILDREN */}
        {children.length > 0 && (
          <>
            {/* vertical down from parent */}
            <div className="h-6 w-px bg-purple-400" />

            {/* horizontal fork */}
            <div className="relative w-full flex justify-center">
              <div className="absolute top-0 left-0 right-0 h-px bg-purple-400" />
            </div>

            {/* children */}
            <div className="flex gap-8 mt-4">
              {children.map(child => (
                <div key={child.call_id} className="flex flex-col items-center">
                  {/* vertical up into child */}
                  <div className="h-4 w-px bg-purple-400" />
                  {renderCall(child)}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    );
  };

  // -------- RENDER --------
  return (
    <div className="bg-slate-800 border-2 border-purple-500 rounded-xl p-6 mb-6">
      <div className="text-purple-400 font-semibold mb-4">
        Recursion Tree
      </div>

      <div className="overflow-x-auto flex justify-center">
        {rootCalls.map(renderCall)}
      </div>
    </div>
  );
}
