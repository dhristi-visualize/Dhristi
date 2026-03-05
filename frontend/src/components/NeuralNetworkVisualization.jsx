// export default function NeuralNetworkVisualization({ model }) {
//   if (!model || !model.layers || model.layers.length === 0) {
//     return null;
//   }

//   const layers = model.layers;

//   /* -------------------------------
//      1. Expand layers into neurons
//   -------------------------------- */

//   const neuronLayers = layers.map((layer, layerIndex) => {
//     const count =
//       layerIndex === 0 ? layer.in : layer.out;

//     return Array.from({ length: count }, (_, i) => ({
//       id: `${layerIndex}-${i}`,
//       layerIndex,
//       neuronIndex: i,
//     }));
//   });

//   /* -------------------------------
//      2. Layout neurons
//   -------------------------------- */

//   const X_GAP = 180;
//   const Y_GAP = 48;
//   const NEURON_SIZE = 24;

//   const positionedLayers = neuronLayers.map((layer, x) => {
//     const totalHeight = (layer.length - 1) * Y_GAP;
//     return layer.map((n, y) => ({
//       ...n,
//       x: x * X_GAP,
//       y: y * Y_GAP - totalHeight / 2,
//     }));
//   });

//   const neurons = positionedLayers.flat();

//   /* -------------------------------
//      3. Build edges (fully connected)
//   -------------------------------- */

//   const edges = [];

//   for (let l = 0; l < positionedLayers.length - 1; l++) {
//     for (const from of positionedLayers[l]) {
//       for (const to of positionedLayers[l + 1]) {
//         edges.push({ from, to });
//       }
//     }
//   }

//   /* -------------------------------
//      4. Compute canvas size
//   -------------------------------- */

//   const maxX =
//     Math.max(...neurons.map((n) => n.x)) +
//     NEURON_SIZE +
//     40;

//   const minY = Math.min(...neurons.map((n) => n.y));
//   const maxY =
//     Math.max(...neurons.map((n) => n.y)) +
//     NEURON_SIZE;

//   const canvasWidth = maxX;
//   const canvasHeight = maxY - minY + 40;

//   /* -------------------------------
//      5. Render
//   -------------------------------- */

//   return (
//     <div className="space-y-3">
//       <div className="text-xs text-cyan-400 font-semibold">
//         Neural Network: {model.model_name}
//       </div>

//       <div className="relative bg-slate-900 rounded-lg p-4 overflow-visible">
//         {/* SVG edges */}
//         <svg
//           width={canvasWidth}
//           height={canvasHeight}
//           className="absolute top-0 left-0"
//           style={{ pointerEvents: "none" }}
//         >
//           {edges.map((e, i) => (
//             <line
//               key={i}
//               x1={e.from.x + NEURON_SIZE / 2}
//               y1={e.from.y - minY + NEURON_SIZE / 2}
//               x2={e.to.x + NEURON_SIZE / 2}
//               y2={e.to.y - minY + NEURON_SIZE / 2}
//               stroke="#06b6d4"
//               strokeWidth="1"
//               opacity="0.35"
//             />
//           ))}
//         </svg>

//         {/* Neurons */}
//         <div
//           style={{
//             width: canvasWidth,
//             height: canvasHeight,
//             position: "relative",
//           }}
//         >
//           {neurons.map((n) => (
//             <div
//               key={n.id}
//               className="absolute rounded-full bg-cyan-400 border border-cyan-200 shadow"
//               style={{
//                 width: NEURON_SIZE,
//                 height: NEURON_SIZE,
//                 left: n.x,
//                 top: n.y - minY,
//               }}
//               title={`Layer ${n.layerIndex}, Neuron ${n.neuronIndex}`}
//             />
//           ))}
//         </div>
//       </div>

//       {/* Summary */}
//       <div className="bg-slate-800 p-3 rounded text-xs text-gray-300">
//         <div className="font-semibold mb-1">
//           Architecture Summary
//         </div>
//         <div>{layers.length} layers</div>
//         <div>
//           Input: {layers[0].in} → Output:{" "}
//           {layers[layers.length - 1].out}
//         </div>
//       </div>
//     </div>
//   );
// }


