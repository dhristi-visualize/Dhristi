import sys
import copy
import math

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
            "event": "call",
            "func": func_name,
            "lineno": lineno,
            "before": snap_locals(),
            "after": None, 
            "code": None
        })
        return tracer
    
    if event == "line":
        if last_line is not None and execution_log:
            after = snap_locals()
            for entry in reversed(execution_log):
                if entry.get("lineno") == last_line and entry.get("after") is None:
                    entry["after"] = after
                    break

        last_line = frame.f_lineno
        before = snap_locals()
        execution_log.append({
            "event": "line",
            "before": before,
            "lineno": last_line,
            "after": None, 
            "code": None,
            "func": frame.f_code.co_name
        })
        return tracer

    if event == "opcode":
        if last_line is not None and frame.f_lineno == last_line and execution_log:
            after = snap_locals()
            for entry in reversed(execution_log):
                if entry.get("after") is None:
                    entry["after"] = after
                    break
        return tracer
    
    if event == "return":
        if last_line is not None and execution_log:
            after = snap_locals()
            for entry in reversed(execution_log):
                if entry.get("lineno") == last_line and entry.get("after") is None:
                    entry["after"] = after
                    break
        
        ret = arg
        lineno = frame.f_lineno
        execution_log.append({
            "event": "return",
            "lineno": lineno,
            "func": frame.f_code.co_name,
            "return_value": ret, 
            "before": None,
            "after": None,
            "code": None
        })
        return tracer
    
    return tracer