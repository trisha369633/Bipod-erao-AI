import "./DualDecisionResult.css";

const translations = {
  en: {
    title: "Final result",
    phishing: "PHISHING",
    legitimate: "LEGITIMATE",
  },
  bn: {
    title: "চূড়ান্ত ফলাফল",
    phishing: "PHISHING",
    legitimate: "LEGITIMATE",
  },
};

export default function DualDecisionResult({ analysis, isBangla }) {
  const text = isBangla ? translations.bn : translations.en;
  const prediction = analysis.final_decision.prediction;

  return (
    <section
      className={`dual-decision dual-decision--${prediction}`}
      aria-live="polite"
    >
      <h2>{text.title}</h2>
      <p className="dual-decision__prediction">{text[prediction]}</p>
      <p className="dual-decision__explanation">
        {analysis.decision_explanation}
      </p>
    </section>
  );
}
