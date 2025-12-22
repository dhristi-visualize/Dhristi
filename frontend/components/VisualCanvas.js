window.Components = window.Components || {};

window.Components.VisualCanvas = ({ executionLog, currentStepData, locals, changedVars, detectType }) => {
  const { ArrayVisualization, MatrixVisualization, DictVisualization } = window.Components;
  const { renderFormula } = window.Utils;

  const renderValue = (value, name) => {
    const type = detectType(value);
    switch (type) {
      case 'array': return <ArrayVisualization arr={value} name={name} />;
      case 'ndarray': return <MatrixVisualization matrix={value} name={name} />;
      case 'tensor_scalar':
        // Scalar tensor - show as number
        const scalarValue = Array.isArray(value.values) ? value.values[0] : value.values;
        return (
          <div>
            <span className="font-mono text-orange-400 text-xl font-bold">{scalarValue}</span>
            <span className="text-xs text-gray-500 ml-2">torch.{value.dtype}</span>
          </div>
        );
      case 'tensor_1d':
        // 1D tensor - show as array
        return (
          <div>
            <div className="text-xs text-gray-400 mb-2">
              torch tensor: shape {value.shape.join('x')} | {value.dtype}
            </div>
            <ArrayVisualization arr={value.values} name={name} />
          </div>
        );
      case 'tensor_2d':
        // 2D tensor - show as matrix
        return (
          <div>
            <div className="text-xs text-gray-400 mb-2">
              torch tensor: shape {value.shape.join('x')} | {value.dtype}
            </div>
            <MatrixVisualization matrix={{ type: 'ndarray', values: value.values }} name={name} />
          </div>
        );
      case 'tensor_nd':
        // Higher dimensional - show info
        return (
          <div className="space-y-2">
            <div className="text-xs text-yellow-400 mb-2">
              torch tensor: shape {value.shape.join('x')} | {value.dtype}
            </div>
            <div className="bg-slate-700 p-3 rounded text-sm text-gray-300">
              {value.summary ? (
                <>
                  <div>Size: {value.summary.size}</div>
                  <div>Min: {value.summary.min?.toFixed(4)}</div>
                  <div>Max: {value.summary.max?.toFixed(4)}</div>
                  <div>Mean: {value.summary.mean?.toFixed(4)}</div>
                </>
              ) : (
                <div>High-dimensional tensor</div>
              )}
            </div>
          </div>
        );
      case 'matrix': return <MatrixVisualization matrix={value} name={name} />;
      case 'dict': return <DictVisualization dict={value} />;
      case 'string': return <span className="font-mono text-green-400 text-lg">"{value}"</span>;
      case 'number': return <span className="font-mono text-orange-400 text-xl font-bold">{value}</span>;
      default: return <span className="font-mono text-gray-400">{JSON.stringify(value)}</span>;
    }
  };

  return (
    <div className="xl:col-span-2 bg-slate-800 rounded-xl shadow-2xl p-4 border border-slate-700">
      <h2 className="text-lg font-semibold text-white mb-3">Visual Canvas</h2>
      
      {executionLog.length === 0 ? (
        <div className="text-slate-400 text-center py-32">
          <div className="text-6xl mb-4 opacity-50">🎨</div>
          <p className="text-lg">Run your code to see visualizations</p>
        </div>
      ) : (
        <div className="space-y-4 max-h-[500px] overflow-y-auto p-4 bg-slate-900/50 rounded-lg">
          {currentStepData?.formula && (
            <div className="bg-indigo-900/30 border-2 border-indigo-500 rounded-xl p-4 mb-4">
              <div className="text-xs text-indigo-400 mb-2 font-semibold">📐 Formula at Line {currentStepData.lineno}</div>
              <div className="bg-slate-900 p-4 rounded-lg">{renderFormula(currentStepData.formula)}</div>
            </div>
          )}
          
          {Object.keys(locals).length > 0 ? (
            Object.entries(locals).map(([name, value]) => (
              <div key={name} className={`rounded-xl p-4 border-2 transition-all ${
                changedVars.has(name) ? 'bg-yellow-900/20 border-yellow-500 shadow-xl shadow-yellow-500/30' : 'bg-slate-800/80 border-slate-600'
              }`}>
                <div className="flex items-center gap-3 mb-4">
                  <span className="font-mono text-lg font-bold text-blue-400">{name}</span>
                  <span className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">{detectType(value)}</span>
                  {changedVars.has(name) && (
                    <span className="text-xs bg-yellow-500 text-black px-2 py-1 rounded-full font-bold">CHANGED</span>
                  )}
                </div>
                <div className="pl-2">{renderValue(value, name)}</div>
              </div>
            ))
          ) : (
            <div className="text-slate-400 text-center py-16">No variables defined yet</div>
          )}
        </div>
      )}
    </div>
  );
};