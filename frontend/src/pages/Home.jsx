import "./Home.css";

const copy = {
  en: {
    welcome: "Welcome to Bipod Erao AI",
    tagline:
      "Your free digital safety guide to detect suspicious messages and links.",
    intro:
      "Check suspicious SMS, identify possible phishing attempts, and understand the risks before you click or respond.",
    messageCta: "Check a Message",
    linkCta: "Check a Link",
    featuresLabel: "What you can do",
    features: [
      {
        title: "Smishing & SMS Detection",
        description:
          "Check suspicious SMS and messages for signs of smishing.",
        action: "Check a message",
        href: "/message-check",
        icon: "message",
      },
      {
        title: "Phishing URL Scanner",
        description: "Scan URLs for patterns associated with phishing.",
        action: "Check a link",
        href: "/link-check",
        icon: "link",
      },
      {
        title: "Official Incident Reporting & Help",
        description:
          "Find official Bangladesh resources for incident reporting and cybercrime support.",
        action: "Find official help",
        href: "/report",
        icon: "help",
      },
    ],
  },
  bn: {
    welcome: "বিপদ এড়াও AI-তে স্বাগতম",
    tagline:
      "সন্দেহজনক মেসেজ ও লিংক শনাক্ত করার আপনার বিনামূল্যের ডিজিটাল নিরাপত্তা সহায়ক।",
    intro:
      "সন্দেহজনক SMS পরীক্ষা করুন, সম্ভাব্য ফিশিং শনাক্ত করুন এবং ক্লিক বা উত্তর দেওয়ার আগে ঝুঁকিগুলো বুঝে নিন।",
    messageCta: "মেসেজ পরীক্ষা করুন",
    linkCta: "লিংক পরীক্ষা করুন",
    featuresLabel: "আপনি যা করতে পারবেন",
    features: [
      {
        title: "স্মিশিং ও SMS শনাক্তকরণ",
        description: "সন্দেহজনক SMS ও মেসেজে স্মিশিংয়ের লক্ষণ পরীক্ষা করুন।",
        action: "মেসেজ পরীক্ষা করুন",
        href: "/message-check",
        icon: "message",
      },
      {
        title: "ফিশিং URL স্ক্যানার",
        description: "ফিশিংয়ের সঙ্গে সম্পর্কিত লক্ষণের জন্য URL পরীক্ষা করুন।",
        action: "লিংক পরীক্ষা করুন",
        href: "/link-check",
        icon: "link",
      },
      {
        title: "অফিশিয়াল ঘটনা রিপোর্ট ও সহায়তা",
        description:
          "ঘটনা রিপোর্ট ও সাইবার অপরাধে সহায়তার জন্য বাংলাদেশের সরকারি সংস্থাগুলোর তথ্য দেখুন।",
        action: "অফিশিয়াল সহায়তা দেখুন",
        href: "/report",
        icon: "help",
      },
    ],
  },
};

function FeatureIcon({ name }) {
  const paths = {
    message: (
      <>
        <path d="M7 9h26v19H18l-8 6v-6H7V9Z" />
        <path d="M13 16h14M13 21h10" />
      </>
    ),
    link: (
      <>
        <path d="m18 22-3 3a7 7 0 0 1-10-10l6-6a7 7 0 0 1 10 0" />
        <path d="m22 18 3-3a7 7 0 0 1 10 10l-6 6a7 7 0 0 1-10 0M14 24l10-10" />
      </>
    ),
    help: (
      <>
        <path d="M20 5 34 10v10c0 10-6 17-14 21C12 37 6 30 6 20V10l14-5Z" />
        <path d="m14 22 4 4 8-9" />
      </>
    ),
  };

  return (
    <span className="feature-card__icon" aria-hidden="true">
      <svg viewBox="0 0 40 40" fill="none">
        {paths[name]}
      </svg>
    </span>
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
          <div className="home-actions">
            <a
              className="home-actions__button home-actions__button--primary"
              href="/message-check"
              onClick={(event) => onNavigate(event, "/message-check")}
            >
              {text.messageCta}
              <span aria-hidden="true">→</span>
            </a>
            <a
              className="home-actions__button home-actions__button--secondary"
              href="/link-check"
              onClick={(event) => onNavigate(event, "/link-check")}
            >
              {text.linkCta}
              <span aria-hidden="true">→</span>
            </a>
          </div>
        </section>

        <section className="feature-section" aria-label={text.featuresLabel}>
          <div className="feature-grid">
            {text.features.map((feature) => (
              <article className="feature-card" key={feature.icon}>
                <FeatureIcon name={feature.icon} />
                <h2>{feature.title}</h2>
                <p>{feature.description}</p>
                <a
                  className="feature-card__action"
                  href={feature.href}
                  onClick={(event) => onNavigate(event, feature.href)}
                >
                  {feature.action}
                  <span aria-hidden="true">→</span>
                </a>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
