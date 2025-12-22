window.Utils = window.Utils || {};

window.Utils.detectType = (value) => {
  if (!value || typeof value !== 'object') {
    if (typeof value === 'string') return 'string';
    if (typeof value === 'number') return 'number';
    return 'other';
  }
  
  if (value.type === 'ndarray') return 'ndarray';
    // Check for torch tensors and determine dimensionality
  if (value.type === 'torchtensor') {
    const shape = value.shape || [];
    
    // Scalar (shape is [] or [1])
    if (shape.length === 0 || (shape.length === 1 && shape[0] === 1)) {
      return 'tensor_scalar';
    }
    
    // 1D tensor
    if (shape.length === 1) {
      return 'tensor_1d';
    }
    
    // 2D tensor
    if (shape.length === 2) {
      return 'tensor_2d';
    }
    
    // Higher dimensions - treat as matrix for now
    return 'tensor_nd';
  }
  // if (value.__torch_tensor__) return 'tensor';
  if (Array.isArray(value)) {
    if (value.length > 0 && Array.isArray(value[0])) return 'matrix';
    return 'array';
  }
  if (typeof value === 'object' && value !== null) return 'dict';
  return 'other';
};