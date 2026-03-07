"""
nn_runtime_tracer.py - with lineno tagging and public patching API
"""

import sys
import traceback
import numpy as np
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class TracedOp:
    kind: str
    name: str
    input_shapes: List[Tuple] = field(default_factory=list)
    output_shape: Optional[Tuple] = None
    extra: dict = field(default_factory=dict)
    lineno: Optional[int] = None        # NEW: source line that triggered this op


@dataclass
class DetectedLayer:
    layer_type: str
    in_features: Optional[int] = None
    out_features: Optional[int] = None


@dataclass
class DetectedModel:
    model_name: str
    source: str
    layers: List[DetectedLayer] = field(default_factory=list)

    def to_dict(self):
        def _int(v):
            return int(v) if v is not None else None

        layers_out = []
        for layer in self.layers:
            if layer.layer_type == "Linear":
                layers_out.append({"layer": "Linear",
                                   "in": _int(layer.in_features),
                                   "out": _int(layer.out_features)})
            else:
                layers_out.append({"layer": layer.layer_type})
        return {
            "model_name": self.model_name,
            "type":       "Dense" if self.source == "numpy" else "Sequential",
            "layers":     layers_out,
        }


class TraceCollector:
    def __init__(self):
        self.ops: List[TracedOp] = []

    def record(self, op: TracedOp):
        self.ops.append(op)

    def clear(self):
        self.ops.clear()


# Public — executor.py imports this directly
collector  = TraceCollector()
_collector = collector   # internal alias


def _current_lineno() -> Optional[int]:
    try:
        import tracer as _tracer
        return _tracer.current_lineno
    except Exception:
        return None


# ── TracingArray ──────────────────────────────────────────────────────────

class TracingArray(np.ndarray):
    def __matmul__(self, other):
        result = np.ndarray.__matmul__(self, other)
        _collector.record(TracedOp(kind="matmul", name="@",
            input_shapes=[self.shape, np.shape(other)],
            output_shape=np.shape(result), lineno=_current_lineno()))
        if isinstance(result, np.ndarray) and not isinstance(result, TracingArray):
            result = result.view(TracingArray)
        return result

    def __rmatmul__(self, other):
        result = np.ndarray.__rmatmul__(self, other)
        _collector.record(TracedOp(kind="matmul", name="@",
            input_shapes=[np.shape(other), self.shape],
            output_shape=np.shape(result), lineno=_current_lineno()))
        if isinstance(result, np.ndarray) and not isinstance(result, TracingArray):
            result = result.view(TracingArray)
        return result


def _as_tracing(arr) -> TracingArray:
    return np.asarray(arr).view(TracingArray)


# ── NumPy wrappers ────────────────────────────────────────────────────────

_original_np_dot    = np.dot
_original_np_matmul = np.matmul


def _patched_dot(a, b, out=None):
    result = _original_np_dot(a, b) if out is None else _original_np_dot(a, b, out)
    _collector.record(TracedOp(kind="matmul", name="np.dot",
        input_shapes=[np.shape(a), np.shape(b)],
        output_shape=np.shape(result), lineno=_current_lineno()))
    return result


def _patched_matmul(x1, x2, **kwargs):
    result = _original_np_matmul(x1, x2, **kwargs)
    _collector.record(TracedOp(kind="matmul", name="np.matmul",
        input_shapes=[np.shape(x1), np.shape(x2)],
        output_shape=np.shape(result), lineno=_current_lineno()))
    return result


def _make_activation_wrapper(fn, label):
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        _collector.record(TracedOp(kind="activation", name=label,
                                   lineno=_current_lineno()))
        return result
    wrapper.__name__ = label
    return wrapper


def _make_maximum_wrapper(ufunc):
    def wrapper(x1, x2, **kwargs):
        result = ufunc(x1, x2, **kwargs)
        try:
            if (np.isscalar(x1) and x1 == 0) or (np.isscalar(x2) and x2 == 0):
                _collector.record(TracedOp(kind="activation",
                                           name="np.maximum(ReLU)",
                                           lineno=_current_lineno()))
        except Exception:
            pass
        return result

    for attr in ("reduce", "accumulate", "reduceat", "outer", "at",
                 "nargs", "ntypes", "types", "identity", "nin", "nout"):
        try:
            setattr(wrapper, attr, getattr(ufunc, attr))
        except AttributeError:
            pass
    return wrapper


# ── patch_numpy (PUBLIC context manager) ─────────────────────────────────

def _build_tracing_np():
    np.dot    = _patched_dot
    np.matmul = _patched_matmul
    _orig_tanh    = np.tanh
    _orig_maximum = np.maximum
    np.tanh    = _make_activation_wrapper(_orig_tanh, "np.tanh")
    np.maximum = _make_maximum_wrapper(_orig_maximum)

    _orig_creators = {}
    for name in ("array", "zeros", "ones", "empty", "full",
                 "zeros_like", "ones_like", "empty_like"):
        orig = getattr(np, name)
        _orig_creators[name] = orig
        def _make(orig_fn):
            def wrapped(*a, **kw): return _as_tracing(orig_fn(*a, **kw))
            return wrapped
        setattr(np, name, _make(orig))

    _orig_rand = {}
    for name in ("randn", "rand", "random", "uniform", "normal"):
        if hasattr(np.random, name):
            orig = getattr(np.random, name)
            _orig_rand[name] = orig
            def _make_r(orig_fn):
                def wrapped(*a, **kw): return _as_tracing(orig_fn(*a, **kw))
                return wrapped
            setattr(np.random, name, _make_r(orig))

    return _orig_tanh, _orig_maximum, _orig_creators, _orig_rand


