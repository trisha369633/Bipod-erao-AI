import { useState } from "react";
import {
  analyzeDualMessage,
  analyzeMessageUrls,
} from "../services/api";
import DualDecisionResult from "../components/DualDecisionResult";
import URLAnalysisResult from "../components/URLAnalysisResult";
import "./AnalysisForm.css";
import "./MessageCheck.css";

const translations = {
  en: {
    title: "Message Check",
    instruction: "Type your message",
    placeholder: "Paste or type your suspicious message here...",
    button: "Check Message",
    loading: "Analyzing message...",
    emptyError: "Enter a message to analyze.",
    tooLongError: "Messages must be 5,000 characters or fewer.",
    invalidError: "The message is invalid. Check it and try again.",
    serviceError:
      "The analysis service is unavailable. Please start the backend and try again.",
    invalidResult:
      "The analysis service returned an invalid result. Please try again later.",
    requestError: "The message could not be analyzed. Please try again later.",
    urlAnalysisError:
      "Message classification succeeded, but URL analysis is unavailable.",
    resultsTitle: "Message Analysis",
    classificationTitle: "Message classification",
    classNames: { normal: "Normal", promo: "Promotional", smish: "Smishing" },
    riskLevel: "Risk level",
    riskLevels: { low: "Low", medium: "Medium", high: "High" },
    heuristic: "Heuristic risk score",
    confidence: "Model confidence scores",
    explanation: "How the analysis works",
    modelExplanation: "Model classification",
    ruleExplanation: "Rule-based indicators",
    indicatorTitle: "Detected indicators",
    noIndicators:
      "No configured indicator patterns matched. This does not guarantee that the message is safe.",
    matchedText: "Matched text",
    safetyAdvice: "Safety advice",
    original: "Original message",
    riskNote:
      "This heuristic score is not a calibrated probability or a guarantee of fraud.",
    urlAnalysisTitle: "URL Analysis",
  },
  bn: {
    title: "মেসেজ চেক",
    instruction: "আপনার মেসেজ লিখুন",
    placeholder: "আপনার সন্দেহজনক মেসেজ এখানে লিখুন...",
    button: "মেসেজ পরীক্ষা করুন",
    loading: "মেসেজ বিশ্লেষণ করা হচ্ছে...",
    emptyError: "বিশ্লেষণের জন্য একটি মেসেজ লিখুন।",
    tooLongError: "মেসেজ ৫,০০০ অক্ষর বা তার কম হতে হবে।",
    invalidError: "মেসেজটি সঠিক নয়। পরীক্ষা করে আবার চেষ্টা করুন।",
    serviceError:
      "বিশ্লেষণ পরিষেবা এখন উপলভ্য নয়। ব্যাকএন্ড চালু করে আবার চেষ্টা করুন।",
    invalidResult:
      "বিশ্লেষণ পরিষেবা থেকে সঠিক ফলাফল পাওয়া যায়নি। পরে আবার চেষ্টা করুন।",
    requestError:
      "মেসেজটি বিশ্লেষণ করা যায়নি। অনুগ্রহ করে পরে আবার চেষ্টা করুন।",
    urlAnalysisError:
      "মেসেজের শ্রেণিবিন্যাস হয়েছে, কিন্তু URL বিশ্লেষণ এখন উপলভ্য নয়।",
    resultsTitle: "মেসেজ বিশ্লেষণ",
    classificationTitle: "মেসেজের শ্রেণিবিন্যাস",
    classNames: {
      normal: "সাধারণ",
      promo: "প্রচারমূলক",
      smish: "স্মিশিং",
    },
    riskLevel: "ঝুঁকির মাত্রা",
    riskLevels: { low: "কম", medium: "মাঝারি", high: "উচ্চ" },
    heuristic: "নিয়মভিত্তিক ঝুঁকি স্কোর",
    confidence: "মডেলের আত্মবিশ্বাসের স্কোর",
    explanation: "বিশ্লেষণ যেভাবে কাজ করে",
    modelExplanation: "মডেলের শ্রেণিবিন্যাস",
    ruleExplanation: "নিয়মভিত্তিক সূচক",
    indicatorTitle: "শনাক্ত সূচক",
    noIndicators:
      "কনফিগার করা কোনো সূচকের ধরন মেলেনি। এর মানে এই নয় যে মেসেজটি নিরাপদ।",
    matchedText: "মিলে যাওয়া টেক্সট",
    safetyAdvice: "নিরাপত্তা পরামর্শ",
    original: "মূল মেসেজ",
    riskNote:
      "এই নিয়মভিত্তিক স্কোর ক্যালিব্রেটেড সম্ভাবনা বা প্রতারণার নিশ্চয়তা নয়।",
    urlAnalysisTitle: "URL বিশ্লেষণ",
  },
};

function getErrorCode(error) {
  if (error.code === "INVALID_MESSAGE") return "invalidError";
  if (error.message === "ANALYSIS_SERVICE_UNAVAILABLE") return "serviceError";
  if (error.message === "ANALYSIS_RESPONSE_INVALID") return "invalidResult";
  return "requestError";
}

