export function detectType(value) {
  if (!value || typeof value !== 'object') {
    if (typeof value === 'string') return 'string';
    if (typeof value === 'number') return 'number';
    return 'other';
  }

  if (value.type === 'ndarray') return 'ndarray';

  // Torch tensors
  if (value.type === 'torchtensor') {
    const shape = value.shape || [];

    if (shape.length === 0 || (shape.length === 1 && shape[0] === 1)) {
      return 'tensor_scalar';
    }

    if (shape.length === 1) return 'tensor_1d';
    if (shape.length === 2) return 'tensor_2d';

    return 'tensor_nd';
  }

  if (Array.isArray(value)) {
    if (value.length > 0 && Array.isArray(value[0])) return 'matrix';
    return 'array';
  }

  if (typeof value === 'object' && value !== null) return 'dict';

  return 'other';
}