@contextmanager
def patch_numpy():
    _orig_tanh, _orig_maximum, orig_creators, orig_rand = _build_tracing_np()
    try:
        yield
    finally:
        np.dot      = _original_np_dot
        np.matmul   = _original_np_matmul
        np.tanh     = _orig_tanh
        np.maximum  = _orig_maximum
        for name, fn in orig_creators.items():
            setattr(np, name, fn)
        for name, fn in orig_rand.items():
            setattr(np.random, name, fn)


# ── patch_torch (PUBLIC) ──────────────────────────────────────────────────

def patch_torch(sandbox_globals: dict) -> Optional[callable]:
    torch = sandbox_globals.get("torch") or sys.modules.get("torch")
    if torch is None:
        return None

    nn = torch.nn
    hooks = []
    LINEAR_TYPES = {"Linear", "Conv1d", "Conv2d", "Conv3d", "Bilinear"}

    def make_hook(mod_label):
        def hook(module, inputs, output):
            in_shape  = tuple(inputs[0].shape) if inputs else None
            out_shape = tuple(output.shape) if output is not None else None
            cls       = type(module).__name__
            _collector.record(TracedOp(
                kind="matmul" if cls in LINEAR_TYPES else "activation",
                name=f"torch.{cls}",
                input_shapes=[in_shape] if in_shape else [],
                output_shape=out_shape,
                extra={"label": mod_label},
                lineno=_current_lineno(),
            ))
        return hook

    _original_init = nn.Module.__init__

    def patched_init(self_mod, *args, **kwargs):
        _original_init(self_mod, *args, **kwargs)
        h = self_mod.register_forward_hook(make_hook(type(self_mod).__name__))
        hooks.append(h)

    nn.Module.__init__ = patched_init

    def restore():
        nn.Module.__init__ = _original_init
        for h in hooks: h.remove()

    return restore


# ── patch_jax (PUBLIC) ────────────────────────────────────────────────────

def patch_jax() -> Optional[callable]:
    try:
        import jax.numpy as jnp
    except ImportError:
        return None

    _orig_dot    = jnp.dot
    _orig_matmul = jnp.matmul

    def _jax_dot(a, b, **kwargs):
        result = _orig_dot(a, b, **kwargs)
        _collector.record(TracedOp(kind="matmul", name="jnp.dot",
            input_shapes=[getattr(a, 'shape', ()), getattr(b, 'shape', ())],
            output_shape=getattr(result, 'shape', ()), lineno=_current_lineno()))
        return result

    def _jax_matmul(a, b, **kwargs):
        result = _orig_matmul(a, b, **kwargs)
        _collector.record(TracedOp(kind="matmul", name="jnp.matmul",
            input_shapes=[getattr(a, 'shape', ()), getattr(b, 'shape', ())],
            output_shape=getattr(result, 'shape', ()), lineno=_current_lineno()))
        return result

    jnp.dot    = _jax_dot
    jnp.matmul = _jax_matmul

    def restore():
        jnp.dot    = _orig_dot
        jnp.matmul = _orig_matmul

    return restore


# ── patch_equinox (PUBLIC) ────────────────────────────────────────────────

def patch_equinox() -> Optional[callable]:
    try:
        import equinox as eqx
        import jax.nn as jax_nn
    except ImportError:
        return None

    _orig_linear_call = eqx.nn.Linear.__call__
    _orig_relu        = jax_nn.relu

    def patched_linear_call(self, x, **kwargs):
        result = _orig_linear_call(self, x, **kwargs)
        _collector.record(TracedOp(kind="matmul", name="eqx.Linear",
            input_shapes=[getattr(x, 'shape', ())],
            output_shape=getattr(result, 'shape', ()),
            lineno=_current_lineno()))
        return result

    def patched_relu(x):
        result = _orig_relu(x)
        _collector.record(TracedOp(kind="activation", name="ReLU",
                                   lineno=_current_lineno()))
        return result

    eqx.nn.Linear.__call__ = patched_linear_call
    jax_nn.relu             = patched_relu

    def restore():
        eqx.nn.Linear.__call__ = _orig_linear_call
        jax_nn.relu             = _orig_relu

    return restore


# ── Activation normalisation ──────────────────────────────────────────────

_ACTIVATION_NORMALIZE = {
    "np.tanh": "Tanh", "np.exp": None,
    "np.maximum(relu)": "ReLU", "@relu": "ReLU",
    "tanh": "Tanh", "relu": "ReLU",
    "sigmoid": "Sigmoid", "softmax": "Softmax",
}


