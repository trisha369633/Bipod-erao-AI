import "./URLAnalysisResult.css";

const translations = {
  en: {
    title: "URL Analysis",
    noUrls: "No URLs were found in this input.",
    url: "Extracted URL",
    status: "URL status",
    statuses: {
      suspicious: "Suspicious",
      no_obvious_threat: "No obvious threat detected",
      unknown: "Unknown / Unable to verify",
    },
    indicators: "Detected indicators",
    noIndicators: "No structural indicators were detected.",
    explanations: {
      http: "HTTP is not encrypted. HTTP alone does not establish malicious intent.",
      ip_address: "Uses an IP address instead of a named domain.",
      shortener: "A shortening service hides the final destination; that alone does not make it phishing.",
      unusual_port: "Uses a non-standard web port.",
      userinfo: "Contains user information before the host, which may disguise the actual destination.",
      brand_impersonation: "Uses a well-known brand name outside its recognized domain.",
      misleading_subdomain: "Places account/security wording in a nested subdomain that can obscure the actual domain.",
      suspicious_hostname: "Combines account-verification terms with a hyphen in the hostname.",
      external_redirect: "A redirect parameter points to another website.",
      excessive_subdomains: "Contains an unusually large number of subdomain levels.",
      whatsapp: "Uses a recognized WhatsApp link host; this does not verify the sender or conversation.",
    },
    explanation: "Explanation",
    action: "Recommended action",
    liveUnavailable: "Live URL reputation checking is not configured. No live security scan was performed.",
    context: "Message context (separate from URL result)",
  },
  bn: {
    title: "URL বিশ্লেষণ",
    noUrls: "এই ইনপুটে কোনো URL পাওয়া যায়নি।",
    url: "শনাক্ত URL",
    status: "URL-এর অবস্থা",
    statuses: {
      suspicious: "সন্দেহজনক",
      no_obvious_threat: "স্পষ্ট হুমকি শনাক্ত হয়নি",
      unknown: "অজানা / যাচাই করা যায়নি",
    },
    indicators: "শনাক্ত সূচক",
    noIndicators: "URL-এর গঠনে কোনো সূচক শনাক্ত হয়নি।",
    explanations: {
      http: "HTTP এনক্রিপ্টেড নয়। শুধু HTTP হওয়া ক্ষতিকর অভিপ্রায় প্রমাণ করে না।",
      ip_address: "নামযুক্ত ডোমেইনের বদলে IP ঠিকানা ব্যবহার করা হয়েছে।",
      shortener: "সংক্ষিপ্তকরণ সেবা চূড়ান্ত গন্তব্য আড়াল করে; শুধু এ কারণে এটি ফিশিং নয়।",
      unusual_port: "ওয়েবের অস্বাভাবিক পোর্ট ব্যবহার করা হয়েছে।",
      userinfo: "হোস্টের আগে ব্যবহারকারীর তথ্য আছে, যা প্রকৃত গন্তব্য আড়াল করতে পারে।",
      brand_impersonation: "পরিচিত ব্র্যান্ডের নাম থাকলেও ডোমেইনটি স্বীকৃত ডোমেইন নয়।",
      misleading_subdomain: "সাবডোমেইনে অ্যাকাউন্ট/নিরাপত্তা-সংক্রান্ত শব্দ প্রকৃত ডোমেইন আড়াল করতে পারে।",
      suspicious_hostname: "হোস্টনেমে হাইফেনসহ অ্যাকাউন্ট যাচাইয়ের শব্দ রয়েছে।",
      external_redirect: "রিডাইরেক্ট প্যারামিটারটি অন্য ওয়েবসাইটে নির্দেশ করে।",
      excessive_subdomains: "অস্বাভাবিকভাবে অনেকগুলো সাবডোমেইন স্তর রয়েছে।",
      whatsapp: "WhatsApp-এর পরিচিত লিংক হোস্ট; এটি প্রেরক বা কথোপকথন যাচাই করে না।",
    },
    explanation: "ব্যাখ্যা",
    action: "প্রস্তাবিত পদক্ষেপ",
    liveUnavailable: "লাইভ URL রেপুটেশন পরীক্ষা কনফিগার করা নেই। কোনো লাইভ নিরাপত্তা স্ক্যান করা হয়নি।",
    context: "মেসেজের প্রেক্ষাপট (URL ফলাফল থেকে আলাদা)",
  },
};

export default function URLAnalysisResult({ isBangla, analysis }) {
  const text = isBangla ? translations.bn : translations.en;
  const language = isBangla ? "bn" : "en";

  return (
    <section className="url-analysis" aria-live="polite">
      <h2>{text.title}</h2>
      {analysis.urls.length ? (
        analysis.urls.map((item, index) => (
          <article className="url-analysis__item" key={`${item.extracted_url}-${index}`}>
            <h3>{text.url}</h3>
            <p className="url-analysis__url">{item.extracted_url}</p>
            <p className={`url-analysis__status url-analysis__status--${item.status}`}>
              <strong>{text.status}: </strong>
              {text.statuses[item.status] ?? text.statuses.unknown}
            </p>
            <h3>{text.indicators}</h3>
            {item.indicators.length ? (
              <ul>
                {item.indicators.map((code) => (
                  <li key={code}>{text.explanations[code] ?? code}</li>
                ))}
              </ul>
            ) : (
              <p>{text.noIndicators}</p>
            )}
            <h3>{text.explanation}</h3>
            <p>{item.explanation[language]}</p>
            <h3>{text.action}</h3>
            <p>{item.recommended_action[language]}</p>
          </article>
        ))
      ) : (
        <p>{text.noUrls}</p>
      )}
      {analysis.message_context && (
        <p className="url-analysis__context">{text.context}: {analysis.message_context[language]}</p>
      )}
      <p className="url-analysis__note">
        {analysis.live_reputation_message?.[language] ?? text.liveUnavailable}
      </p>
    </section>
  );
}
