import "./DualDecisionResult.css";

const translations = {
  en: {
    ml: "ML Model Analysis",
    gemini: "Gemini AI Analysis",
    final: "Final Decision",
    selected: "Selected System",
    why: "Why This Decision?",
    confidence: "Model confidence",
    mlNote: "Uncalibrated model score; not a guaranteed accuracy percentage.",
    geminiNote: "Self-reported confidence; not a validated reliability score.",
    prediction: "Prediction",
    evidence: "Supporting evidence",
    reasons: "Reasons",
    unavailable: "Gemini analysis is unavailable.",
    noDetails: "No supporting details were returned.",
    systems: { ml: "ML model", both: "Both systems", none: "Neither system" },
    statuses: {
      agreement: "Systems agree",
      review_required: "Review required",
      ml_fallback: "ML-only fallback",
    },
    review: "Human review required",
    labels: {
      normal: "Normal",
      promo: "Promotional",
      smish: "Smishing",
      phishing: "Phishing",
      legitimate: "Legitimate",
    },
    calibrated:
      "No validated reliability calibration is available. Disagreement is not resolved by comparing raw confidence scores.",
  },
  bn: {
    ml: "এমএল মডেল বিশ্লেষণ",
    gemini: "Gemini AI বিশ্লেষণ",
    final: "চূড়ান্ত সিদ্ধান্ত",
    selected: "নির্বাচিত সিস্টেম",
    why: "এই সিদ্ধান্তের কারণ",
    confidence: "মডেলের আত্মবিশ্বাস",
    mlNote: "এটি অপরিমাপকৃত মডেল স্কোর; সঠিকতার নিশ্চয়তাপ্রাপ্ত শতাংশ নয়।",
    geminiNote: "এটি স্ব-প্রতিবেদিত আত্মবিশ্বাস; যাচাইকৃত নির্ভরযোগ্যতার স্কোর নয়।",
    prediction: "পূর্বাভাস",
    evidence: "সহায়ক প্রমাণ",
    reasons: "কারণ",
    unavailable: "Gemini বিশ্লেষণ পাওয়া যায়নি।",
    noDetails: "কোনো সহায়ক বিবরণ পাওয়া যায়নি।",
    systems: { ml: "এমএল মডেল", both: "উভয় সিস্টেম", none: "কোনোটি নয়" },
    statuses: {
      agreement: "সিস্টেম দুটির ফল এক",
      review_required: "পর্যালোচনা প্রয়োজন",
      ml_fallback: "শুধু এমএল বিকল্প ফল",
    },
    review: "মানবীয় পর্যালোচনা প্রয়োজন",
    labels: {
      normal: "সাধারণ",
      promo: "প্রচারমূলক",
      smish: "স্মিশিং",
      phishing: "ফিশিং",
      legitimate: "বৈধ",
    },
    calibrated:
      "যাচাইকৃত নির্ভরযোগ্যতা ক্যালিব্রেশন নেই। কাঁচা আত্মবিশ্বাসের স্কোর তুলনা করে মতভেদ মেটানো হয় না।",
  },
};

function Confidence({ value, note, title }) {
  if (typeof value !== "number") return null;
  return (
    <p className="dual-decision__confidence">
      <strong>{title}: {(value * 100).toFixed(1)}%</strong>
      <span>{note}</span>
    </p>
  );
}

function DetailList({ title, items, fallback }) {
  return (
    <>
      <h4>{title}</h4>
      {items?.length ? (
        <ul>
          {items.map((item, index) => (
            <li key={`${item}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>{fallback}</p>
      )}
    </>
  );
}

export default function DualDecisionResult({ analysis, isBangla }) {
  const text = isBangla ? translations.bn : translations.en;
  const label = (value) => text.labels[value] ?? value ?? text.review;
  const finalDecision = analysis.final_decision;
  const gemini = analysis.gemini_analysis;

  return (
    <section className="dual-decision" aria-live="polite">
      <article className="dual-decision__system">
        <h2>{text.ml}</h2>
        <p><strong>{text.prediction}: {label(analysis.ml_analysis.prediction)}</strong></p>
        <Confidence
          title={text.confidence}
          value={analysis.ml_analysis.confidence}
          note={text.mlNote}
        />
      </article>

      <article className="dual-decision__system">
        <h2>{text.gemini}</h2>
        {gemini.status === "available" ? (
          <>
            <p><strong>{text.prediction}: {label(gemini.prediction)}</strong></p>
            <Confidence
              title={text.confidence}
              value={gemini.confidence}
              note={text.geminiNote}
            />
            <DetailList
              title={text.evidence}
              items={gemini.evidence}
              fallback={text.noDetails}
            />
            <DetailList
              title={text.reasons}
              items={gemini.reasons}
              fallback={text.noDetails}
            />
          </>
        ) : (
          <p role="status">{text.unavailable}</p>
        )}
      </article>

      <article
        className={`dual-decision__final dual-decision__final--${finalDecision.status}`}
      >
        <h2>{text.final}</h2>
        <p className="dual-decision__status">
          {text.statuses[finalDecision.status] ?? text.review}
        </p>
        <p className="dual-decision__prediction">
          {label(finalDecision.prediction)}
        </p>
        <p><strong>{text.selected}: </strong>
          {text.systems[finalDecision.selected_system] ?? text.systems.none}
        </p>
        <h3>{text.why}</h3>
        <p>{analysis.decision_explanation}</p>
        {analysis.reliability_policy?.calibration_available === false && (
          <p className="dual-decision__policy">{text.calibrated}</p>
        )}
      </article>
    </section>
  );
}