window.Utils = window.Utils || {};

window.Utils.renderFormula = (formulaObj) => {
  if (!formulaObj) return null;
  const { latex, expr } = formulaObj;
  if (latex && window.katex) {
    try {
      const html = window.katex.renderToString(latex, { throwOnError: false, displayMode: true });
      return <div dangerouslySetInnerHTML={{ __html: html }} className="mb-2" />;
    } catch (e) {
      return <pre className="text-xs text-white">{latex || expr}</pre>;
    }
  }
  return <pre className="text-xs text-white">{expr}</pre>;
};