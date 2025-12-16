from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import copy
import traceback
import inspect
import json
import math 
import ast
import numpy as np
import sympy as sp
import torch

app = Flask(__name__)
CORS(app)

execution_log = []
last_line = None

def tracer(frame, event, arg):
    global last_line 

    if frame.f_globals.get("__name__") != "__main__":
        return tracer
    
    try:
        frame.f_trace_opcodes = True
    except Exception:
        pass

    def clean_vars(variables):
        cleaned = {}
        for k, v in variables.items():
            if k.startswith("__"):
                continue
            if callable(v):
                continue
            if isinstance(v, type(math)):
                continue
            cleaned[k] = v

        return cleaned

    def snap_locals():
        try:
            raw = copy.deepcopy(frame.f_locals)
        except Exception:
            raw = dict(frame.f_locals)
        return clean_vars(raw)
        
    if event == "call":
        func_name = frame.f_code.co_name
        lineno = frame.f_lineno
        execution_log.append({
            "event" : "call",
            "func" : func_name,
            "lineno" : lineno,
            "before" : {k: v for k, v in snap_locals().items()},
            "after" : None, 
            "code" : None
        })
        return tracer
    
    if event == "line":
        if last_line is not None and execution_log:
            after = snap_locals()
            for entry in reversed(execution_log):
                if entry.get("lineno") == last_line and entry.get("after") is None:
                    entry["after"] = {k: v for k, v in after.items()}
                    break

        last_line = frame.f_lineno
        try:
            before = snap_locals()
        except Exception:
            before = dict(frame.f_locals)
        execution_log.append({
            "event" : "line",
            "before" : {k: v for k, v in before.items()},
            "lineno" : last_line,
            "after" : None, 
            "code" : None,
            "func" : frame.f_code.co_name
        })
        return tracer

    if event == "opcode":
        if last_line is not None and frame.f_lineno == last_line and execution_log:
            try:
                after = snap_locals()
            except Exception:
                after = dict(frame.f_locals)

                for entry in reversed(execution_log):
                    if entry.get("after") is None:
                        entry["after"] = {k: v for k, v in after.items()}
                        break
        return tracer
    
    if event == "return":
        if last_line is not None and execution_log:
            after = snap_locals()
            for entry in reversed(execution_log):
                if entry.get("lineno") == last_line and entry.get("after") is None:
                    entry["after"] = {k: v for k, v in after.items()}
                    break
        ret = arg
        lineno = frame.f_lineno
        execution_log.append({
            "event" : "return",
            "lineno" : lineno,
            "func" : frame.f_code.co_name,
            "return_value" : ret, 
            "before" : None,
            "after" : None,
            "code" : None
        })
        return tracer
    
    return tracer

def find_candidate_expressions(source):
    '''
    Docstring for find_candidate_expressions
    Parse source and return mapping lineno -> expression string
    We look for Assign and Return nodes whose value is an expression (BinOp / Call / UnaryOp)
    :param source: Description
    '''
    tree = ast.parse(source)
    formulas = {} #lineno -> {"expr" : stc_str, "latex" : latex_str_or_none}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.Return)):
            val = node.value if isinstance(node, ast.Assign) or isinstance(node, ast.AnnAssign) else node.value
            if val is None:
                continue
            #consider expressions of interest
            if isinstance(val, (ast.BinOp, ast.UnaryOp, ast.Call, ast.BoolOp, ast.Compare)):
                try:
                    src = ast.unparse(val)
                except Exception:
                    #fallback : try to reconstruct minimal string
                    src = "<expr>"
                
                latex = None
                if sp is not None:
                    #try to simplify the expression string into a sympy expression
                    try:
                        sym = sp.sympify(src)
                        latex = sp.latex(sym)
                    except Exception:
                        latex = None

                formulas[getattr(node, "lineno", None)] = {"expr" : src, "latex" : latex}
    
    return formulas