function MessageAnalysisResult({ result, message, text, isBangla }) {
  const confidenceScores = result.confidence_scores;
  const explanation = result.explanation;

  return (
    <section className="message-result" aria-live="polite">
      <h2>{text.resultsTitle}</h2>

      <div className="message-result__summary">
        <div className="message-result__classification">
          <span>{text.classificationTitle}</span>
          <strong>{text.classNames[result.predicted_label] ?? result.predicted_label}</strong>
        </div>
        <div
          className={`message-result__risk message-result__risk--${result.risk_level}`}
        >
          <span>{text.riskLevel}</span>
          <strong>{text.riskLevels[result.risk_level]}</strong>
        </div>
      </div>

      <div
        className="message-result__progress"
        role="progressbar"
        aria-label={text.heuristic}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={result.risk_score}
      >
        <span
          className={`message-result__progress-value message-result__progress-value--${result.risk_level}`}
          style={{ width: `${result.risk_score}%` }}
        />
      </div>
      <p className="message-result__note">
        {text.heuristic}: {result.risk_score}/100. {result.risk_score_note[isBangla ? "bn" : "en"]}
      </p>

      {confidenceScores && (
        <section className="message-result__section">
          <h3>{text.confidence}</h3>
          <ul className="message-result__confidence">
            {Object.entries(confidenceScores).map(([label, score]) => (
              <li key={label}>
                <span>{text.classNames[label] ?? label}</span>
                <strong>{score.toFixed(3)}</strong>
              </li>
            ))}
          </ul>
          <p className="message-result__note">
            {result.confidence_note[isBangla ? "bn" : "en"]}
          </p>
        </section>
      )}

      <section className="message-result__section">
        <h3>{text.explanation}</h3>
        <p>
          <strong>{text.modelExplanation}: </strong>
          {explanation.model[isBangla ? "bn" : "en"]}
        </p>
        <p>
          <strong>{text.ruleExplanation}: </strong>
          {explanation.rule_based[isBangla ? "bn" : "en"]}
        </p>
      </section>

      <section className="message-result__section">
        <h3>{text.indicatorTitle}</h3>
        {result.suspicious_indicators.length ? (
          <ul className="message-result__indicators">
            {result.suspicious_indicators.map((indicator) => (
              <li key={indicator.code}>
                <p>{indicator.description[isBangla ? "bn" : "en"]}</p>
                <span>{text.matchedText}: {indicator.matches.join(", ")}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p>{text.noIndicators}</p>
        )}
      </section>

      <section className="message-result__section">
        <h3>{text.safetyAdvice}</h3>
        <ul>
          {result.safety_advice[isBangla ? "bn" : "en"].map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="message-result__section message-result__original">
        <h3>{text.original}</h3>
        <pre>{message}</pre>
      </section>
    </section>
  );
}

export default function MessageCheck({ isBangla }) {
  const text = isBangla ? translations.bn : translations.en;
  const [message, setMessage] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [dualAnalysis, setDualAnalysis] = useState(null);
  const [urlAnalysis, setUrlAnalysis] = useState(null);
  const [urlAnalysisError, setUrlAnalysisError] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (isAnalyzing) return;
    setError("");
    setResult(null);
    setDualAnalysis(null);
    setUrlAnalysis(null);
    setUrlAnalysisError(false);

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
      const dualResult = await analyzeDualMessage(
        message,
        isBangla ? "bn" : "en",
      );
      setResult(dualResult.ml_details);
      setDualAnalysis(dualResult);
      try {
        setUrlAnalysis(await analyzeMessageUrls(message));
      } catch {
        setUrlAnalysisError(true);
      }
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
            <span className="analysis-panel__marker" aria-hidden="true">
              01
            </span>
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
                setResult(null);
                setDualAnalysis(null);
                setUrlAnalysis(null);
                setUrlAnalysisError(false);
              }}
              placeholder={text.placeholder}
              rows={7}
              maxLength={5000}
              disabled={isAnalyzing}
              aria-invalid={Boolean(error)}
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
              {isAnalyzing ? text.loading : text.button}
              {!isAnalyzing && <span aria-hidden="true">→</span>}
            </button>
          </form>

          {result && (
            <>
              <MessageAnalysisResult
                isBangla={isBangla}
                message={message}
                result={result}
                text={text}
              />
              {dualAnalysis && (
                <DualDecisionResult
                  analysis={dualAnalysis}
                  isBangla={isBangla}
                />
              )}
              {urlAnalysis && (
                <URLAnalysisResult isBangla={isBangla} analysis={urlAnalysis} />
              )}
              {urlAnalysisError && (
                <section className="message-result__section" role="alert">
                  <h3>{text.urlAnalysisTitle}</h3>
                  <p>{text.urlAnalysisError}</p>
                </section>
              )}
            </>
          )}
        </section>
      </div>
    </main>
  );
}
