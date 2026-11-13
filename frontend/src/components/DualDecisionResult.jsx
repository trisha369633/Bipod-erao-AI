import "./DualDecisionResult.css";

const translations = {
  en: {
    falseLabel: "FALSE",
    trueLabel: "TRUE",
    messageFalse:
      "This message appears to be fraudulent. It is not safe to click links or follow its instructions.",
    messageTrue:
      "This message appears legitimate. You may proceed with caution.",
    urlFalse: "This link appears suspicious or fraudulent. Do not click or open it.",
    urlTrue:
      "This link appears legitimate. However, remain cautious before entering personal information.",
  },
  bn: {
    falseLabel: "FALSE",
    trueLabel: "TRUE",
    messageFalse:
      "এই মেসেজটি ভুয়া। এতে ক্লিক করা বা দেওয়া নির্দেশনা অনুসরণ করা ঠিক হবে না।",
    messageTrue:
      "এই মেসেজটি স্বাভাবিক মনে হচ্ছে। আপনি সতর্কতার সঙ্গে এটি অনুসরণ করতে পারেন।",
    urlFalse:
      "এটি একটি সন্দেহজনক বা ভুয়া লিংক। এই লিংকে ক্লিক করা ঠিক হবে না।",
    urlTrue:
      "এই লিংকটি আসল বলে মনে হচ্ছে। তবে ওয়েবসাইটে কোনো ব্যক্তিগত তথ্য দেওয়ার আগে সতর্ক থাকুন।",
  },
};

export default function DualDecisionResult({
  analysis,
  isBangla,
  analysisType,
}) {
  const text = isBangla ? translations.bn : translations.en;
  const isFalse = analysis.final_decision.prediction === "phishing";
  const outcome = isFalse ? "false" : "true";
  const explanationKey = `${analysisType}${isFalse ? "False" : "True"}`;

  return (
    <section
      className={`dual-decision dual-decision--${outcome}`}
      role="status"
      aria-live="polite"
    >
      <p className="dual-decision__label">
        {isFalse ? text.falseLabel : text.trueLabel}
      </p>
      <p className="dual-decision__explanation">{text[explanationKey]}</p>
    </section>
  );
}
