import ast
import sympy as sp

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