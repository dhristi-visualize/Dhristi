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

def extract_manual_dense_layers(code: str):
    tree = ast.parse(code)

    tree = ast.parse(code)
    dense_assignments = extract_dense_assignments(tree)

    if len(dense_assignments) >= 2:
        return [{
            "model_name": "ManualDense",
            "type": "Dense",
            "layers": chain_dense_layers(dense_assignments)
        }]

    unrolled = detect_unrolled_dense(tree)
    if unrolled:
        return [{
            "model_name": "ManualDense",
            "type": "Dense",
            "layers": [{
                "layer": "Linear",
                "in": unrolled["inputs"],
                "out": unrolled["neurons"]
            }]
        }]

    input_size = None
    neuron_count = None
    has_bias = False
    has_dot = False
    has_loop = False

    for node in ast.walk(tree):

        # Detect input vector
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.List):
                name = node.targets[0].id if isinstance(node.targets[0], ast.Name) else ""

                # Heuristic: 1D list used later in dot or loop
                if input_size is None and len(node.value.elts) >= 2:
                    input_size = len(node.value.elts)

                # Detect 2D weight matrix
                if node.value.elts and isinstance(node.value.elts[0], ast.List):
                    neuron_count = len(node.value.elts)

                # Detect bias vector
                if name.lower().startswith("bias"):
                    has_bias = True

        # Detect np.dot(weights, inputs)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "dot":
                has_dot = True

        # Detect zip(weights, biases) loop
        if isinstance(node, ast.For):
            if isinstance(node.iter, ast.Call):
                if isinstance(node.iter.func, ast.Name) and node.iter.func.id == "zip":
                    has_loop = True

    confidence = 0
    confidence += 3 if has_dot else 0
    confidence += 2 if has_loop else 0
    confidence += 2 if neuron_count else 0
    confidence += 1 if has_bias else 0

    if confidence < 4 or not input_size or not neuron_count:
        return []

    return [{
        "model_name": "ManualDense",
        "type": "Dense",
        "layers": [{
            "layer": "Linear",
            "in": input_size,
            "out": neuron_count
        }]
    }]

def extract_weight_stack_dense(code: str):
    tree = ast.parse(code)
    layers = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.List):
                # weights = [...]
                if isinstance(node.targets[0], ast.Name) and node.targets[0].id == "weights":
                    top = node.value.elts  # layers

                    prev_out = None

                    for layer in top:
                        if not isinstance(layer, ast.List):
                            continue

                        neurons = len(layer.elts)
                        if neurons == 0:
                            continue

                        first = layer.elts[0]
                        if not isinstance(first, ast.List):
                            continue

                        in_features = len(first.elts)

                        layers.append({
                            "layer": "Linear",
                            "in": in_features if prev_out is None else prev_out,
                            "out": neurons
                        })

                        prev_out = neurons

    if not layers:
        return []

    return [{
        "model_name": "ManualDense",
        "type": "Dense",
        "layers": layers
    }]


def detect_unrolled_dense(tree):
    """
    Detects:
    inputs[0]*w[0] + inputs[1]*w[1] + ... + bias
    repeated N times → Dense layer
    """
    neuron_count = 0
    input_indices = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            terms = flatten_add(node)

            mul_terms = [
                t for t in terms
                if isinstance(t, ast.BinOp) and isinstance(t.op, ast.Mult)
            ]

            if len(mul_terms) >= 2:
                for m in mul_terms:
                    if isinstance(m.left, ast.Subscript):
                        input_indices.add(ast.unparse(m.left))
                neuron_count += 1

    if neuron_count >= 1 and len(input_indices) >= 2:
        return {
            "inputs": len(input_indices),
            "neurons": neuron_count
        }

    return None


def flatten_add(node):
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return flatten_add(node.left) + flatten_add(node.right)
    return [node]

def extract_dense_assignments(tree):
    """
    Finds:
    layerX_out = <dense expression>
    """
    layers = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
            name = node.targets[0].id if isinstance(node.targets[0], ast.Name) else None
            dense = detect_unrolled_dense_expr(node.value)

            if name and dense:
                layers.append({
                    "var": name,
                    "out": dense["neurons"]
                })
    return layers

def chain_dense_layers(dense_layers):
    chained = []
    prev_out = None

    for layer in dense_layers:
        in_features = prev_out if prev_out is not None else layer.get("in", None)

        chained.append({
            "layer": "Linear",
            "in": in_features,
            "out": layer["out"]
        })

        prev_out = layer["out"]

    return chained

def detect_unrolled_dense_expr(expr):
    """
    Detects a SINGLE dense layer from:
    [
      a*b + c*d + bias,
      ...
    ]
    """
    if not isinstance(expr, ast.List):
        return None

    neuron_count = len(expr.elts)
    input_terms = set()

    for elt in expr.elts:
        if not isinstance(elt, ast.BinOp):
            return None

        terms = flatten_add(elt)
        muls = [t for t in terms if isinstance(t, ast.BinOp) and isinstance(t.op, ast.Mult)]

        if len(muls) < 2:
            return None

        for m in muls:
            if isinstance(m.left, ast.Subscript):
                input_terms.add(ast.unparse(m.left.value))

    if neuron_count >= 1 and len(input_terms) >= 1:
        return {
            "inputs": None,     # resolved via chaining
            "neurons": neuron_count
        }

    return None

