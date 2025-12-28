import json
import numpy as np
import torch

def safe_json(value, max_elements=30):
    if hasattr(value, '__class__') and 'torch.nn' in str(type(value)):
        return {
            "type" : "nn_model",
            "model_repr" : repr(value),
            "model_str" : str(value)
        }
    # Handle datetime objects
    if hasattr(value, 'isoformat'):  # datetime, date, time
        return str(value)
    
    # Handle Decimal
    if value.__class__.__name__ == 'Decimal':
        return str(value)
    
    # Handle Fraction
    if value.__class__.__name__ == 'Fraction':
        return str(value)
    
    # Handle numpy arrays
    if isinstance(value, np.ndarray):
        size = value.size
        
        if size <= max_elements:
            return {
                "type": "ndarray",
                "values": value.tolist()
            }
        else:
            try:
                flat = value.ravel()
                return {
                    "type": "ndarray",
                    "summary": {
                        "size": int(size),
                        "min": float(flat.min()),
                        "max": float(flat.max()),
                        "mean": float(flat.mean()),
                        "sample": flat[:min(6, size)].tolist()
                    }
                }
            except:
                return repr(value)

    # Handle torch tensors
    if torch is not None and isinstance(value, torch.Tensor):
        t = value
        numel = t.numel()
        
        if numel <= max_elements:
            tensor_value = t.cpu().detach().tolist()
            return {
                "type": "torchtensor",
                # "__torch_tensor__": True,
                "shape": list(t.size()),
                "dtype": str(t.dtype),
                "values": tensor_value
            }
        else:
            try:
                flat = t.cpu().detach().view(-1)
                return {
                    "type": "torchtensor",
                    # "__torch_tensor__": True,
                    "shape": list(t.size()),
                    "dtype": str(t.dtype),
                    "summary": {
                        "size": int(numel),
                        "min": float(flat.min().item()),
                        "max": float(flat.max().item()),
                        "mean": float(flat.float().mean().item()),
                        "sample": flat[:min(6, numel)].tolist()
                    }
                }
            except:
                return repr(value)
    
    # Handle regular Python objects
    try:
        # Test if it's JSON serializable
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)