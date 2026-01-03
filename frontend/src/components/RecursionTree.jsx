export default function RecursionTree({
  callTree,
  currentStep,
  executionLog,
}) {
  if (!callTree || callTree.length === 0) {
    return null;
  }

  return (
    <div className="bg-slate-800 border-2 border-purple-500 rounded-xl p-4 mb-6">
      <div className="text-sm font-bold text-purple-400 mb-4">
        Recursion Tree
      </div>

      <div className="space-y-2 font-mono text-sm">
        {callTree.map((node, idx) => {
          const isActive =
            idx === currentStep &&
            executionLog[currentStep]?.event === "call";

          const isReturned =
            idx < currentStep &&
            executionLog[idx]?.event === "return";

          return (
            <div
              key={idx}
              className={`flex items-center gap-2 px-3 py-1 rounded transition-all ${
                isActive
                  ? "bg-purple-600 text-white font-bold"
                  : isReturned
                  ? "bg-slate-700 text-slate-300"
                  : "text-slate-400"
              }`}
              style={{
                marginLeft: `${node.depth * 16}px`,
              }}
            >
              <span className="text-purple-400">↳</span>
              <span>{node.func}</span>
              <span className="text-xs text-slate-400">
                ({node.args?.join(", ")})
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
