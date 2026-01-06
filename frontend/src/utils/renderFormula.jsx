import katex from "katex";
import "katex/dist/katex.min.css";

export function renderFormula(formulaObj) {
  if (!formulaObj) return null;

  const { latex, expr } = formulaObj;

  if (latex) {
    try {
      const html = katex.renderToString(latex, {
        throwOnError: false,
        displayMode: true,
      });

      return (
        <div
          className="mb-2"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      );
    } catch {
      return <pre className="text-xs text-white">{latex || expr}</pre>;
    }
  }

  return <pre className="text-xs text-white">{expr}</pre>;
}
