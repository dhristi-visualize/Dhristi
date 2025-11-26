import sys

def tracer(frame, event, arg):
    if event in ("line", "opcode"):
        lineno = frame.f_lineno
        local_vars = frame.f_locals
        print(f"Executing line : {lineno} : {local_vars}")

    return tracer

def run_code(code):
    sys.settrace(tracer)
    exec(code)
    sys.settrace(None)

code = '''list1 = [1,2,3]
list2 = [4,5,6]
list1.extend(list2)
'''

run_code(code)