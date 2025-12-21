import sys
import math
import numpy as np
import torch
import sympy as sp
import traceback

from tracer import tracer, state
from ast_utils import find_candidate_expressions
from serializer import safe_json

def run_code(code):
    state["execution_log"] = []
    state["last_line"] = None

    formula_map = find_candidate_expressions(code)

    try:
        compiled = compile(code, "<user_code>", "exec")
        sandbox_globals = {
            "__name__": "__main__",
            "np": np,
            "torch": torch,
            "sp": sp,
            "math": math,
            "__builtins__": __builtins__
        }
        
        sys.settrace(tracer)
        try:
            exec(compiled, sandbox_globals, sandbox_globals)
        finally:
            sys.settrace(None)

            if state["execution_log"]:
                final_locals = {}
                for entry in reversed(state["execution_log"]):
                    if entry.get("after") and entry["event"] == "line":
                        final_locals = entry["after"]
                        break
                    elif entry.get("before") and entry["event"] == "line":
                        final_locals = entry["before"]
                        break
                
                for entry in reversed(state["execution_log"]):
                    if entry.get("event") == "line" and entry.get("after") is None:
                        entry["after"] = final_locals
                        break

        # Add code lines
        code_lines = code.split('\n')
        for step in state["execution_log"]:
            ln = step.get("lineno")
            if isinstance(ln, int) and 1 <= ln <= len(code_lines):
                step['code'] = code_lines[ln - 1]
            else:
                step['code'] = None

        # Convert to JSON-safe format
        safe_steps = []
        for s in state["execution_log"]:
            ss = {
                "event": s.get("event"),
                "func": s.get("func"),
                "lineno": s.get("lineno"),
                "code": s.get("code")
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

        return {"success": True, "steps": safe_steps}

    except Exception as e:
        sys.settrace(None)
        return {
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc()
        }