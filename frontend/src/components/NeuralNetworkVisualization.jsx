// NeuralNetworkVisualization.jsx
//
// Props:
//   model          — the NN model dict from backend
//   currentNnOps   — current step's nn_ops array (may be empty)
//   executionLog   — full steps array (used to find last active layer for activations)
//   currentStep    — current step index

export default function NeuralNetworkVisualization({
  model,
  currentNnOps = [],
  executionLog = [],
  currentStep = 0,
}) {
  if (!model || !model.layers || model.layers.length === 0) return null;

  const linearLayers = model.layers.filter(l => l.layer === "Linear");
  const allLayers    = model.layers;

  if (linearLayers.length === 0) return null;

  // ── Determine what to highlight ──────────────────────────────────────────
  // For a matmul op: highlight the from/to columns and their connections.
  // For an activation op: look back through executionLog to find the most
  // recent matmul op's layer_index, then highlight that output column.
  const activeLayerIndices    = new Set();
  const activeConnectionPairs = new Set();

  const hasMatmul     = currentNnOps.some(op => op.kind === "matmul");
  const hasActivation = currentNnOps.some(op => op.kind === "activation");

  if (hasMatmul) {
    for (const op of currentNnOps) {
      if (op.kind === "matmul" && op.layer_index != null) {
        activeLayerIndices.add(op.layer_index);
        activeLayerIndices.add(op.layer_index + 1);
        activeConnectionPairs.add(`${op.layer_index}-${op.layer_index + 1}`);
      }
    }
  }

  if (hasActivation) {
    // Find the most recent matmul op in previous steps to know which column to light up
    for (let i = currentStep - 1; i >= 0; i--) {
      const prevOps = executionLog[i]?.nn_ops ?? [];
      const prevMatmul = prevOps.find(op => op.kind === "matmul" && op.layer_index != null);
      if (prevMatmul) {
        activeLayerIndices.add(prevMatmul.layer_index + 1);
        break;
      }
    }
  }

  const hasActiveOps = activeLayerIndices.size > 0 || hasActivation;

  // ── Build neuron columns ──────────────────────────────────────────────────
  const neuronColumns = [];
  linearLayers.forEach((layer, i) => {
    if (i === 0) neuronColumns.push({ count: layer.in,  label: "Input",         colIndex: 0 });
    neuronColumns.push(            { count: layer.out, label: `Layer ${i + 1}`, colIndex: i + 1 });
  });

  const X_GAP       = 180;
  const Y_GAP       = 48;
  const NEURON_SIZE  = 24;
  const MAX_NEURONS  = 8;

  const positionedCols = neuronColumns.map((col, x) => {
    const displayCount = Math.min(col.count, MAX_NEURONS);
    const hasEllipsis  = col.count > MAX_NEURONS;
    const totalHeight  = (displayCount - 1) * Y_GAP;
    const isActive     = activeLayerIndices.has(col.colIndex);

    const neurons = Array.from({ length: displayCount }, (_, i) => ({
      id: `${x}-${i}`, colIndex: x, neuronIndex: i,
      x: x * X_GAP,
      y: i * Y_GAP - totalHeight / 2,
    }));

    return { ...col, neurons, hasEllipsis, displayCount, isActive };
  });

  const allNeurons = positionedCols.flatMap(c => c.neurons);

  // ── Edges ─────────────────────────────────────────────────────────────────
  const edges = [];
  for (let c = 0; c < positionedCols.length - 1; c++) {
    const isActive = activeConnectionPairs.has(`${c}-${c + 1}`);
    for (const from of positionedCols[c].neurons) {
      for (const to of positionedCols[c + 1].neurons) {
        edges.push({ from, to, isActive });
      }
    }
  }

  // ── Canvas size ───────────────────────────────────────────────────────────
  const minY    = Math.min(...allNeurons.map(n => n.y));
  const maxY    = Math.max(...allNeurons.map(n => n.y));
  const maxX    = Math.max(...allNeurons.map(n => n.x)) + NEURON_SIZE + 40;
  const canvasH = maxY - minY + NEURON_SIZE + 40;

  // ── Activation badge positions ────────────────────────────────────────────
  const activationLabels = [];
  let linearIdx = 0;
  allLayers.forEach(layer => {
    if (layer.layer === "Linear") { linearIdx++; return; }
    if (linearIdx > 0 && linearIdx < positionedCols.length) {
      const x1 = positionedCols[linearIdx - 1].neurons[0]?.x ?? 0;
      const x2 = positionedCols[linearIdx].neurons[0]?.x ?? 0;
      activationLabels.push({
        label: layer.layer,
        isActive: hasActivation,
        x: (x1 + x2) / 2 + NEURON_SIZE / 2,
      });
    }
  });

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="text-xs text-cyan-400 font-semibold">
          Neural Network: {model.model_name}
          <span className="ml-2 text-slate-400 font-normal">({model.type})</span>
        </div>
        {hasActiveOps && (
          <span className="text-xs bg-yellow-500 text-black px-2 py-0.5 rounded font-semibold animate-pulse">
            ● {hasActivation ? "ACTIVATION" : "FORWARD PASS"}
          </span>
        )}
      </div>

      <div className="relative bg-slate-900 rounded-lg p-4 overflow-x-auto">
        <svg
          width={maxX}
          height={canvasH}
          className="absolute top-0 left-0"
          style={{ pointerEvents: "none" }}
        >
          {edges.map((e, i) => (
            <line
              key={i}
              x1={e.from.x + NEURON_SIZE / 2}
              y1={e.from.y - minY + NEURON_SIZE / 2 + 20}
              x2={e.to.x   + NEURON_SIZE / 2}
              y2={e.to.y   - minY + NEURON_SIZE / 2 + 20}
              stroke={e.isActive ? "#facc15" : "#06b6d4"}
              strokeWidth={e.isActive ? 1.5 : 1}
              opacity={e.isActive ? 0.85 : (hasActiveOps ? 0.08 : 0.3)}
            />
          ))}

          {activationLabels.map((a, i) => (
            <text
              key={i}
              x={a.x} y={12}
              textAnchor="middle"
              fill={a.isActive ? "#facc15" : "#a78bfa"}
              fontSize="10"
              fontFamily="monospace"
              fontWeight={a.isActive ? "bold" : "normal"}
            >
              {a.label}
            </text>
          ))}
        </svg>

        <div style={{ width: maxX, height: canvasH, position: "relative" }}>
          {positionedCols.map((col, ci) => (
            <div key={ci}>
              <div
                className={`absolute text-xs text-center transition-colors ${
                  col.isActive ? "text-yellow-400 font-semibold" : "text-slate-400"
                }`}
                style={{ left: col.neurons[0]?.x, top: 0, width: NEURON_SIZE }}
              >
                {col.label}
              </div>

              {col.neurons.map(n => (
                <div
                  key={n.id}
                  className="absolute rounded-full border shadow"
                  style={{
                    width:  NEURON_SIZE,
                    height: NEURON_SIZE,
                    left:   n.x,
                    top:    n.y - minY + 20,
                    backgroundColor: col.isActive ? "#facc15" : "#22d3ee",
                    borderColor:     col.isActive ? "#fef08a" : "#a5f3fc",
                    boxShadow: col.isActive ? "0 0 10px 3px rgba(250,204,21,0.6)" : undefined,
                    opacity: hasActiveOps && !col.isActive ? 0.2 : 1,
                    transition: "all 0.15s ease",
                  }}
                  title={`${col.label}, Neuron ${n.neuronIndex}`}
                />
              ))}

              {col.hasEllipsis && (
                <div
                  className={`absolute text-lg ${col.isActive ? "text-yellow-400" : "text-cyan-400"}`}
                  style={{ left: col.neurons[0]?.x + 6, top: col.neurons.at(-1)?.y - minY + 28 }}
                >
                  ···
                </div>
              )}

              <div
                className="absolute text-xs text-slate-500 text-center"
                style={{ left: col.neurons[0]?.x - 4, top: canvasH - 18, width: NEURON_SIZE + 8 }}
              >
                {col.count}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Architecture summary */}
      <div className="bg-slate-800 p-3 rounded text-xs text-gray-300">
        <div className="font-semibold mb-1">Architecture</div>
        <div className="flex flex-wrap gap-1">
          {allLayers.map((l, i) => {
            const layerLinearIdx = allLayers.slice(0, i).filter(x => x.layer === "Linear").length;
            const isLinearActive = l.layer === "Linear" &&
              (activeLayerIndices.has(layerLinearIdx) || activeLayerIndices.has(layerLinearIdx + 1));
            const isActActive = l.layer !== "Linear" && hasActivation;
            const isAct = isLinearActive || isActActive;
            return (
              <span
                key={i}
                className={`px-2 py-0.5 rounded text-xs font-mono transition-all ${
                  isAct
                    ? "bg-yellow-500 text-black font-bold"
                    : l.layer === "Linear"
                      ? "bg-cyan-900 text-cyan-300"
                      : "bg-violet-900 text-violet-300"
                }`}
              >
                {l.layer === "Linear" ? `Linear(${l.in}→${l.out})` : l.layer}
              </span>
            );
          })}
        </div>
        <div className="mt-2 text-slate-400">
          Input: {linearLayers[0]?.in} → Output: {linearLayers.at(-1)?.out}
          {" · "}{model.type === "Dense" ? "Traced at runtime" : "From AST"}
        </div>
      </div>
    </div>
  );
}