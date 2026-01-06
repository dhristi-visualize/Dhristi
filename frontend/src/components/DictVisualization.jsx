export default function DictVisualization({ dict }) {
  return (
    <div className="space-y-2">
      {Object.entries(dict).map(([key, value], idx) => (
        <div
          key={idx}
          className="flex items-center gap-3 bg-purple-900/30 p-3 rounded-lg border border-purple-500/50"
        >
          <div className="bg-purple-600 text-white px-3 py-1 rounded font-mono text-sm font-bold">
            {key}
          </div>
          <div className="text-purple-300">→</div>
          <div className="bg-purple-800/50 text-purple-200 px-3 py-1 rounded font-mono text-sm flex-1">
            {JSON.stringify(value)}
          </div>
        </div>
      ))}
    </div>
  );
}
