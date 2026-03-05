"""
nn_runtime_tracer.py

Detects neural networks by EXECUTING code and tracing matrix multiplications
chained with nonlinearities at runtime.

Supports:
  - Raw NumPy: np.dot, np.matmul, AND the @ operator
  - Manual loops over weight matrices
  - PyTorch nn.Sequential / custom nn.Module (forward hooks)

Key design decisions:
  - np.dot / np.matmul are monkey-patched at the module level (works because
    Python resolves np.dot via the module __dict__ at call time).
  - The @ operator dispatches through ndarray.__matmul__ at the C level and
    bypasses the module-level patch. Fix: arrays created inside the sandbox
    are instances of TracingArray (an ndarray subclass) whose __matmul__
    records the op and preserves the subclass through the result.
  - np.exp is deliberately suppressed (it appears inside sigmoid internals
    and would create a spurious "Exp" layer).
"""

import sys
import types
import traceback
import numpy as np
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class TracedOp:
    kind: str                          # "matmul" | "activation"
    name: str                          # "np.dot", "@", "torch.Linear", …
    input_shapes: List[Tuple] = field(default_factory=list)
    output_shape: Optional[Tuple] = None
    extra: dict = field(default_factory=dict)


@dataclass
class DetectedLayer:
    layer_type: str                    # "Linear", "ReLU", "Sigmoid", …
    in_features: Optional[int] = None
    out_features: Optional[int] = None


@dataclass
class DetectedModel:
    model_name: str
    source: str                        # "numpy" | "torch"
    layers: List[DetectedLayer] = field(default_factory=list)

    def to_dict(self):
        """
        Returns schema expected by executor.py and NeuralNetworkVisualization.jsx:
          { model_name, type, layers: [{layer, in?, out?}] }
        All numeric values are cast to plain Python int so Flask's JSON
        encoder never sees numpy.int64 / numpy.intp etc.
        """
        def _int(v):
            return int(v) if v is not None else None

        layers_out = []
        for layer in self.layers:
            if layer.layer_type == "Linear":
                layers_out.append({
                    "layer": "Linear",
                    "in":    _int(layer.in_features),
                    "out":   _int(layer.out_features),
                })
            else:
                layers_out.append({"layer": layer.layer_type})
        return {
            "model_name": self.model_name,
            "type":       "Dense" if self.source == "numpy" else "Sequential",
            "layers":     layers_out,
        }


# ---------------------------------------------------------------------------
# Trace collector (module-level singleton, always cleared before each run)
# ---------------------------------------------------------------------------

class TraceCollector:
    def __init__(self):
        self.ops: List[TracedOp] = []

    def record(self, op: TracedOp):
        self.ops.append(op)

    def clear(self):
        self.ops.clear()


_collector = TraceCollector()


# ---------------------------------------------------------------------------
# TracingArray — ndarray subclass that intercepts the @ operator
#
# WHY: numpy's @ dispatches through ndarray.__matmul__ at the C level.
# Patching np.matmul = my_fn only replaces the Python module attribute;
# the C-level __matmul__ still calls the original ufunc directly.
# Solution: make all sandbox arrays instances of TracingArray so that
# a @ b goes through our Python __matmul__ and records the op.
# ---------------------------------------------------------------------------

class TracingArray(np.ndarray):
    """
    ndarray subclass whose __matmul__ (@ operator) records ops.
    All numpy array-creation functions in the sandbox return this type.
    """

    def __matmul__(self, other):
        result = np.ndarray.__matmul__(self, other)
        _collector.record(TracedOp(
            kind="matmul", name="@",
            input_shapes=[self.shape, np.shape(other)],
            output_shape=np.shape(result),
        ))
        # Preserve subclass so chained @ calls (a @ W1 @ W2) keep tracing
        if isinstance(result, np.ndarray) and not isinstance(result, TracingArray):
            result = result.view(TracingArray)
        return result

    def __rmatmul__(self, other):
        result = np.ndarray.__rmatmul__(self, other)
        _collector.record(TracedOp(
            kind="matmul", name="@",
            input_shapes=[np.shape(other), self.shape],
            output_shape=np.shape(result),
        ))
        if isinstance(result, np.ndarray) and not isinstance(result, TracingArray):
            result = result.view(TracingArray)
        return result


