import ast
import sympy as sp
import __future__

def find_candidate_expressions(source):
    try:
        tree = ast.parse(source)
    except:
        return {}
    
    formulas = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.Return)):
            val = node.value if isinstance(node, ast.Assign) or isinstance(node, ast.AnnAssign) else node.value
            if val is None:
                continue
            
            if isinstance(val, (ast.BinOp, ast.UnaryOp, ast.Call, ast.BoolOp, ast.Compare)):
                try:
                    src = ast.unparse(val)
                except:
                    src = "<expr>"
                
                latex = None
                try:
                    sym = sp.sympify(src)
                    latex = sp.latex(sym)
                except:
                    latex = None

                formulas[getattr(node, "lineno", None)] = {"expr": src, "latex": latex}
    
    return formulas

def get_future_flags(code):
    try:
        tree = ast.parse(code)
    except:
        return 0
    
    flags = 0

    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module != "__future__":
            continue

        for alias in node.names:
            feature = alias.name
            if hasattr(__future__, feature):
                flags |= getattr(__future__, feature).compiler_flag

    return flags

