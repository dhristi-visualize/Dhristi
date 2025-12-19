const detectType = (value) => {
        if (!value || typeof value !== 'object') {
        if (typeof value === 'string') return 'string';
        if (typeof value === 'number') return 'number';
            return 'other';
        }
            
        // FIXED: Check for numpy array first (before checking for dict)
        if (value.type === 'ndarray') return 'ndarray';
        if (value.__torch_tensor__) return 'tensor';
            
        // Check for regular arrays
        if (Array.isArray(value)) {
            if (value.length > 0 && Array.isArray(value[0])) return 'matrix';
              return 'array';
        }
            
        // If it's a plain object (dict)
        if (typeof value === 'object' && value !== null) return 'dict';    
            return 'other';
};