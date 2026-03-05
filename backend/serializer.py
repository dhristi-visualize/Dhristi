# import json
# import numpy as np
# import torch
# import io

# def is_linked_list_node(obj):
#     return hasattr(obj, "__dict__") and "next" in obj.__dict__

# def safe_json(value, max_elements=30, seen=None):
#     if seen is None:
#         seen = set()

#     # Handle numpy arrays and subclasses (including TracingArray)
#     if isinstance(value, np.ndarray):
#         return value.tolist()

#     # Handle numpy scalar types
#     if isinstance(value, np.integer):
#         return int(value)
#     if isinstance(value, np.floating):
#         return float(value)
#     if isinstance(value, np.bool_):
#         return bool(value)

#     # Handle iterators that aren't directly serializable
#     if hasattr(value, '__iter__') and not isinstance(value, (str, list, dict, tuple)):
#         try:
#             return safe_json(list(value), seen=seen)
#         except Exception:
#             return str(value)

#     value_id = id(value)
#     if value_id in seen:
#         return {"type": "cycle"}

#     if hasattr(value, '__class__') and 'torch.nn' in str(type(value)):
#         return {
#             "type" : "nn_model",
#             "model_repr" : repr(value),
#             "model_str" : str(value)
#         }
#     # Handle datetime objects
#     if hasattr(value, 'isoformat'):  # datetime, date, time
#         return str(value)
    
#     # Handle Decimal
#     if value.__class__.__name__ == 'Decimal':
#         return str(value)
    
#     # Handle Fraction
#     if value.__class__.__name__ == 'Fraction':
#         return str(value)
    
#     # Handle linked lists
#     if is_linked_list_node(value):
#         elements = []
#         current = value
#         steps = 0
#         max_steps = 20

#         while current is not None and id(current) not in seen and steps < max_steps:
#             seen.add(id(current))

#             elements.append(
#                 safe_json(getattr(current, "val", None), max_elements, seen)
#             )

#             current = getattr(current, "next", None)
#             steps += 1

#         if current is not None:
#             elements.append("cycle")

#         return {
#             "type": "linked_list",
#             "values": elements
#         }


    
#     # Handle numpy arrays
#     if isinstance(value, np.ndarray):
#         size = value.size
        
#         if size <= max_elements:
#             return {
#                 "type": "ndarray",
#                 "values": value.tolist()
#             }
#         else:
#             try:
#                 flat = value.ravel()
#                 return {
#                     "type": "ndarray",
#                     "summary": {
#                         "size": int(size),
#                         "min": float(flat.min()),
#                         "max": float(flat.max()),
#                         "mean": float(flat.mean()),
#                         "sample": flat[:min(6, size)].tolist()
#                     }
#                 }
#             except:
#                 return repr(value)

#     # Handle torch tensors
#     if torch is not None and isinstance(value, torch.Tensor):
#         t = value
#         numel = t.numel()
        
#         if numel <= max_elements:
#             tensor_value = t.cpu().detach().tolist()
#             return {
#                 "type": "torchtensor",
#                 # "__torch_tensor__": True,
#                 "shape": list(t.size()),
#                 "dtype": str(t.dtype),
#                 "values": tensor_value
#             }
#         else:
#             try:
#                 flat = t.cpu().detach().view(-1)
#                 return {
#                     "type": "torchtensor",
#                     # "__torch_tensor__": True,
#                     "shape": list(t.size()),
#                     "dtype": str(t.dtype),
#                     "summary": {
#                         "size": int(numel),
#                         "min": float(flat.min().item()),
#                         "max": float(flat.max().item()),
#                         "mean": float(flat.float().mean().item()),
#                         "sample": flat[:min(6, numel)].tolist()
#                     }
#                 }
#             except:
#                 return repr(value)
    
#     # Handle user-defined objects
#     if hasattr(value, "__dict__"):
#         if id(value) in seen:
#             return {"type": "cycle"}

#         seen.add(id(value))

#         return {
#             "type": "object",
#             "class": value.__class__.__name__,
#             "fields": {
#                 k: safe_json(v, max_elements, seen)
#                 for k, v in value.__dict__.items()
#                 if not k.startswith("__")
#             }
#         }


#     # Handle regular Python objects
#     try:
#         # Test if it's JSON serializable
#         json.dumps(value)
#         return value
#     except (TypeError, ValueError):
#         return str(value)