def _as_tracing(arr) -> TracingArray:
    """Convert any array-like to a TracingArray."""
    return np.asarray(arr).view(TracingArray)


# ---------------------------------------------------------------------------
# Tracing wrappers for np.dot / np.matmul
# ---------------------------------------------------------------------------

_original_np_dot    = np.dot
_original_np_matmul = np.matmul


def _patched_dot(a, b, out=None):
    result = _original_np_dot(a, b) if out is None else _original_np_dot(a, b, out)
    _collector.record(TracedOp(
        kind="matmul", name="np.dot",
        input_shapes=[np.shape(a), np.shape(b)],
        output_shape=np.shape(result),
    ))
    return result


def _patched_matmul(x1, x2, **kwargs):
    result = _original_np_matmul(x1, x2, **kwargs)
    _collector.record(TracedOp(
        kind="matmul", name="np.matmul",
        input_shapes=[np.shape(x1), np.shape(x2)],
        output_shape=np.shape(result),
    ))
    return result


# ---------------------------------------------------------------------------
# Activation wrappers
# ---------------------------------------------------------------------------

def _make_activation_wrapper(fn, label):
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        _collector.record(TracedOp(kind="activation", name=label))
        return result
    wrapper.__name__ = label
    return wrapper


def _make_maximum_wrapper(ufunc):
    """
    Wrap np.maximum to detect relu(x) = maximum(0, x) calls.

    IMPORTANT: np.maximum is a numpy ufunc. Internal numpy code (e.g. array
    printing, np.max) calls np.maximum.reduce(...) on it. A plain Python
    function has no .reduce attribute, which crashes numpy internals.
    Fix: copy all ufunc attributes (reduce, accumulate, outer, …) onto the
    wrapper so it behaves like a ufunc to callers that inspect it.
    """
    def wrapper(x1, x2, **kwargs):
        result = ufunc(x1, x2, **kwargs)
        try:
            if (np.isscalar(x1) and x1 == 0) or (np.isscalar(x2) and x2 == 0):
                _collector.record(TracedOp(kind="activation", name="np.maximum(ReLU)"))
        except Exception:
            pass
        return result

    # Preserve all ufunc methods so numpy internals don't break
    for attr in ("reduce", "accumulate", "reduceat", "outer", "at",
                 "nargs", "ntypes", "types", "identity", "nin", "nout"):
        try:
            setattr(wrapper, attr, getattr(ufunc, attr))
        except AttributeError:
            pass

    return wrapper


# ---------------------------------------------------------------------------
# Sandbox numpy module
#
# We build a lightweight proxy module that:
#   1. Has dot/matmul/maximum/tanh patched for tracing
#   2. Has array-creation functions (randn, zeros, ones, array, …) that
#      return TracingArray so the @ operator is also captured
# ---------------------------------------------------------------------------

