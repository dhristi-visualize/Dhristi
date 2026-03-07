import sys
import math
import numpy as np
import torch
import sympy as sp
import traceback
import types

import tracer
from ast_utils import find_candidate_expressions, get_future_flags
from serializer import safe_json
from nn_extractor import (extract_sequential_models, extract_manual_dense_layers,
                          extract_weight_stack_dense, extract_keras_functional)
from recursion_detector import extract_recursive_function
from nn_runtime_tracer import (
    collector as nn_collector,
    patch_numpy, patch_torch, patch_jax, patch_equinox,
    analyze_ops, ops_by_lineno,
)
from imports import STDLIB_MODULES

try:
    import jax
    import jax.numpy as jnp
    import equinox as eqx
except ImportError:
    jax = jnp = eqx = None

try:
    import keras
except ImportError:
    keras = None

try:
    import tensorflow as tf
except ImportError:
    tf = None

printed_output = []


def traced_print(*args, **kwargs):
    text = " ".join(str(a) for a in args)
    lineno = tracer.current_lineno
    if lineno is not None:
        printed_output.append({
            "lineno":     lineno,
            "text":       text,
            "step_index": len(tracer.execution_log) - 1,
        })
    sys.__stdout__.write(text + "\n")


def _sanitize_call_tree(tree):
    result = []
    for call in tree:
        seen = set()
        result.append({
            "call_id":      call.get("call_id"),
            "func":         call.get("func"),
            "lineno":       call.get("lineno"),
            "parent_id":    call.get("parent_id"),
            "step_index":   call.get("step_index"),
            "return_step":  call.get("return_step"),
            "args":         {k: safe_json(v, seen=seen)
                             for k, v in (call.get("args") or {}).items()},
            "return_value": safe_json(call.get("return_value"), seen=seen),
        })
    return result


