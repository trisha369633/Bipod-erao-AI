import "./AnalysisResult.css";

const translations = {
  en: {
    estimate: "Estimated risk",
    riskLevel: "Risk level",
    levels: { low: "Low Risk", medium: "Medium Risk", high: "High Risk" },
    why: "Why Is It Suspicious?",
    noReasons: "The analysis did not provide specific reasons.",
    elements: "Suspicious Elements",
    noElements: "No suspicious elements were identified by the analysis.",
    advice: "Safety Advice",
    original: "Original Input",
    estimateNote: "This is an estimated risk, not guaranteed scam detection.",
    messageAdvice: [
      "Never share your OTP, PIN, or password.",
      "Do not click suspicious links.",
      "Verify the sender through an official channel.",
    ],
    linkAdvice: [
      "Do not enter passwords or payment details on suspicious websites.",
      "Verify the domain through the official website.",
      "Avoid shortened or unfamiliar links if you cannot verify their destination.",
    ],
  },
  bn: {
    estimate: "আনুমানিক ঝুঁকি",
    riskLevel: "ঝুঁকির মাত্রা",
    levels: { low: "কম ঝুঁকি", medium: "মাঝারি ঝুঁকি", high: "উচ্চ ঝুঁকি" },
    why: "কেন এটি সন্দেহজনক?",
    noReasons: "বিশ্লেষণে নির্দিষ্ট কোনো কারণ দেওয়া হয়নি।",
    elements: "সন্দেহজনক অংশ",
    noElements: "বিশ্লেষণে সন্দেহজনক কোনো অংশ শনাক্ত হয়নি।",
    advice: "নিরাপত্তা পরামর্শ",
    original: "মূল ইনপুট",
    estimateNote: "এটি আনুমানিক ঝুঁকি; প্রতারণা শনাক্তের নিশ্চয়তা নয়।",
    messageAdvice: [
      "আপনার OTP, PIN বা পাসওয়ার্ড কখনো শেয়ার করবেন না।",
      "সন্দেহজনক লিংকে ক্লিক করবেন না।",
      "অফিশিয়াল মাধ্যমে প্রেরকের পরিচয় যাচাই করুন।",
    ],
    linkAdvice: [
      "সন্দেহজনক ওয়েবসাইটে পাসওয়ার্ড বা পেমেন্টের তথ্য দেবেন না।",
      "অফিশিয়াল ওয়েবসাইট থেকে ডোমেইন যাচাই করুন।",
      "গন্তব্য যাচাই করতে না পারলে সংক্ষিপ্ত বা অপরিচিত লিংক এড়িয়ে চলুন।",
    ],
  },
};

export default function AnalysisResult({ isBangla, result, input, type }) {
  const text = isBangla ? translations.bn : translations.en;
  const advice = result.advice.length
    ? result.advice
    : type === "message"
      ? text.messageAdvice
      : text.linkAdvice;

  return (
    <section className="analysis-result" aria-live="polite">
      <div className="analysis-result__top">
        <div>
          <p className="analysis-result__eyebrow">{text.estimate}</p>
          <p className="analysis-result__score">{result.riskPercentage}%</p>
        </div>
        <div
          className={`analysis-result__level analysis-result__level--${result.riskLevel}`}
        >
          <span>{text.riskLevel}</span>
          <strong>{text.levels[result.riskLevel]}</strong>
        </div>
      </div>

      <div
        className="analysis-result__progress"
        role="progressbar"
        aria-label={text.estimate}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={result.riskPercentage}
      >
        <span
          className={`analysis-result__progress-value analysis-result__progress-value--${result.riskLevel}`}
          style={{ width: `${result.riskPercentage}%` }}
        />
      </div>
      <p className="analysis-result__note">{text.estimateNote}</p>

      <div className="analysis-result__sections">
        <section className="analysis-result__section">
          <h3>{text.why}</h3>
          {result.reasons.length ? (
            <ul>
              {result.reasons.map((reason, index) => (
                <li key={`${reason}-${index}`}>{reason}</li>
              ))}
            </ul>
          ) : (
            <p>{text.noReasons}</p>
          )}
        </section>

        <section className="analysis-result__section">
          <h3>{text.elements}</h3>
          {result.suspiciousElements.length ? (
            <ul className="analysis-result__elements">
              {result.suspiciousElements.map((element, index) => (
                <li key={`${element}-${index}`}>{element}</li>
              ))}
            </ul>
          ) : (
            <p>{text.noElements}</p>
          )}
        </section>

        <section className="analysis-result__section">
          <h3>{text.advice}</h3>
          <ul>
            {advice.map((item, index) => (
              <li key={`${item}-${index}`}>{item}</li>
            ))}
          </ul>
        </section>

        <section className="analysis-result__section analysis-result__original">
          <h3>{text.original}</h3>
          <pre>{input}</pre>
        </section>
      </div>
    </section>
  );
}
