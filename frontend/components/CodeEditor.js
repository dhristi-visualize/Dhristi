window.Components = window.Components || {};

const { Play, AlertCircle } = window.Icons;

window.Components.CodeEditor = ({ code, setCode, runCode, isRunning, error }) => {
  return (
    <div className="xl:col-span-1 bg-slate-800 rounded-xl shadow-2xl p-4 border border-slate-700">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold text-white">Code Editor</h2>
        <div className="text-xs text-purple-300">Python 3 + NumPy</div>
      </div>
      <textarea
        value={code}
        onChange={(e) => setCode(e.target.value)}
        className="w-full h-96 font-mono text-sm p-3 bg-slate-900 text-green-400 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
        placeholder="Enter your Python code here..."
        spellCheck="false"
      />
      <button
        onClick={runCode}
        disabled={isRunning}
        className="mt-3 w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition shadow-lg"
      >
        <Play />
        {isRunning ? 'Executing...' : 'Run & Visualize'}
      </button>
      
      {error && (
        <div className="mt-3 bg-red-900/50 border border-red-500 text-red-200 p-3 rounded-lg flex items-start gap-2 text-xs">
          <AlertCircle />
          <div>
            <div className="font-semibold mb-1">Error:</div>
            <pre className="whitespace-pre-wrap font-mono">{error}</pre>
          </div>
        </div>
      )}
    </div>
  );
};