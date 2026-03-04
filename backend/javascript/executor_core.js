import { instrument } from "./instrumenter.js";
import { runInstrumented } from "./sandbox.js";

export function executeJavaScript(sourceCode) {
  const instrumented = instrument(sourceCode);
  const tracer = runInstrumented(instrumented);

  return {
    success: true,
    steps: tracer.steps,
    call_tree: tracer.call_tree,
    nn_models: [],
    recursive_funcs: [],
  };
}
