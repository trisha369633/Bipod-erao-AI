import "./Home.css";

const copy = {
  en: {
    welcome: "Welcome to Bipod Erao AI",
    tagline:
      "Your free digital safety guide to detect suspicious messages and links.",
    intro:
      "Check suspicious SMS, identify possible phishing attempts, and understand the risks before you click or respond.",
    messageTitle: "Message Check",
    messageDescription:
      "Check suspicious SMS or messages to understand whether they may contain phishing attempts or scams.",
    messageButton: "Check Message",
    linkTitle: "Link Check",
    linkDescription:
      "Check suspicious URLs to understand whether they may lead to phishing websites or online scams.",
    linkButton: "Check Link",
  },
  bn: {
    welcome: "বিপদ এড়াও AI-তে স্বাগতম",
    tagline:
      "সন্দেহজনক মেসেজ ও লিংক শনাক্ত করার আপনার বিনামূল্যের ডিজিটাল নিরাপত্তা সহায়ক।",
    intro:
      "সন্দেহজনক SMS পরীক্ষা করুন, সম্ভাব্য ফিশিং শনাক্ত করুন এবং ক্লিক বা উত্তর দেওয়ার আগে ঝুঁকিগুলো বুঝে নিন।",
    messageTitle: "মেসেজ চেক",
    messageDescription:
      "সন্দেহজনক SMS বা মেসেজ পরীক্ষা করুন এবং ফিশিং বা প্রতারণার সম্ভাবনা বুঝুন।",
    messageButton: "মেসেজ পরীক্ষা করুন",
    linkTitle: "লিংক চেক",
    linkDescription:
      "সন্দেহজনক লিংক পরীক্ষা করুন এবং ফিশিং ওয়েবসাইট বা অনলাইন প্রতারণার ঝুঁকি বুঝুন।",
    linkButton: "লিংক পরীক্ষা করুন",
  },
};

function MessageIcon() {
  return (
    <svg viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <path
        d="M9 10.5h30v22H22l-9 6v-6H9v-22Z"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinejoin="round"
      />
      <path
        d="M16 19h16M16 25h11"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
    </svg>
  );
}

function LinkIcon() {
  return (
    <svg viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <path
        d="m19.5 28.5-3 3a7 7 0 0 1-9.9-9.9l7-7a7 7 0 0 1 9.9 0"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <path
        d="m28.5 19.5 3-3a7 7 0 0 1 9.9 9.9l-7 7a7 7 0 0 1-9.9 0M18 30l12-12"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function Home({ isBangla, onNavigate }) {
  const text = isBangla ? copy.bn : copy.en;

  return (
    <main className="home-page" id="home">
      <div className="home-content">
        <section className="welcome" aria-labelledby="welcome-title">
          <h1 id="welcome-title">{text.welcome}</h1>
          <p className="welcome__tagline">{text.tagline}</p>
          <p className="welcome__intro">{text.intro}</p>
        </section>

        <section
          className="check-options"
          aria-label={isBangla ? "নিরাপত্তা যাচাই" : "Safety checks"}
        >
          <article className="check-card check-card--message" id="message-check">
            <div className="check-card__icon">
              <MessageIcon />
            </div>
            <div className="check-card__body">
              <h2>{text.messageTitle}</h2>
              <p>{text.messageDescription}</p>
              <a
                className="check-card__button"
                href="/message-check"
                onClick={(event) => onNavigate(event, "/message-check")}
              >
                {text.messageButton}
                <span aria-hidden="true">→</span>
              </a>
            </div>
            <span className="check-card__number" aria-hidden="true">
              01
            </span>
          </article>

          <article className="check-card check-card--link" id="link-check">
            <div className="check-card__icon">
              <LinkIcon />
            </div>
            <div className="check-card__body">
              <h2>{text.linkTitle}</h2>
              <p>{text.linkDescription}</p>
              <a
                className="check-card__button"
                href="/link-check"
                onClick={(event) => onNavigate(event, "/link-check")}
              >
                {text.linkButton}
                <span aria-hidden="true">→</span>
              </a>
            </div>
            <span className="check-card__number" aria-hidden="true">
              02
            </span>
          </article>
        </section>
      </div>
    </main>
  );
}
