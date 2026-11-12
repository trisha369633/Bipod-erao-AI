import { useState } from "react";
import DualDecisionResult from "../components/DualDecisionResult";
import URLClassificationResult from "../components/URLClassificationResult";
import { analyzeDualUrl } from "../services/api";
import "./AnalysisForm.css";
import "./LinkCheck.css";

const translations = {
  en: {
    title: "Link Check",
    instruction: "Enter the suspicious link",
    placeholder: "Paste the suspicious URL here...",
    button: "Check Link",
    loading: "Analyzing link...",
    emptyError: "Enter a URL to analyze.",
    invalidUrlError: "Enter a valid HTTP or HTTPS URL.",
    serviceError:
      "The analysis service is unavailable. Please try again later.",
    invalidResult:
      "The analysis service returned an invalid result. Please try again later.",
    requestError: "The link could not be analyzed. Please try again later.",
  },
  bn: {
    title: "লিংক চেক",
    instruction: "সন্দেহজনক লিংকটি লিখুন",
    placeholder: "সন্দেহজনক লিংকটি এখানে পেস্ট করুন...",
    button: "লিংক পরীক্ষা করুন",
    loading: "লিংক বিশ্লেষণ করা হচ্ছে...",
    emptyError: "বিশ্লেষণের জন্য একটি URL লিখুন।",
    invalidUrlError: "একটি সঠিক HTTP বা HTTPS URL লিখুন।",
    serviceError:
      "বিশ্লেষণ পরিষেবা এখন উপলভ্য নয়। অনুগ্রহ করে পরে আবার চেষ্টা করুন।",
    invalidResult:
      "বিশ্লেষণ পরিষেবা থেকে সঠিক ফলাফল পাওয়া যায়নি। পরে আবার চেষ্টা করুন।",
    requestError:
      "লিংকটি বিশ্লেষণ করা যায়নি। অনুগ্রহ করে পরে আবার চেষ্টা করুন।",
  },
};

function getErrorCode(error) {
  if (error.code === "INVALID_ANALYSIS_INPUT") return "invalidUrlError";
  if (error.code === "INVALID_URL") return "invalidUrlError";
  if (error.message === "ANALYSIS_SERVICE_UNAVAILABLE") return "serviceError";
  if (error.message === "ANALYSIS_RESPONSE_INVALID") return "invalidResult";
  return "requestError";
}

export default function LinkCheck({ isBangla }) {
  const text = isBangla ? translations.bn : translations.en;
  const [url, setUrl] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!url.trim()) {
      setError("emptyError");
      return;
    }

    setIsAnalyzing(true);
    try {
      setResult(
        await analyzeDualUrl(url.trim(), isBangla ? "bn" : "en"),
      );
    } catch (analysisError) {
      setError(getErrorCode(analysisError));
    } finally {
      setIsAnalyzing(false);
    }
  }

  return (
    <main className="analysis-page">
      <div className="analysis-page__content">
        <section className="analysis-panel" aria-labelledby="link-title">
          <div className="analysis-panel__heading">
            <span className="analysis-panel__marker" aria-hidden="true">
              02
            </span>
            <h1 id="link-title">{text.title}</h1>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <label className="analysis-panel__instruction" htmlFor="link-input">
              {text.instruction}
            </label>
            <input
              id="link-input"
              className="analysis-panel__url-input"
              type="text"
              inputMode="url"
              autoCapitalize="none"
              autoComplete="url"
              spellCheck="false"
              value={url}
              onChange={(event) => {
                setUrl(event.target.value);
                setError("");
                setResult(null);
              }}
              placeholder={text.placeholder}
              disabled={isAnalyzing}
              aria-invalid={error === "emptyError"}
              aria-describedby={error ? "link-error" : undefined}
            />
            {error && (
              <p className="analysis-panel__error" id="link-error" role="alert">
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
              <URLClassificationResult
                isBangla={isBangla}
                result={result.ml_details}
              />
              <DualDecisionResult analysis={result} isBangla={isBangla} />
            </>
          )}
        </section>
      </div>
    </main>
  );
}
