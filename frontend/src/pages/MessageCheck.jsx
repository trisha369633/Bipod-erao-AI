import { useState } from "react";
import { analyzeDualMessage } from "../services/api";
import DualDecisionResult from "../components/DualDecisionResult";
import "./AnalysisForm.css";
import "./MessageCheck.css";

const translations = {
  en: {
    title: "Message Check",
    instruction: "Type your message",
    placeholder: "Paste or type your suspicious message here...",
    button: "Check Message",
    retry: "Try again",
    loading: "Analyzing message...",
    emptyError: "Enter a message to analyze.",
    tooLongError: "Messages must be 5,000 characters or fewer.",
    invalidError: "The message is invalid. Check it and try again.",
    unavailable:
      "Analysis is temporarily unavailable. Please try again.",
    requestError: "The message could not be analyzed. Please try again.",
  },
  bn: {
    title: "মেসেজ চেক",
    instruction: "আপনার মেসেজ লিখুন",
    placeholder: "আপনার সন্দেহজনক মেসেজ এখানে লিখুন...",
    button: "মেসেজ পরীক্ষা করুন",
    retry: "আবার চেষ্টা করুন",
    loading: "মেসেজ বিশ্লেষণ করা হচ্ছে...",
    emptyError: "বিশ্লেষণের জন্য একটি মেসেজ লিখুন।",
    tooLongError: "মেসেজ ৫,০০০ অক্ষর বা তার কম হতে হবে।",
    invalidError: "মেসেজটি সঠিক নয়। পরীক্ষা করে আবার চেষ্টা করুন।",
    unavailable:
      "বিশ্লেষণ সাময়িকভাবে উপলভ্য নয়। অনুগ্রহ করে আবার চেষ্টা করুন।",
    requestError: "মেসেজটি বিশ্লেষণ করা যায়নি। অনুগ্রহ করে আবার চেষ্টা করুন।",
  },
};

function getErrorCode(error) {
  if (error.code === "INVALID_ANALYSIS_INPUT") return "invalidError";
  if (error.code === "GEMINI_UNAVAILABLE") return "unavailable";
  if (error.message === "ANALYSIS_SERVICE_UNAVAILABLE") return "unavailable";
  return "requestError";
}

export default function MessageCheck({ isBangla }) {
  const text = isBangla ? translations.bn : translations.en;
  const [message, setMessage] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    if (isAnalyzing) return;
    setError("");
    setAnalysis(null);

    if (!message.trim()) {
      setError("emptyError");
      return;
    }
    if (message.length > 5000) {
      setError("tooLongError");
      return;
    }

    setIsAnalyzing(true);
    try {
      setAnalysis(await analyzeDualMessage(message, isBangla ? "bn" : "en"));
    } catch (analysisError) {
      setError(getErrorCode(analysisError));
    } finally {
      setIsAnalyzing(false);
    }
  }

  return (
    <main className="analysis-page">
      <div className="analysis-page__content">
        <section className="analysis-panel" aria-labelledby="message-title">
          <div className="analysis-panel__heading">
            <h1 id="message-title">{text.title}</h1>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <label className="analysis-panel__instruction" htmlFor="message-input">
              {text.instruction}
            </label>
            <textarea
              id="message-input"
              className="analysis-panel__textarea"
              value={message}
              onChange={(event) => {
                setMessage(event.target.value);
                setError("");
                setAnalysis(null);
              }}
              placeholder={text.placeholder}
              rows={4}
              maxLength={5000}
              disabled={isAnalyzing}
              aria-invalid={
                ["emptyError", "tooLongError", "invalidError"].includes(error)
              }
              aria-describedby={error ? "message-error" : undefined}
            />
            {error && (
              <p className="analysis-panel__error" id="message-error" role="alert">
                {text[error]}
              </p>
            )}
            <button
              className="analysis-panel__submit"
              type="submit"
              disabled={isAnalyzing}
            >
              {isAnalyzing
                ? text.loading
                : error === "unavailable"
                  ? text.retry
                  : text.button}
              {!isAnalyzing && <span aria-hidden="true">→</span>}
            </button>
          </form>

          {analysis && (
            <DualDecisionResult
              analysis={analysis}
              isBangla={isBangla}
              analysisType="message"
            />
          )}
        </section>
      </div>
    </main>
  );
}