export default function NeuralNetworkVisualization({ model }) {
  if (!model || !model.layers || model.layers.length === 0) return null;

  // ── 1. Separate Linear layers (have neurons) from activations (labels only)
  const linearLayers = model.layers.filter(l => l.layer === "Linear");
  const allLayers    = model.layers;   // used for the summary list below

  if (linearLayers.length === 0) return null;

  // ── 2. Build neuron columns from LINEAR layers only ──────────────────────
  // First linear: show both input AND output columns
  // Subsequent linears: only show output column (input = prev output)
  const neuronColumns = [];

  linearLayers.forEach((layer, i) => {
    if (i === 0) {
      neuronColumns.push({ count: layer.in,  label: "Input",          layerIdx: 0 });
    }
    neuronColumns.push({ count: layer.out, label: `Layer ${i + 1}`,  layerIdx: i + 1 });
  });

  // ── 3. Layout ─────────────────────────────────────────────────────────────
  const X_GAP      = 180;
  const Y_GAP      = 48;
  const NEURON_SIZE = 24;
  const MAX_NEURONS = 8;   // cap display so large networks don't overflow

  const positionedCols = neuronColumns.map((col, x) => {
    const displayCount = Math.min(col.count, MAX_NEURONS);
    const hasEllipsis  = col.count > MAX_NEURONS;
    const totalHeight  = (displayCount - 1) * Y_GAP;

    const neurons = Array.from({ length: displayCount }, (_, i) => ({
      id:          `${x}-${i}`,
      colIndex:    x,
      neuronIndex: i,
      x:           x * X_GAP,
      y:           i * Y_GAP - totalHeight / 2,
    }));

    return { ...col, neurons, hasEllipsis, displayCount };
  });

  const allNeurons = positionedCols.flatMap(c => c.neurons);

  // ── 4. Edges ──────────────────────────────────────────────────────────────
  const edges = [];
  for (let c = 0; c < positionedCols.length - 1; c++) {
    for (const from of positionedCols[c].neurons) {
      for (const to of positionedCols[c + 1].neurons) {
        edges.push({ from, to });
      }
    }
  }

  // ── 5. Canvas size ────────────────────────────────────────────────────────
  const minY       = Math.min(...allNeurons.map(n => n.y));
  const maxY       = Math.max(...allNeurons.map(n => n.y));
  const maxX       = Math.max(...allNeurons.map(n => n.x)) + NEURON_SIZE + 40;
  const canvasH    = maxY - minY + NEURON_SIZE + 40;

  // ── 6. Activation badge positions (between linear columns) ───────────────
  // Map: after linearLayers[i] → show its activation between col i+1 and i+2
  const activationLabels = [];
  let linearIdx = 0;
  allLayers.forEach(layer => {
    if (layer.layer === "Linear") { linearIdx++; return; }
    // Place badge above the midpoint between column linearIdx-1 and linearIdx
    if (linearIdx > 0 && linearIdx < positionedCols.length) {
      const x1 = positionedCols[linearIdx - 1].neurons[0]?.x ?? 0;
      const x2 = positionedCols[linearIdx].neurons[0]?.x ?? 0;
      activationLabels.push({
        label: layer.layer,
        x:     (x1 + x2) / 2 + NEURON_SIZE / 2,
      });
    }
  });

  // ── 7. Render ─────────────────────────────────────────────────────────────
  return (
    <div className="space-y-3">
      <div className="text-xs text-cyan-400 font-semibold">
        Neural Network: {model.model_name}
        <span className="ml-2 text-slate-400 font-normal">({model.type})</span>
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
              stroke="#06b6d4" strokeWidth="1" opacity="0.3"
            />
          ))}
          {/* Activation labels between columns */}
          {activationLabels.map((a, i) => (
            <text
              key={i}
              x={a.x} y={12}
              textAnchor="middle"
              fill="#a78bfa"
              fontSize="10"
              fontFamily="monospace"
            >
              {a.label}
            </text>
          ))}
        </svg>

        <div style={{ width: maxX, height: canvasH, position: "relative" }}>
          {positionedCols.map((col, ci) => (
            <div key={ci}>
              {/* Column label */}
              <div
                className="absolute text-xs text-slate-400 text-center"
                style={{ left: col.neurons[0]?.x, top: 0, width: NEURON_SIZE }}
              >
                {col.label}
              </div>

              {/* Neurons */}
              {col.neurons.map(n => (
                <div
                  key={n.id}
                  className="absolute rounded-full bg-cyan-400 border border-cyan-200 shadow"
                  style={{
                    width:  NEURON_SIZE,
                    height: NEURON_SIZE,
                    left:   n.x,
                    top:    n.y - minY + 20,
                  }}
                  title={`${col.label}, Neuron ${n.neuronIndex}`}
                />
              ))}

              {/* Ellipsis for large layers */}
              {col.hasEllipsis && (
                <div
                  className="absolute text-cyan-400 text-lg"
                  style={{ left: col.neurons[0]?.x + 6, top: col.neurons.at(-1)?.y - minY + 28 }}
                >
                  ···
                </div>
              )}

              {/* Neuron count badge */}
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

      {/* Architecture summary — now shows ALL layers including activations */}
      <div className="bg-slate-800 p-3 rounded text-xs text-gray-300">
        <div className="font-semibold mb-1">Architecture</div>
        <div className="flex flex-wrap gap-1">
          {allLayers.map((l, i) => (
            <span
              key={i}
              className={`px-2 py-0.5 rounded text-xs font-mono ${
                l.layer === "Linear"
                  ? "bg-cyan-900 text-cyan-300"
                  : "bg-violet-900 text-violet-300"
              }`}
            >
              {l.layer === "Linear" ? `Linear(${l.in}→${l.out})` : l.layer}
            </span>
          ))}
        </div>
        <div className="mt-2 text-slate-400">
          Input: {linearLayers[0]?.in} → Output: {linearLayers.at(-1)?.out}
          {" · "}{model.type === "Dense" ? "Traced at runtime" : "From AST"}
        </div>
      </div>
    </div>
  );
}
