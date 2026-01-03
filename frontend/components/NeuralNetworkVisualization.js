// window.Components = window.Components || {};

// window.Components.NeuralNetworkVisualization = ({ model }) => {
//   if (model.type === "manual_dense") {
//     return (
//       <div className="space-y-4">
//         <div className="text-xs text-cyan-400 font-semibold">
//           Manual Dense Network
//         </div>

//         <div className="flex items-center justify-center gap-8">
//           {/* Input layer */}
//           <div className="flex flex-col gap-2">
//             {Array.from({ length: model.input_size }).map((_, i) => (
//               <div key={i} className="w-8 h-8 rounded-full bg-blue-500" />
//             ))}
//           </div>

//           {/* Hidden / output layer */}
//           <div className="flex flex-col gap-4">
//             {model.weights.map((_, i) => (
//               <div key={i} className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center text-xs text-white">
//                 +{model.biases[i]}
//               </div>
//             ))}
//           </div>
//         </div>
//       </div>
//     );
//   }

//   const layers = model.layers || [];
  
//   return (
//     <div className="space-y-4">
//       <div className="text-xs text-cyan-400 mb-3 font-semibold">
//         Neural Network: {model.model_name}
//       </div>
      
//       <div className="flex flex-col items-center gap-3 bg-slate-900 p-6 rounded-lg">
//         {layers.map((layer, idx) => (
//           <React.Fragment key={idx}>
//             {/* Layer Box */}
//             <div className="relative">
//               <div className="bg-gradient-to-r from-cyan-600 to-blue-600 text-white px-6 py-4 rounded-lg shadow-lg border-2 border-cyan-400 min-w-[200px]">
//                 <div className="text-center">
//                   <div className="font-bold text-lg">{layer.layer}</div>
//                   {layer.in && layer.out && (
//                     <div className="text-xs mt-1 opacity-90">
//                       {layer.in} → {layer.out}
//                     </div>
//                   )}
//                 </div>
//               </div>
              
//               {/* Layer number badge */}
//               <div className="absolute -top-2 -left-2 bg-purple-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
//                 {idx + 1}
//               </div>
//             </div>
            
//             {/* Arrow to next layer */}
//             {idx < layers.length - 1 && (
//               <div className="flex flex-col items-center">
//                 <svg width="24" height="40" viewBox="0 0 24 40">
//                   <line x1="12" y1="0" x2="12" y2="35" stroke="#06b6d4" strokeWidth="3"/>
//                   <polygon points="12,40 7,30 17,30" fill="#06b6d4"/>
//                 </svg>
//               </div>
//             )}
//           </React.Fragment>
//         ))}
//       </div>
      
//       {/* Summary */}
//       <div className="bg-slate-800 p-3 rounded text-xs text-gray-300">
//         <div className="font-semibold mb-1">Architecture Summary:</div>
//         <div>{layers.length} layers total</div>
//         {layers.some(l => l.in) && (
//           <div className="mt-1">
//             Input: {layers[0]?.in} → Output: {layers[layers.length - 1]?.out}
//           </div>
//         )}
//       </div>
//     </div>
//   );
// };

window.Components = window.Components || {};

window.Components.NeuralNetworkVisualization = ({ model }) => {
  if (!model || !model.layers || model.layers.length === 0) {
    return null;
  }

  const layers = model.layers;

  /* -------------------------------
     1. Expand layers into neurons
  -------------------------------- */

  const neuronLayers = layers.map((layer, layerIndex) => {
    const count =
      layerIndex === 0 ? layer.in : layer.out;

    return Array.from({ length: count }, (_, i) => ({
      id: `${layerIndex}-${i}`,
      layerIndex,
      neuronIndex: i
    }));
  });

  /* -------------------------------
     2. Layout neurons
  -------------------------------- */

  const X_GAP = 180;
  const Y_GAP = 48;
  const NEURON_SIZE = 24;

  const positionedLayers = neuronLayers.map((layer, x) => {
    const totalHeight = (layer.length - 1) * Y_GAP;
    return layer.map((n, y) => ({
      ...n,
      x: x * X_GAP,
      y: y * Y_GAP - totalHeight / 2
    }));
  });

  const neurons = positionedLayers.flat();

  /* -------------------------------
     3. Build edges (fully connected)
  -------------------------------- */

  const edges = [];

  for (let l = 0; l < positionedLayers.length - 1; l++) {
    for (const from of positionedLayers[l]) {
      for (const to of positionedLayers[l + 1]) {
        edges.push({ from, to });
      }
    }
  }

  /* -------------------------------
     4. Compute canvas size
  -------------------------------- */

  const maxX = Math.max(...neurons.map(n => n.x)) + NEURON_SIZE + 40;
  const minY = Math.min(...neurons.map(n => n.y));
  const maxY = Math.max(...neurons.map(n => n.y)) + NEURON_SIZE;

  const canvasWidth = maxX;
  const canvasHeight = maxY - minY + 40;

  /* -------------------------------
     5. Render
  -------------------------------- */

  return (
    <div className="space-y-3">
      <div className="text-xs text-cyan-400 font-semibold">
        Neural Network: {model.model_name}
      </div>

      <div className="relative bg-slate-900 rounded-lg p-4 overflow-visible">

        {/* SVG edges */}
        <svg
          width={canvasWidth}
          height={canvasHeight}
          className="absolute top-0 left-0"
          style={{ pointerEvents: "none" }}
        >
          {edges.map((e, i) => (
            <line
              key={i}
              x1={e.from.x + NEURON_SIZE / 2}
              y1={e.from.y - minY + NEURON_SIZE / 2}
              x2={e.to.x + NEURON_SIZE / 2}
              y2={e.to.y - minY + NEURON_SIZE / 2}
              stroke="#06b6d4"
              strokeWidth="1"
              opacity="0.35"
            />
          ))}
        </svg>

        {/* Neurons */}
        <div
          style={{
            width: canvasWidth,
            height: canvasHeight,
            position: "relative"
          }}
        >
          {neurons.map(n => (
            <div
              key={n.id}
              className="absolute rounded-full bg-cyan-400 border border-cyan-200 shadow"
              style={{
                width: NEURON_SIZE,
                height: NEURON_SIZE,
                left: n.x,
                top: n.y - minY
              }}
              title={`Layer ${n.layerIndex}, Neuron ${n.neuronIndex}`}
            />
          ))}
        </div>
      </div>

      {/* Summary */}
      <div className="bg-slate-800 p-3 rounded text-xs text-gray-300">
        <div className="font-semibold mb-1">Architecture Summary</div>
        <div>{layers.length} layers</div>
        <div>
          Input: {layers[0].in} → Output: {layers[layers.length - 1].out}
        </div>
      </div>
    </div>
  );
};
