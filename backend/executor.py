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
from nn_extractor import extract_sequential_models, extract_manual_dense_layers, extract_weight_stack_dense, extract_keras_functional
from recursion_detector import extract_recursive_function
from nn_runtime_tracer import trace_and_extract
from imports import STDLIB_MODULES

# At the top of executor.py — wrap in try/except since these may not be installed
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
        # Store with execution index (how many line events we've seen)
        printed_output.append({
            "lineno": lineno,
            "text": text,
            "step_index": len(tracer.execution_log) - 1  # Current step
        })

    sys.__stdout__.write(text + "\n")

# AFTER — sanitize call_tree before returning:
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
    tracer.last_line = None
    tracer.current_lineno = None
    tracer.call_stack.clear()
    tracer.call_counter = 0
    tracer.call_tree.clear()
    printed_output.clear()


    formula_map = find_candidate_expressions(code)
    nn_models = []

    # Highest confidence: explicit framework models
    seq = extract_sequential_models(code)
    if seq:
        nn_models = seq
    else:
        keras_models = extract_keras_functional(code)
        if keras_models:
            nn_models = keras_models
        else:
            # Static weight-stack inference (MULTI-LAYER)
            stack = extract_weight_stack_dense(code)
            if stack:
                nn_models = stack

            else:
                # Heuristic fallback (SINGLE-LAYER)
                manual = extract_manual_dense_layers(code)
                if manual:
                    nn_models = manual

    recursive_funcs = extract_recursive_function(code)

    safe_builtins = dict(__builtins__)
    safe_builtins["print"] = traced_print

    try:
        future_flags = get_future_flags(code)
        compiled = compile(code, "<user_code>", "exec", flags=future_flags, dont_inherit=True)
        sandbox_globals = {
            "__name__": "__main__",
            "__builtins__": safe_builtins,
            #Scientific computing
            "np": np,
            "torch": torch,
            "sp": sp,
            "math": math,
            #Standard library
            **STDLIB_MODULES
        }

        # Add optional frameworks only if available
        if jax is not None:
            sandbox_globals.update({"jax": jax, "jnp": jnp})
        if eqx is not None:
            sandbox_globals["eqx"] = eqx
        if keras is not None:
            sandbox_globals["keras"] = keras
        if tf is not None:
            sandbox_globals["tf"] = tf

        sys.settrace(tracer.tracer)
        try:
            exec(compiled, sandbox_globals, sandbox_globals)
        finally:
            sys.settrace(None)
        
            if not nn_models:
                try:
                    runtime_models = trace_and_extract(code)
                    if runtime_models:
                        nn_models = runtime_models
                except Exception:
                    pass   # never let tracer crash the main response

            if tracer.execution_log:
                final_locals = {}
                for k, v in sandbox_globals.items():
                    if not k.startswith("__") and not isinstance(v, types.ModuleType):
                        final_locals[k] = v
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

        # lines = code.rstrip().split("\n")
        # last = lines[-1]

        # if last and not last.startswith(("return", "print")):
        #     lines[-1] = f"__expr_result__ = {last}"

        # code = "\n".join(lines)

        # Add code lines and match prints to specific step indices
        code_lines = code.split('\n')
        for idx, step in enumerate(tracer.execution_log):
            ln = step.get("lineno")
            if isinstance(ln, int) and 1 <= ln <= len(code_lines):
                step['code'] = code_lines[ln - 1]
            else:
                step['code'] = None
            
            # Add stdout for THIS specific execution of this line
            if step.get("event") == "line":
                step["stdout"] = [
                    p["text"] 
                    for p in printed_output 
                    if p["step_index"] == idx
                ]
            else:
                step["stdout"] = []
        '''
        {
            "event": "line",
            "lineno": 5,
            "before": {...},
            "after": {...},
            "stdout": ["Starting execution..."]
            }
        '''

        # Convert to JSON-safe format
        safe_steps = []
        for s in tracer.execution_log:
            ss = {
                "event": s.get("event"),
                "func": s.get("func"),
                "lineno": s.get("lineno"),
                "code": s.get("code"),
                "stdout" : s.get("stdout", [])
            }
            
            # Process before/after states
            for key in ("before", "after"):
                if s.get(key) is None:
                    ss[key] = None
                else:
                    seen = set()
                    ss[key] = {name: safe_json(val, seen=seen) for name, val in s[key].items()}
            
            # Process return value
            if "return_value" in s:
                ss["return_value"] = safe_json(s["return_value"])
            
            # Add formula if exists
            ln = s.get("lineno")
            if ln and ln in formula_map:
                ss["formula"] = formula_map[ln]
            else:
                ss["formula"] = None
            
            safe_steps.append(ss)
        
        for m in nn_models:
            try:
                X = sandbox_globals.get(m["input"])
                W = sandbox_globals.get(m["weights"])
                b = sandbox_globals.get(m.get("biases"))

                # ---- NUMPY / MATRIX ----
                if isinstance(W, list) and isinstance(W[0], list):
                    m["type"] = "manual_dense"
                    m["input_size"] = len(X)
                    m["output_size"] = len(W)
                    m["weights"] = W
                    m["biases"] = b if isinstance(b, list) else [0]*len(W)

                # ---- SINGLE NEURON ----
                elif isinstance(W, list):
                    m["type"] = "manual_dense"
                    m["input_size"] = len(X)
                    m["output_size"] = 1
                    m["weights"] = [W]
                    m["biases"] = [b] if b is not None else [0]

            except Exception:
                continue

        return {
            "success":        True,
            "steps":          safe_steps,
            "nn_models":      nn_models,
            "call_tree":      _sanitize_call_tree(tracer.call_tree),
            "recursive_funcs": recursive_funcs
        }

    except Exception as e:
        sys.settrace(None)
        return {
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc()
        }