def _build_tracing_np():
    np.dot    = _patched_dot
    np.matmul = _patched_matmul
    # np.tanh: save the CURRENT value (the real ufunc) before wrapping
    _orig_tanh = np.tanh
    np.tanh = _make_activation_wrapper(_orig_tanh, "np.tanh")
    # np.maximum: wrap with ufunc-attribute-preserving wrapper
    _orig_maximum = np.maximum
    np.maximum = _make_maximum_wrapper(_orig_maximum)
    # np.exp deliberately NOT patched — appears inside sigmoid internals

    # Wrap array-creation so results are TracingArrays
    _orig_creators = {}
    for name in ("array", "zeros", "ones", "empty", "full",
                 "zeros_like", "ones_like", "empty_like"):
        orig = getattr(np, name)
        _orig_creators[name] = orig
        def _make(orig_fn):
            def wrapped(*a, **kw):
                return _as_tracing(orig_fn(*a, **kw))
            return wrapped
        setattr(np, name, _make(orig))

    # Wrap np.random creation
    _orig_rand = {}
    for name in ("randn", "rand", "random", "uniform", "normal"):
        if hasattr(np.random, name):
            orig = getattr(np.random, name)
            _orig_rand[name] = orig
            def _make_r(orig_fn):
                def wrapped(*a, **kw):
                    return _as_tracing(orig_fn(*a, **kw))
                return wrapped
            setattr(np.random, name, _make_r(orig))

    return _orig_tanh, _orig_maximum, _orig_creators, _orig_rand


@contextmanager
def _patch_numpy():
    """Context manager: apply tracing patches, restore on exit."""
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


# ---------------------------------------------------------------------------
# PyTorch forward hooks
# ---------------------------------------------------------------------------

def _try_patch_torch(sandbox_globals: dict, collector: TraceCollector):
    """
    Registers forward hooks on every nn.Module found after exec().
    Returns (attach_fn, hooks_list).
    attach_fn() must be called BEFORE the forward pass runs (i.e. before exec,
    or by patching nn.Module.__init__ to auto-hook new instances).
    """
    torch = sandbox_globals.get("torch") or sys.modules.get("torch")
    if torch is None:
        return None, []

    nn    = torch.nn
    hooks = []

    LINEAR_TYPES = {"Linear", "Conv1d", "Conv2d", "Conv3d", "Bilinear"}

    def make_hook(mod_label):
        def hook(module, inputs, output):
            in_shape  = tuple(inputs[0].shape) if inputs else None
            out_shape = tuple(output.shape)    if output is not None else None
            cls       = type(module).__name__
            collector.record(TracedOp(
                kind="matmul" if cls in LINEAR_TYPES else "activation",
                name=f"torch.{cls}",
                input_shapes=[in_shape] if in_shape else [],
                output_shape=out_shape,
                extra={"label": mod_label},
            ))
        return hook

    # Patch nn.Module.__init__ so every instance created during exec() gets
    # a hook registered immediately — this solves the timing problem where
    # the forward pass happens inside exec() before we can attach hooks.
    _original_init = nn.Module.__init__

    def patched_init(self_mod, *args, **kwargs):
        _original_init(self_mod, *args, **kwargs)
        label = type(self_mod).__name__
        h = self_mod.register_forward_hook(make_hook(label))
        hooks.append(h)

    nn.Module.__init__ = patched_init

    def restore():
        nn.Module.__init__ = _original_init
        for h in hooks:
            h.remove()

    return restore, hooks


# ---------------------------------------------------------------------------
# Sandbox execution
# ---------------------------------------------------------------------------

def _build_sandbox() -> dict:
    import math, random
    globs: dict = {
        "__builtins__": __builtins__,
        "np": np,
        "numpy": np,
        "math": math,
        "random": random,
    }
    try:
        import torch
        import torch.nn as nn
        globs["torch"] = torch
        globs["nn"]    = nn
    except ImportError:
        pass
    return globs


def _safe_exec(code: str, globs: dict) -> Optional[str]:
    try:
        exec(compile(code, "<nn_code>", "exec"), globs)
        return None
    except Exception:
        return traceback.format_exc()


# ---------------------------------------------------------------------------
# Activation name normalisation
# ---------------------------------------------------------------------------

_ACTIVATION_NORMALIZE = {
    "np.tanh":          "Tanh",
    "np.exp":           None,           # sigmoid internal — suppress
    "np.maximum(relu)": "ReLU",
    "@relu":            "ReLU",         # user-defined relu called before @
    "tanh":             "Tanh",
    "relu":             "ReLU",
    "sigmoid":          "Sigmoid",
    "softmax":          "Softmax",
}


