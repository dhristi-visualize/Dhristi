const NeuralNetworkVisualizer = ({ models }) => {
  if (!models || models.length === 0) return null;

  return (
    <div className="mb-6 p-4 bg-slate-800 rounded-xl border border-indigo-500">
      <h3 className="text-lg font-bold text-indigo-300 mb-3">
        Neural Network Architecture
      </h3>

      {models.map((model, i) => (
        <div key={i} className="space-y-2">
          <div className="text-indigo-400 font-mono">
            {model.model_name} ({model.type})
          </div>

          {model.layers.map((layer, idx) => (
            <div
              key={idx}
              className="flex items-center gap-3 bg-slate-700 p-2 rounded"
            >
              <div className="font-mono text-sm text-white">
                {layer.layer}
              </div>

              {layer.in !== undefined && (
                <div className="text-xs text-slate-300">
                  {layer.in} → {layer.out}
                </div>
              )}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};
