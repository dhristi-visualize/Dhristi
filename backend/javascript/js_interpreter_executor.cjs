const Interpreter = require("js-interpreter");
const babel = require("@babel/core");

/**
 * Transpile modern JS → ES5 (required for JS-Interpreter)
 */
function transpileToES5(code) {
  const result = babel.transformSync(code, {
    presets: [["@babel/preset-env", { targets: { ie: "11" } }]],
    sourceType: "script",
    babelrc: false,
    configFile: false,
  });

  return result.code;
}

function runJavaScript(code) {
  const steps = [];
  const callTree = [];
  const stdout = [];
  const funcStack = ["<module>"];

  // 🔥 CRITICAL: transpile first
  const es5Code = transpileToES5(code);

  function captureState(interpreter) {
    const frames = [];
    const state = interpreter.stateStack[interpreter.stateStack.length - 1];
    let scope = state?.scope;

    while (scope) {
      const vars = {};
      for (const name in scope.object.properties) {
        const val = scope.object.properties[name];

        if (val === undefined || val === null || typeof val !== "object") {
          vars[name] = null;
        } else if ("value" in val) {
          vars[name] = val.value;
        } else {
          vars[name] = null;
        }
      }
      frames.push(vars);
      scope = scope.parentScope;
    }
    return frames;
  }

  const interpreter = new Interpreter(es5Code, function (interp, globalObject) {
    interp.setProperty(
      globalObject,
      "print",
      interp.createNativeFunction(function (text) {
        stdout.push(String(text));
      }),
    );
  });

  while (interpreter.step()) {
    const state = interpreter.stateStack[interpreter.stateStack.length - 1];
    if (!state || !state.node) continue;

    // Function entry
    if (
      state.node.type === "FunctionDeclaration" &&
      state.node.id &&
      state.node.id.name
    ) {
      funcStack.push(state.node.id.name);
    }

    // Function return
    if (state.node.type === "ReturnStatement") {
      funcStack.pop();
    }

    // Line-level step (best-effort; JS-Interpreter is op-based)
    if (typeof state.node.start === "number") {
      steps.push({
        event: "line",
        lineno: null, // exact line mapping requires source maps (optional later)
        func: funcStack[funcStack.length - 1],
        before: captureState(interpreter),
        after: captureState(interpreter),
        stdout: stdout.slice(),
      });
    }
  }

  return {
    success: true,
    steps,
    call_tree: callTree,
    nn_models: [],
    recursive_funcs: [],
  };
}

module.exports = { runJavaScript };