def _normalize_activation(raw_name: str) -> Optional[str]:
    key = raw_name.lower()
    for k, v in _ACTIVATION_NORMALIZE.items():
        if k in key:
            return v
    return raw_name.split(".")[-1].capitalize()


# ---------------------------------------------------------------------------
# Pattern analysis: ops → DetectedModel
# ---------------------------------------------------------------------------

def _shape_to_features(in_shape, out_shape):
    in_f = in_shape[-1]  if in_shape  and len(in_shape)  >= 1 else None
    out_f = out_shape[-1] if out_shape and len(out_shape) >= 1 else None
    return in_f, out_f


def _analyze_numpy_trace(ops: List[TracedOp]) -> Optional[DetectedModel]:
    matmul_ops = [op for op in ops if op.kind == "matmul"]
    if not matmul_ops:
        return None

    layers: List[DetectedLayer] = []
    for op in ops:
        if op.kind == "matmul":
            in_f, out_f = _shape_to_features(
                op.input_shapes[0] if op.input_shapes else None,
                op.output_shape,
            )
            layers.append(DetectedLayer("Linear", in_f, out_f))
        elif op.kind == "activation":
            act_name = _normalize_activation(op.name)
            if act_name is None:
                continue
            if not layers or layers[-1].layer_type != act_name:
                layers.append(DetectedLayer(act_name))

    if not any(l.layer_type == "Linear" for l in layers):
        return None

    return DetectedModel("TracedDenseNetwork", "numpy", layers)


def _analyze_torch_trace(ops: List[TracedOp]) -> Optional[DetectedModel]:
    torch_ops = [op for op in ops if op.name.startswith("torch.")]
    if not torch_ops:
        return None

    # Deduplicate: nn.Module.__init__ hook fires for EVERY submodule
    # (Sequential contains Linear which contains...). Keep leaf ops only
    # by ignoring "Sequential" and "ModuleList" container types.
    CONTAINERS = {"Sequential", "ModuleList", "ModuleDict"}

    layers: List[DetectedLayer] = []
    for op in torch_ops:
        cls = op.name.replace("torch.", "")
        if cls in CONTAINERS:
            continue
        if op.kind == "matmul":
            in_f, out_f = _shape_to_features(
                op.input_shapes[0] if op.input_shapes else None,
                op.output_shape,
            )
            layers.append(DetectedLayer(cls, in_f, out_f))
        else:
            if not layers or layers[-1].layer_type != cls:
                layers.append(DetectedLayer(cls))

    if not layers:
        return None
    return DetectedModel("TracedTorchNetwork", "torch", layers)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def trace_and_extract(code: str) -> List[dict]:
    """
    Execute *code* with runtime tracing active.
    Returns a list of detected models as dicts compatible with executor.py
    and NeuralNetworkVisualization.jsx.

    Returns [] if no neural-network pattern is detected.
    """
    _collector.clear()
    globs = _build_sandbox()

    # PyTorch: patch nn.Module.__init__ BEFORE exec so every module instance
    # created during execution is automatically hooked.
    torch_restore = None
    try:
        import torch  # noqa: F401
        torch_restore, _ = _try_patch_torch(globs, _collector)
    except ImportError:
        pass

    with _patch_numpy():
        err = _safe_exec(code, globs)

    # Restore torch patches
    if torch_restore:
        torch_restore()

    if err:
        print(f"[nn_runtime_tracer] execution warning:\n{err}", file=sys.stderr)

    # Prefer torch trace; fall back to numpy trace
    results = []
    torch_model = _analyze_torch_trace(_collector.ops)
    if torch_model:
        results.append(torch_model.to_dict())
    else:
        numpy_model = _analyze_numpy_trace(_collector.ops)
        if numpy_model:
            results.append(numpy_model.to_dict())

    _collector.clear()
    return results