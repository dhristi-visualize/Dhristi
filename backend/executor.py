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
from nn_extractor import extract_sequential_models
from imports import STDLIB_MODULES

printed_output = []

def traced_print(*args, **kwargs):
    text = " ".join(str(a) for a in args)

    printed_output.append({
        "lineno" : tracer.current_lineno,
        "text" : text
    })

    sys.__stdout__.write(text + "\n")

def run_code(code):
    tracer.execution_log.clear()
    tracer.last_line = None
    printed_output.clear()

    formula_map = find_candidate_expressions(code)
    nn_models = extract_sequential_models(code)

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

        sys.settrace(tracer.tracer)
        try:
            exec(compiled, sandbox_globals, sandbox_globals)
        finally:
            sys.settrace(None)


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

        # Add code lines
        code_lines = code.split('\n')
        for step in tracer.execution_log:
            if step.get("event") == "line":
                step["stdout"] = [
                    o["text"]
                    for o in printed_output
                    if o["lineno"] == step["lineno"]
                ]
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
                    ss[key] = {name: safe_json(val) for name, val in s[key].items()}
            
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

        return {
            "success": True, 
            "steps": safe_steps, 
            "nn_models" : nn_models
        }

    except Exception as e:
        sys.settrace(None)
        return {
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc()
        }