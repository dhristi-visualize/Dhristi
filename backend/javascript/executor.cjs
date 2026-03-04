const { runJavaScript } = require("./js_interpreter_executor.cjs");

// Ensure stdin is read as UTF-8
process.stdin.setEncoding("utf8");

let code = "";

process.stdin.on("data", (chunk) => {
  code += chunk;
});

process.stdin.on("end", () => {
  try {
    if (!code.trim()) {
      process.stdout.write(
        JSON.stringify({
          success: false,
          error: "No JavaScript code provided",
        }),
      );
      process.exit(0);
    }

    const result = runJavaScript(code);
    process.stdout.write(JSON.stringify(result));
    process.exit(0);
  } catch (e) {
    process.stdout.write(
      JSON.stringify({
        success: false,
        error: String(e),
      }),
    );
    process.exit(0);
  }
});

// Safety: handle unexpected stdin errors
process.stdin.on("error", (err) => {
  process.stdout.write(
    JSON.stringify({
      success: false,
      error: "Stdin error: " + String(err),
    }),
  );
  process.exit(0);
});