def _normalize_activation(raw_name: str) -> Optional[str]:
    key = raw_name.lower()
    for k, v in _ACTIVATION_NORMALIZE.items():
        if k in key:
            return v
    return raw_name.split(".")[-1].capitalize()


# ── Pattern analysis ──────────────────────────────────────────────────────

def _shape_to_features(in_shape, out_shape):
    in_f  = in_shape[-1]  if in_shape  and len(in_shape)  >= 1 else None
    out_f = out_shape[-1] if out_shape and len(out_shape) >= 1 else None
    return in_f, out_f


def analyze_ops(ops: List[TracedOp]) -> Optional[DetectedModel]:
    return (_analyze_torch_trace(ops) or
            _analyze_equinox_trace(ops) or
            _analyze_numpy_trace(ops))


def _analyze_numpy_trace(ops):
    ops = [op for op in ops if not op.name.startswith(("eqx.", "torch.", "jnp."))]
    if not any(op.kind == "matmul" for op in ops):
        return None
    layers = []
    for op in ops:
        if op.kind == "matmul":
            in_f, out_f = _shape_to_features(
                op.input_shapes[0] if op.input_shapes else None, op.output_shape)
            layers.append(DetectedLayer("Linear", in_f, out_f))
        elif op.kind == "activation":
            act_name = _normalize_activation(op.name)
            if act_name is None: continue
            if not layers or layers[-1].layer_type != act_name:
                layers.append(DetectedLayer(act_name))
    if not any(l.layer_type == "Linear" for l in layers):
        return None
    return DetectedModel("TracedDenseNetwork", "numpy", layers)


def _analyze_torch_trace(ops):
    torch_ops = [op for op in ops if op.name.startswith("torch.")]
    if not torch_ops: return None
    CONTAINERS = {"Sequential", "ModuleList", "ModuleDict"}
    layers = []
    for op in torch_ops:
        cls = op.name.replace("torch.", "")
        if cls in CONTAINERS: continue
        if op.kind == "matmul":
            in_f, out_f = _shape_to_features(
                op.input_shapes[0] if op.input_shapes else None, op.output_shape)
            layers.append(DetectedLayer(cls, in_f, out_f))
        else:
            if not layers or layers[-1].layer_type != cls:
                layers.append(DetectedLayer(cls))
    if not layers: return None
    return DetectedModel("TracedTorchNetwork", "torch", layers)


def _analyze_equinox_trace(ops):
    if not any(op.name.startswith("eqx.") for op in ops): return None
    layers = []
    for op in ops:
        if op.name == "eqx.Linear":
            in_f  = op.input_shapes[0][-1] if op.input_shapes and op.input_shapes[0] else None
            out_f = op.output_shape[-1] if op.output_shape else None
            layers.append(DetectedLayer("Linear", in_f, out_f))
        elif op.kind == "activation" and op.name in ("ReLU", "Tanh", "Sigmoid", "Softmax"):
            if not layers or layers[-1].layer_type != op.name:
                layers.append(DetectedLayer(op.name))
    if not layers: return None
    return DetectedModel("TracedEquinoxNetwork", "numpy", layers)


# ── ops_by_lineno (PUBLIC) ────────────────────────────────────────────────

def ops_by_lineno(ops: List[TracedOp]) -> dict:
    """{ lineno: [op_dict, ...] } — used by executor.py to attach nn_ops to steps."""
    result = {}
    for op in ops:
        if op.lineno is None: continue
        entry = {
            "kind": op.kind,
            "name": op.name,
            "in":   [list(s) for s in op.input_shapes] if op.input_shapes else [],
            "out":  list(op.output_shape) if op.output_shape else [],
        }
        result.setdefault(op.lineno, []).append(entry)
    return result


# ── Backwards-compatible trace_and_extract ────────────────────────────────

def _build_sandbox() -> dict:
    import math, random
    globs = {"__builtins__": __builtins__, "np": np, "numpy": np,
             "math": math, "random": random}
    try:
        import torch, torch.nn as nn
        globs["torch"] = torch; globs["nn"] = nn
    except ImportError:
        pass
    try:
        import jax, jax.numpy as jnp, equinox as eqx
        globs.update({"jax": jax, "jnp": jnp, "eqx": eqx})
    except ImportError:
        pass
    return globs


def trace_and_extract(code: str) -> List[dict]:
    """Backwards-compatible: runs code a second time. Use patch_* directly for line-by-line."""
    _collector.clear()
    globs = _build_sandbox()
    torch_restore = patch_torch(globs)
    jax_restore   = patch_jax()
    eqx_restore   = patch_equinox()
    with patch_numpy():
        try:
            exec(compile(code, "<nn_code>", "exec"), globs)
        except Exception as e:
            print(f"[nn_runtime_tracer] warning: {e}", file=sys.stderr)
    if torch_restore: torch_restore()
    if jax_restore:   jax_restore()
    if eqx_restore:   eqx_restore()
    model = analyze_ops(_collector.ops)
    result = [model.to_dict()] if model else []
    _collector.clear()
    return result