export default function NeuralNetworkVisualization({ model }) {
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
      neuronIndex: i,
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
      y: y * Y_GAP - totalHeight / 2,
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

  const maxX =
    Math.max(...neurons.map((n) => n.x)) +
    NEURON_SIZE +
    40;

  const minY = Math.min(...neurons.map((n) => n.y));
  const maxY =
    Math.max(...neurons.map((n) => n.y)) +
    NEURON_SIZE;

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
            position: "relative",
          }}
        >
          {neurons.map((n) => (
            <div
              key={n.id}
              className="absolute rounded-full bg-cyan-400 border border-cyan-200 shadow"
              style={{
                width: NEURON_SIZE,
                height: NEURON_SIZE,
                left: n.x,
                top: n.y - minY,
              }}
              title={`Layer ${n.layerIndex}, Neuron ${n.neuronIndex}`}
            />
          ))}
        </div>
      </div>

      {/* Summary */}
      <div className="bg-slate-800 p-3 rounded text-xs text-gray-300">
        <div className="font-semibold mb-1">
          Architecture Summary
        </div>
        <div>{layers.length} layers</div>
        <div>
          Input: {layers[0].in} → Output:{" "}
          {layers[layers.length - 1].out}
        </div>
      </div>
    </div>
  );
}
