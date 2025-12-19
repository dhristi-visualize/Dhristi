const MatrixVisualization = ({ matrix, name }) => {
          // Check if it's a numpy array from backend
          if (matrix && matrix.type === 'ndarray') {
            const values = matrix.values;
            
            // If values is a 2D array, display as matrix
            if (Array.isArray(values) && Array.isArray(values[0])) {
              const rows = values.length;
              const cols = values[0].length;
              
              return (
                <div className="space-y-2">
                  <div className="text-xs text-gray-400 mb-2">
                    numpy array: {rows} × {cols}
                  </div>
                  <div className="inline-block border-2 border-green-500 rounded">
                    {values.map((row, i) => (
                      <div key={i} className="flex">
                        {row.map((val, j) => (
                          <div 
                            key={j}
                            className="w-16 h-16 border border-green-700/30 bg-green-900/20 flex items-center justify-center text-green-300 font-mono text-xs"
                          >
                            {typeof val === 'number' ? val.toFixed(2) : JSON.stringify(val)}
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              );
            }
            
            // If values is a 1D array, display as array visualization
            if (Array.isArray(values)) {
              return <ArrayVisualization arr={values} name={name} />;
            }
            
            // If we have summary (large array), show summary
            if (matrix.summary) {
              return (
                <div className="space-y-2">
                  <div className="text-xs text-yellow-400 mb-2">
                    Large numpy array (size: {matrix.summary.size})
                  </div>
                  <div className="bg-slate-700 p-3 rounded text-sm text-gray-300">
                    <div>Min: {matrix.summary.min?.toFixed(4)}</div>
                    <div>Max: {matrix.summary.max?.toFixed(4)}</div>
                    <div>Mean: {matrix.summary.mean?.toFixed(4)}</div>
                    <div className="mt-2">Sample: {JSON.stringify(matrix.summary.sample)}</div>
                  </div>
                </div>
              );
            }
          }

          // Check if it's a regular 2D array
          if (Array.isArray(matrix) && Array.isArray(matrix[0])) {
            const rows = matrix.length;
            const cols = matrix[0].length;

            return (
              <div className="space-y-2">
                <div className="text-xs text-gray-400 mb-2">
                  list: {rows} × {cols}
                </div>
                <div className="inline-block border-2 border-green-500 rounded">
                  {matrix.map((row, i) => (
                    <div key={i} className="flex">
                      {row.map((val, j) => (
                        <div 
                          key={j}
                          className="w-16 h-16 border border-green-700/30 bg-green-900/20 flex items-center justify-center text-green-300 font-mono text-xs"
                        >
                          {typeof val === 'number' ? val.toFixed(2) : JSON.stringify(val)}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            );
          }

          return <span className="font-mono text-orange-700">{JSON.stringify(matrix)}</span>;
        };