import json
import numpy as np
import io

try:
    import torch
except ImportError:
    torch = None

def is_linked_list_node(obj):
    return hasattr(obj, "__dict__") and "next" in obj.__dict__

def safe_json(value, max_elements=30, seen=None):
    if seen is None:
        seen = set()

    # ── Numpy types (must come before the __iter__ check, since ndarray
    #    has __iter__ and would otherwise be converted via list()) ──────────
    if isinstance(value, np.ndarray):
        size = value.size
        if size <= max_elements:
            return {
                "type": "ndarray",
                "values": value.tolist()     # tolist() gives plain Python scalars
            }
        else:
            try:
                flat = value.ravel()
                return {
                    "type": "ndarray",
                    "summary": {
                        "size":   int(size),
                        "min":    float(flat.min()),
                        "max":    float(flat.max()),
                        "mean":   float(flat.mean()),
                        "sample": flat[:min(6, size)].tolist()
                    }
                }
            except Exception:
                return repr(value)

    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)

    # ── Torch tensors (before __iter__ check — tensors are iterable) ───────
    if torch is not None and isinstance(value, torch.Tensor):
        numel = value.numel()
        if numel <= max_elements:
            return {
                "type":   "torchtensor",
                "shape":  list(value.size()),
                "dtype":  str(value.dtype),
                "values": value.cpu().detach().tolist()
            }
        else:
            try:
                flat = value.cpu().detach().view(-1)
                return {
                    "type":  "torchtensor",
                    "shape": list(value.size()),
                    "dtype": str(value.dtype),
                    "summary": {
                        "size":   int(numel),
                        "min":    float(flat.min().item()),
                        "max":    float(flat.max().item()),
                        "mean":   float(flat.float().mean().item()),
                        "sample": flat[:min(6, numel)].tolist()
                    }
                }
            except Exception:
                return repr(value)

    # ── Cycle guard ──────────────────────────────────────────────────────────
    value_id = id(value)
    if value_id in seen:
        return {"type": "cycle"}

    # ── torch.nn models ──────────────────────────────────────────────────────
    if hasattr(value, '__class__') and 'torch.nn' in str(type(value)):
        return {
            "type":        "nn_model",
            "model_repr":  repr(value),
            "model_str":   str(value)
        }

    # ── datetime / Decimal / Fraction ────────────────────────────────────────
    if hasattr(value, 'isoformat'):
        return str(value)
    if value.__class__.__name__ == 'Decimal':
        return str(value)
    if value.__class__.__name__ == 'Fraction':
        return str(value)

    # ── Linked list nodes ────────────────────────────────────────────────────
    if is_linked_list_node(value):
        elements = []
        current  = value
        steps    = 0
        max_steps = 20
        while current is not None and id(current) not in seen and steps < max_steps:
            seen.add(id(current))
            elements.append(safe_json(getattr(current, "val", None), max_elements, seen))
            current = getattr(current, "next", None)
            steps  += 1
        if current is not None:
            elements.append("cycle")
        return {"type": "linked_list", "values": elements}

    # ── Plain Python containers — RECURSE into contents ──────────────────────
    # This is the critical fix: list/dict/tuple must have their contents
    # serialized recursively, not passed raw to json.dumps.
    if isinstance(value, list):
        seen.add(value_id)
        return [safe_json(item, max_elements, seen) for item in value]

    if isinstance(value, tuple):
        seen.add(value_id)
        return [safe_json(item, max_elements, seen) for item in value]

    if isinstance(value, dict):
        seen.add(value_id)
        return {
            str(k): safe_json(v, max_elements, seen)
            for k, v in value.items()
        }

    # ── Other iterables (generators, zip, map, range, set, …) ───────────────
    # Must come AFTER the numpy/torch checks so those types aren't consumed here
    if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
        try:
            return [safe_json(item, max_elements, seen) for item in value]
        except Exception:
            return str(value)

    # ── User-defined objects ─────────────────────────────────────────────────
    if hasattr(value, "__dict__"):
        seen.add(value_id)
        return {
            "type":   "object",
            "class":  value.__class__.__name__,
            "fields": {
                k: safe_json(v, max_elements, seen)
                for k, v in value.__dict__.items()
                if not k.startswith("__")
            }
        }

    # ── Scalar fallback ──────────────────────────────────────────────────────
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)