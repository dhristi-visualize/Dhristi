import sys
import copy
import math
import types

execution_log = []
last_line = None
current_lineno = None
call_stack = [] # track function calls
call_tree = [] # store recursive call tree
call_counter = 0 # unique id for each call

def tracer(frame, event, arg):
    global last_line
    global call_counter 
    current_call_id = call_stack[-1]["call_id"] if call_stack else None


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
            if callable(v) and not hasattr(v, '__dict__'): # -> to check if an object can be called (checking if v is callable, if it is, then continue)
                continue
            if isinstance(v, types.ModuleType):
                continue
            if isinstance(v, type): # -> checks whether an object or variable is an instance of a specified type or class. (checks whether v is of type math)
                continue
            # if hasattr(v, '__module__') and v.__module__ == '__future__':
            #     continue
            cleaned[k] = v
        return cleaned

    def snap_locals():
        try:
            # raw = copy.deepcopy(frame.f_locals)
            raw = dict(frame.f_locals)
        except Exception:
            raw = {}
        return clean_vars(raw)
        
    if event == "call":
        func_name = frame.f_code.co_name
        lineno = frame.f_lineno

        call_id = call_counter
        call_counter = call_counter + 1

        parent_id = call_stack[-1]["call_id"] if call_stack else None

        call_info = {
            "call_id" : call_id,
            "func" : func_name,
            "lineno" : lineno,
            "args" : snap_locals(),
            "parent_id" : parent_id,
            "return_value" : None,
            "step_index" : len(execution_log)
        }

        call_stack.append(call_info)
        call_tree.append(call_info)

        execution_log.append({
            "event": "call",
            "func": func_name,
            "lineno": lineno,
            "before": snap_locals(),
            "after": None, 
            "code": None,
            "call_id" : call_id
        })
        return tracer
    
    if event == "line":
        global current_lineno
        # providing "after" state for the PREVIOUS line
        if last_line is not None and execution_log:
            after = snap_locals()
            for entry in reversed(execution_log):
                if entry.get("lineno") == last_line and entry.get("after") is None:
                    entry["after"] = after
                    break

        # log the CURRENT line (with "before" state)
        last_line = frame.f_lineno
        current_lineno = last_line
        
        before = snap_locals()
        execution_log.append({
            "event": "line",
            "before": before,
            "lineno": last_line,
            "after": None, 
            "code": None,
            "func": frame.f_code.co_name, 
            "call_id" : current_call_id
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
                if entry.get("event") == "line" and entry.get("after") is None:
                    entry["after"] = after
                    break
        
        ret = arg
        lineno = frame.f_lineno

        if call_stack:
            call_info = call_stack.pop()
            call_info["return_value"] = ret
            call_info["return_step"] = len(execution_log)

            #find and update the same object in call_tree
            # its already there by reference, but being explicit

            for ct_call in call_tree:
                if ct_call["call_id"] == call_info["call_id"]:
                    ct_call["return_value"] = ret
                    ct_call["return_step"] = len(execution_log)
                    break

        execution_log.append({
            "event": "return",
            "lineno": lineno,
            "func": frame.f_code.co_name,
            "return_value": ret, 
            "before": None,
            "after": None,
            "code": None, 
            "call_id" : current_call_id
        })
        return tracer
    
    return tracer