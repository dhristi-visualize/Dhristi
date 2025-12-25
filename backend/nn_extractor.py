import ast

def extract_sequential_models(code: str):
    tree = ast.parse(code)
    models = []

    for node in ast.walk(tree):
        #model = nn.Sequential(...)
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Call):
                call = node.value

                # nn.Sequential(...)
                if isinstance(call.func, ast.Attribute):
                    if call.func.attr == "Sequential":
                        model_name = node.targets[0].id
                        layers = []

                        for arg in call.args:
                            if isinstance(arg, ast.Call):
                                layer = extract_layer(arg)
                                if layer:
                                    layers.append(layer)
                    
                        models.append({
                            "model_name" : model_name,
                            "type" : "Sequential",
                            "layers" : layers
                        })
    return models

def extract_layer(call_node: ast.Call):
    if isinstance(call_node.func, ast.Attribute):
        layer_type = call_node.func.attr

        #nn.Linear(in, out)
        if layer_type == "Linear" and len(call_node.args) >= 2:
            return {
                "layer" : "Linear",
                "in" : ast.literal_eval(call_node.args[0]),
                "out" : ast.literal_eval(call_node.args[1])
            }
        
        # nn.ReLU(), nn.Sigmoid(), etc:
        return {
            "layer" : layer_type
        }
    
    return None