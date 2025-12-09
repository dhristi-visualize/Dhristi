import sys
import copy

execution_log = []
last_line = None

def tracer(frame, event, arg):
    global last_line

    if frame.f_globals.get("__name__") != "__main__":
        return tracer
    
    frame.f_trace_opcodes = True
    
    if event == "line":
        last_line = frame.f_lineno
        snapshot_before = copy.deepcopy(frame.f_locals)
        execution_log.append({
            "before" : snapshot_before,
            "lineno" : last_line,
            "after" : None
        })

    if event == "opcode" and frame.f_lineno == last_line: 
        snapshot_after = copy.deepcopy(frame.f_locals)
        execution_log[-1]["after"] = snapshot_after
        
        # print(f"Executing line : {lineno} : {local_vars}")
    return tracer

'''
frame - 
a frame object representing the current execution frame(like a stack frame). It has attributes such as : 
1. frame.f_lineno -> the ucrrent line number (an integer)
2. frame.f_locals -> a dict of local variables in that frame(names -> values)
3. frame.f_code -> code object, etc

event - 
a string telling why Python called the tracer. Common values : 
1. call -> a function is called. 
2. line -> the interpreter is about to execute a new source line
3. return -> a function is returning
4. exception -> an exception was raised
5. opcode -> per-bytecode instruction, not always delivered.

arg - 
additional event data(ex : return value for "return")

frame.f_lineno -
this is the line number of the next source line to execute WITHIN THE CODE OBJECT that is running. 
when I exec() a multi-line string, line numbers are relative to that string(starting at 1).

frame.f_locals -
a dictionary of the frame's local variables and their current values. It shoes the state RIGHT NOW, at the moment the trace event is fired. 

Output ->
Executing line : 1 : {'code': 'list1 = [1,2,3]\nlist2 = [4,5,6]\nlist1.extend(list2)\n'}
Executing line : 2 : {'code': 'list1 = [1,2,3]\nlist2 = [4,5,6]\nlist1.extend(list2)\n', 'list1': [1, 2, 3]}
Executing line : 3 : {'code': 'list1 = [1,2,3]\nlist2 = [4,5,6]\nlist1.extend(list2)\n', 'list1': [1, 2, 3], 'list2': [4, 5, 6]}

'''

def run_code(code):
    global execution_log, last_line
    execution_log = []
    last_line = None

    compiled = compile(code, "<user_code>", "exec")

    sys.settrace(tracer)
    exec(compiled, {"__name__" : "__main__"}, {})
    sys.settrace(None)


'''
exec function is am in-built function used for the dynamic execution of python code. 
Dyanmic code execution means, it allows for the execution of python code that is generated ot determined during runtime, rather than being hardcoded. 
'''


code = '''
list1 = [1,2,3]
list2 = [4,5,6]
list1.extend(list2)
'''

run_code(code)

for step, snap in enumerate(execution_log, start=1):
    print(f"\nSTEP {step}: executing line {snap['lineno']}:")
    for name, value in snap["after"].items():
        print(f"   {name} = {value}")

'''
TRACING :

run_code() frame created
|
sys.settrace(tracer)  ← tells Python: “call tracer on every event now”
|
exec(code) is about to run → Python calls tracer("call") for the exec frame
|
exec begins executing line 1 → tracer("line") is called
|
line 1 executed → create list1
|
line 2 → tracer("line") is called
|
line 3 → tracer("line") is called
|
exec finishes → tracer("return") is called
|
sys.settrace(None) stops tracing


Step A - 
Enter run_code: 

FRAME is like - 

CALL STACK
--------------------------------
| Frame: run_code              |
| locals = { 'code': '...' }   |
--------------------------------

Step B - 
call exec(code) -> python creates a new frame for the code string 
There is no new frame created per line.
A frame is created per function call, not per statement.

CALL STACK
--------------------------------
| Frame: your_code (exec)      |
| locals = { }                 |
--------------------------------
| Frame: run_code              |
| locals = { code: '...' }     |
--------------------------------

STEP C - 
Python executes each line inside the exec frame

line 1 - list1 = [1, 2, 3]
locals = { 'list1' : [1, 2, 3]}

line 2 - list2 = [4, 5, 6]
locals = {
            'list1' : [1, 2, 3],
            'list2' : [4, 5, 6]
        }

line 3 - list1.extend(list2)
locals = {
            'list1' : [1, 2, 3, 4, 5, 6]
            'list2' : [4, 5, 6]
        }

so the final frame is like - 

CALL STACK
--------------------------------
| Frame: your_code (exec)      |
| locals = {}                  |  <- before line 1
| locals = {list1: [...] }     |  <- after line 1
| locals = {list1, list2}      |  <- after line 2
| locals = {list1 extended}    |  <- after line 3
--------------------------------
| Frame: run_code              |
| locals = { code: "..." }     |
--------------------------------



'''