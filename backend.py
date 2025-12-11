from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import copy
import traceback
import inspect
import json

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

    def snap_locals():
        try:
            return copy.deepcopy(frame.f_locals)
        except Exception:
            return dict(frame.f_locals)
        
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

def safe_json(value):
    try:
        return json.loads(json.dumps(value, default=lambda o: repr(o)))
    except:
        return repr(value)

def run_code(code):
    global execution_log, last_line
    execution_log = []
    last_line = None

    try:
        compiled = compile(code, "<user_code>", "exec")
        sys.settrace(tracer)
        try:
            exec(compiled, {"__name__" : "__main__"}, {})
        finally:
            sys.settrace(None)

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

