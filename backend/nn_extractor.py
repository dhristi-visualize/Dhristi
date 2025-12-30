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

def analyze_neuron_expression(expr):
    '''
    Docstring for analyze_neuron_expression
    
    detects expressions of the form : x[0]*w[0] + x[1]*w[1] + ... + bias
    '''
    if not isinstance(expr, ast.BinOp):
        return None
    
    terms = []
    bias = None

    def walk(node):
        nonlocal bias
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            walk(node.left)
            walk(node.right)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            # expect x[i] * w[i]
            if (
                isinstance(node.left, ast.Subscript)
                and isinstance(node.right, ast.Subscript)
            ):
                terms.append((node.left, node.right))
        elif isinstance(node, ast.Name) or isinstance(node, ast.Constant):
            bias = ast.unparse(node)

    walk(expr)

    if len(terms) < 2:
        return None
    
    input_name = ast.unparse(terms[0][0].value)
    weight_name = ast.unparse(terms[0][1].value)

    return {
        "input" : input_name,
        "weight" : weight_name,
        "bias" : bias,
        "input_count" : len(terms)
    }

# def extract_manual_dense(code):
#     tree = ast.parse(code)
#     models = []

#     for node in ast.walk(tree):
#         if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
#             outputs = node.value.elts
#             neurons = []

#             for elt in outputs:
#                 neuron = analyze_neuron_expression(elt)
#                 if neuron:
#                     neurons.append(neuron)

#             if len(neurons) >= 2:
#                 models.append({
#                     "model_name" : node.targets[0].id,
#                     "type" : "ManualDense",
#                     "neurons" : neurons
#                 })

#     return models

def extract_manual_dense(code):
    tree = ast.parse(code)
    models = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            # Case 1: Multiple neurons (list of expressions)
            if isinstance(node.value, ast.List):
                outputs = node.value.elts
                neurons = []

                for elt in outputs:
                    neuron = analyze_neuron_expression(elt)
                    if neuron:
                        neurons.append(neuron)

                if len(neurons) >= 2:  # At least 2 neurons
                    models.append({
                        "model_name": node.targets[0].id,
                        "type": "ManualDense",
                        "neurons": neurons
                    })
            
            # Case 2: Single neuron (direct expression)
            else:
                neuron = analyze_neuron_expression(node.value)
                if neuron:
                    # Check if variable names suggest neural network
                    var_name = node.targets[0].id if node.targets else ""
                    if is_likely_neural_network(var_name, neuron):
                        models.append({
                            "model_name": var_name,
                            "type": "SingleNeuron",
                            "neurons": [neuron]
                        })

    return models

def is_likely_neural_network(var_name, neuron):
    """Heuristic to guess if this is a neural network"""
    nn_keywords = ["output", "neuron", "activation", "hidden", "layer", "prediction", "y_pred", "forward"]
    
    # Check variable name
    var_lower = var_name.lower()
    if any(keyword in var_lower for keyword in nn_keywords):
        return True
    
    # Check if weights/bias naming suggests NN
    weight_name = neuron.get("weight", "").lower()
    bias_name = str(neuron.get("bias", "")).lower()
    
    if "weight" in weight_name or "w" == weight_name:
        if "bias" in bias_name or "b" == bias_name:
            return True
    
    # If it has 3+ inputs, more likely to be NN
    if neuron.get("input_count", 0) >= 3:
        return True
    
    return False

