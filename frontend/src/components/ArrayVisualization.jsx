export default function ArrayVisualization({ arr }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs text-gray-500">indices:</span>
        {arr.slice(0, 20).map((_, idx) => (
          <div
            key={idx}
            className="w-12 text-center text-xs text-gray-400"
          >
            {idx}
          </div>
        ))}
        {arr.length > 20 && (
          <span className="text-xs text-gray-500">...</span>
        )}
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        {arr.slice(0, 20).map((item, idx) => (
          <div key={idx} className="relative group">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 border-2 border-blue-700 rounded flex items-center justify-center text-white font-bold shadow-lg transform transition-transform hover:scale-110">
              {typeof item === "number"
                ? item.toFixed(1)
                : JSON.stringify(item)}
            </div>
            <div className="absolute -bottom-6 left-0 right-0 text-center text-xs text-blue-300 opacity-0 group-hover:opacity-100 transition-opacity">
              [{idx}]
            </div>
          </div>
        ))}
        {arr.length > 20 && (
          <div className="text-gray-400 text-sm">
            ... +{arr.length - 20} more
          </div>
        )}
      </div>
    </div>
  );
}
