window.Utils = window.Utils || {};

window.Utils.detectType = (value) => {
  if (!value || typeof value !== 'object') {
    if (typeof value === 'string') return 'string';
    if (typeof value === 'number') return 'number';
    return 'other';
  }
  
  if (value.type === 'ndarray') return 'ndarray';
  if (value.__torch_tensor__) return 'tensor';
  if (Array.isArray(value)) {
    if (value.length > 0 && Array.isArray(value[0])) return 'matrix';
    return 'array';
  }
  if (typeof value === 'object' && value !== null) return 'dict';
  return 'other';
};