def safe_json(value, max_elements=30):

    try:
        #numpy arrays
        if np is not None and isinstance(value, np.ndarray):
            size = value.size
            info = {
                "type" : "ndarray",
                "values" : value.tolist()
            }
            if size <= max_elements:
                #safe to send full values
                info["values"] = value.tolist()
            else:
                try:
                    flat = value.ravel()
                    info["summary"] = {
                        "size" : int(size),
                        "min" : float(flat.min()),
                        "max" : float(flat.max()),
                        "mean" : float(flat.mean()),
                        "sample" : flat[:min(6, size)].tolist()
                    }
                except Exception:
                    info["repr"] = repr(value)
            return info

        #torch tensors
        if torch is not None and isinstance(value, torch.Tensor):
            t = value
            info = {
                "__torch_tensor__" : True,
                "shape" : list(t.size()),
                "dtype" : str(t.dtype)
            }
            try:
                numel = t.numel()
                if numel <= max_elements:
                    info["values"] = t.cpu().detach().tolist()
                else:
                    flat = t.cpu().detach().view(-1)
                    info["summary"] = {
                        "size" : int(numel),
                        "min" : float(flat.min().item()),
                        "max" : float(flat.max().item()),
                        "mean" : float(flat.float().mean().item()),
                        "sample" : flat[:min(6, numel)].tolist()
                    }
            except Exception:
                info["repr"] = repr(value)
            return info
    
        return json.loads(json.dumps(value, default=lambda o: repr(o)))
    
    except Exception:
        return repr(value)


def run_code(code):
    global execution_log, last_line
    execution_log = []
    last_line = None

    formula_map = find_candidate_expressions(code)

    try:
        compiled = compile(code, "<user_code>", "exec")
        sandbox_globals = {
                "__name__" : "__main__",
                "np" : np,
                "torch" : torch,
                "sp" : sp,
                "math" : math,
                "__builtins__" : __builtins__
            }
        sys.settrace(tracer)
        try:
            exec(compiled, sandbox_globals, sandbox_globals)
        finally:
            sys.settrace(None)

            if execution_log:
                final_locals = {}
                for entry in reversed(execution_log):
                    if entry.get("after") and entry["event"] == "line":
                        final_locals = entry["after"]
                        break
                    elif entry.get("before") and entry["event"] == "line":
                        final_locals = entry["before"]
                        break
                
                for entry in reversed(execution_log):
                    if entry.get("event") == "line" and entry.get("after") is None:
                        entry["after"] = final_locals
                        break

        code_lines = code.split('\n')
        for step in execution_log:
            ln = step.get("lineno")
            if isinstance(ln, int) and 1 <= ln <= len(code_lines):
                step['code'] = code_lines[ln - 1]
            else:
                step['code'] = None

        safe_steps = []
        for s in execution_log:
            ss = {}
            for k, v in s.items():
                if k in ("before", "after"):
                    if v is None:
                        ss[k] = None
                    else:
                        ss[k] = {name : safe_json(val) for name, val in v.items()}
                elif k == "return_value":
                    ss[k] = safe_json(v)
                else:
                    ss[k] = v
            ln = s.get("lineno")
            if ln and ln in formula_map:
                ss["formula"] = formula_map[ln]
            else:
                ss["formula"] = None
            safe_steps.append(ss)

        return {"success" : True, "steps": safe_steps}

    except Exception as e:
        sys.settrace(None)
        return {
            "success" : False, 
            "error" : str(e),
            "traceback" : traceback.format_exc()
        }
    
@app.route('/execute', methods=['POST'])

def execute_code():
    data = request.json
    code = data.get('code', '')

    if not code:
        return jsonify({"success" : False, "error" : "No code provided"}), 400
    
    result = run_code(code)
    return jsonify(result)

@app.route('/health', methods=['GET'])

def health():
    return jsonify({"status" : "ok"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)

