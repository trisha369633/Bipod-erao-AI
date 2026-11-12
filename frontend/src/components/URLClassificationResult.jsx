import "./URLClassificationResult.css";

const translations = {
  en: {
    title: "URL Phishing Analysis",
    prediction: "Model prediction",
    labels: { phishing: "Phishing", legitimate: "Legitimate" },
    risk: "Risk level",
    levels: { high: "High", low: "Low" },
    confidence: "Model confidence",
    confidenceNote:
      "Model confidence is not a guaranteed probability that this URL is malicious or safe.",
    url: "Analyzed URL",
  },
  bn: {
    title: "URL ফিশিং বিশ্লেষণ",
    prediction: "মডেলের পূর্বাভাস",
    labels: { phishing: "ফিশিং", legitimate: "বৈধ" },
    risk: "ঝুঁকির মাত্রা",
    levels: { high: "উচ্চ", low: "কম" },
    confidence: "মডেলের আত্মবিশ্বাস",
    confidenceNote:
      "মডেলের আত্মবিশ্বাস এই URL ক্ষতিকর বা নিরাপদ হওয়ার নিশ্চয়তাপ্রাপ্ত সম্ভাবনা নয়।",
    url: "বিশ্লেষিত URL",
  },
};

export default function URLClassificationResult({ isBangla, result }) {
  const text = isBangla ? translations.bn : translations.en;

  return (
    <section className="url-classification" aria-live="polite">
      <h2>{text.title}</h2>
      <div className="url-classification__summary">
        <div>
          <span>{text.prediction}</span>
          <strong>{text.labels[result.prediction]}</strong>
        </div>
        <div
          className={`url-classification__risk url-classification__risk--${result.risk_level}`}
        >
          <span>{text.risk}</span>
          <strong>{text.levels[result.risk_level]}</strong>
        </div>
      </div>
      <p className="url-classification__message">{result.message}</p>
      <div className="url-classification__confidence">
        <span>{text.confidence}</span>
        <strong>{(result.model_confidence * 100).toFixed(1)}%</strong>
      </div>
      <p className="url-classification__note">{text.confidenceNote}</p>
      <h3>{text.url}</h3>
      <p className="url-classification__url">{result.url}</p>
    </section>
  );
}