def run_code(code):
    tracer.execution_log.clear()
    tracer.last_line      = None
    tracer.current_lineno = None
    tracer.call_stack.clear()
    tracer.call_counter   = 0
    tracer.call_tree.clear()
    printed_output.clear()
    nn_collector.clear()

    formula_map = find_candidate_expressions(code)
    nn_models   = []

    # AST-based extraction
    seq = extract_sequential_models(code)
    if seq:
        nn_models = seq
    else:
        keras_models = extract_keras_functional(code)
        if keras_models:
            nn_models = keras_models
        else:
            stack = extract_weight_stack_dense(code)
            if stack:
                nn_models = stack
            else:
                manual = extract_manual_dense_layers(code)
                if manual:
                    nn_models = manual

    recursive_funcs = extract_recursive_function(code)

    safe_builtins = dict(__builtins__)
    safe_builtins["print"] = traced_print

    torch_restore = None
    jax_restore   = None
    eqx_restore   = None

    try:
        future_flags = get_future_flags(code)
        compiled = compile(code, "<user_code>", "exec",
                           flags=future_flags, dont_inherit=True)

        sandbox_globals = {
            "__name__":     "__main__",
            "__builtins__": safe_builtins,
            "np":           np,
            "torch":        torch,
            "sp":           sp,
            "math":         math,
            **STDLIB_MODULES,
        }

        if jax is not None:
            sandbox_globals.update({"jax": jax, "jnp": jnp})
        if eqx is not None:
            sandbox_globals["eqx"] = eqx
        if keras is not None:
            sandbox_globals["keras"] = keras
        if tf is not None:
            sandbox_globals["tf"] = tf

        # Apply NN patches BEFORE exec so they fire during the main run
        # and tracer.current_lineno is accurate for every recorded op.
        torch_restore = patch_torch(sandbox_globals)
        jax_restore   = patch_jax()
        eqx_restore   = patch_equinox()

        sys.settrace(tracer.tracer)
        try:
            with patch_numpy():
                exec(compiled, sandbox_globals, sandbox_globals)
        finally:
            sys.settrace(None)
            if torch_restore: torch_restore()
            if jax_restore:   jax_restore()
            if eqx_restore:   eqx_restore()

        # Build NN model from runtime ops if AST found nothing
        if not nn_models and nn_collector.ops:
            model = analyze_ops(nn_collector.ops)
            if model:
                nn_models = [model.to_dict()]

        # Final-locals fill-in
        if tracer.execution_log:
            final_locals = {
                k: v for k, v in sandbox_globals.items()
                if not k.startswith("__") and not isinstance(v, types.ModuleType)
            }
            for entry in reversed(tracer.execution_log):
                if entry.get("after") and entry["event"] == "line":
                    final_locals = entry["after"]
                    break
                elif entry.get("before") and entry["event"] == "line":
                    final_locals = entry["before"]
                    break

            for entry in reversed(tracer.execution_log):
                if entry.get("event") == "line" and entry.get("after") is None:
                    entry["after"] = final_locals
                    break

        # Build nn_ops_map: lineno -> list of op dicts
        nn_ops_map = ops_by_lineno(nn_collector.ops)

        # Stamp layer_index onto matmul ops so frontend knows which layer to highlight
        if nn_models:
            model_layers  = nn_models[0].get("layers", [])
            linear_layers = [l for l in model_layers if l.get("layer") == "Linear"]
            matmul_ops    = [op for op in nn_collector.ops if op.kind == "matmul"]
            lineno_to_layer_idx = {}
            for i, op in enumerate(matmul_ops):
                if i < len(linear_layers) and op.lineno is not None:
                    lineno_to_layer_idx[op.lineno] = i

            for lineno, op_list in nn_ops_map.items():
                for op_dict in op_list:
                    if op_dict["kind"] == "matmul":
                        op_dict["layer_index"] = lineno_to_layer_idx.get(lineno)

        # Annotate steps
        code_lines = code.split("\n")
        for idx, step in enumerate(tracer.execution_log):
            ln = step.get("lineno")
            step["code"]   = code_lines[ln - 1] if isinstance(ln, int) and 1 <= ln <= len(code_lines) else None
            step["stdout"] = [p["text"] for p in printed_output if p["step_index"] == idx] \
                             if step.get("event") == "line" else []

        # Serialize steps — attach nn_ops to each step
        safe_steps = []
        for s in tracer.execution_log:
            ss = {
                "event":   s.get("event"),
                "func":    s.get("func"),
                "lineno":  s.get("lineno"),
                "code":    s.get("code"),
                "stdout":  s.get("stdout", []),
                "nn_ops":  nn_ops_map.get(s.get("lineno"), []),
            }

            for key in ("before", "after"):
                if s.get(key) is None:
                    ss[key] = None
                else:
                    seen = set()
                    ss[key] = {name: safe_json(val, seen=seen)
                               for name, val in s[key].items()}

            if "return_value" in s:
                ss["return_value"] = safe_json(s["return_value"])

            ln = s.get("lineno")
            ss["formula"] = formula_map.get(ln) if ln else None

            safe_steps.append(ss)

        # Legacy AST model enrichment
        for m in nn_models:
            try:
                X = sandbox_globals.get(m.get("input"))
                W = sandbox_globals.get(m.get("weights"))
                b = sandbox_globals.get(m.get("biases"))

                if isinstance(W, list) and isinstance(W[0], list):
                    m["type"]        = "manual_dense"
                    m["input_size"]  = len(X)
                    m["output_size"] = len(W)
                    m["weights"]     = W
                    m["biases"]      = b if isinstance(b, list) else [0] * len(W)
                elif isinstance(W, list):
                    m["type"]        = "manual_dense"
                    m["input_size"]  = len(X)
                    m["output_size"] = 1
                    m["weights"]     = [W]
                    m["biases"]      = [b] if b is not None else [0]
            except Exception:
                continue

        return {
            "success":         True,
            "steps":           safe_steps,
            "nn_models":       nn_models,
            "call_tree":       _sanitize_call_tree(tracer.call_tree),
            "recursive_funcs": recursive_funcs,
        }

    except Exception as e:
        sys.settrace(None)
        if torch_restore: torch_restore()
        if jax_restore:   jax_restore()
        if eqx_restore:   eqx_restore()
        return {
            "success":   False,
            "error":     str(e),
            "traceback": traceback.format_exc(),
        }