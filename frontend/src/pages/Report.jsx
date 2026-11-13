import "./Report.css";

const translations = {
  en: {
    title: "Need Official Help?",
    subtitle:
      "If you are a victim of cybercrime or encounter suspicious online activity, contact the appropriate official authorities in Bangladesh.",
    resources: [
      {
        id: "cirt",
        title: "BGD e-GOV CIRT",
        description:
          "Report cybersecurity incidents directly to Bangladesh's national incident response team.",
        action: "Report an Incident",
        href: "https://www.cirt.gov.bd/report-incident",
        icon: "incident",
      },
      {
        id: "women-support",
        title: "Bangladesh Police – Police Cyber Support for Women",
        description:
          "Dedicated cyber support service for women facing cybercrime.",
        phoneLabel: "Phone",
        phone: "01320000888",
        emailLabel: "Email",
        email: "cybersupport.women@police.gov.bd",
        action: "Visit Official Website",
        href: "https://www.police.gov.bd/en/police_cyber_support_for_women",
        icon: "women-support",
      },
      {
        id: "emergency",
        title: "National Emergency Service",
        description:
          "For immediate danger or urgent threats, contact the national emergency service.",
        phoneLabel: "Phone",
        phone: "999",
        action: "Call 999",
        href: "tel:999",
        icon: "emergency",
      },
      {
        id: "police",
        title: "Bangladesh Police",
        description:
          "Contact Bangladesh Police or visit the nearest police station for assistance with cybercrime.",
        action: "Visit Bangladesh Police",
        href: "https://www.police.gov.bd/",
        icon: "police",
      },
    ],
  },
  bn: {
    title: "অফিশিয়াল সহায়তা প্রয়োজন?",
    subtitle:
      "আপনি সাইবার অপরাধের শিকার হলে বা সন্দেহজনক অনলাইন কার্যকলাপের সম্মুখীন হলে, বাংলাদেশের সংশ্লিষ্ট সরকারি কর্তৃপক্ষের সঙ্গে যোগাযোগ করুন।",
    resources: [
      {
        id: "cirt",
        title: "BGD e-GOV CIRT",
        description:
          "বাংলাদেশের জাতীয় ইনসিডেন্ট রেসপন্স টিমে সরাসরি সাইবার নিরাপত্তা ঘটনা রিপোর্ট করুন।",
        action: "ঘটনা রিপোর্ট করুন",
        href: "https://www.cirt.gov.bd/report-incident",
        icon: "incident",
      },
      {
        id: "women-support",
        title: "বাংলাদেশ পুলিশ – নারী সাইবার সহায়তা",
        description:
          "সাইবার অপরাধের শিকার নারীদের জন্য বিশেষায়িত সাইবার সহায়তা সেবা।",
        phoneLabel: "ফোন",
        phone: "01320000888",
        emailLabel: "ইমেইল",
        email: "cybersupport.women@police.gov.bd",
        action: "অফিশিয়াল ওয়েবসাইট দেখুন",
        href: "https://www.police.gov.bd/en/police_cyber_support_for_women",
        icon: "women-support",
      },
      {
        id: "emergency",
        title: "জাতীয় জরুরি সেবা",
        description:
          "তাৎক্ষণিক বিপদ বা জরুরি হুমকির ক্ষেত্রে জাতীয় জরুরি সেবায় যোগাযোগ করুন।",
        phoneLabel: "ফোন",
        phone: "999",
        action: "৯৯৯-এ কল করুন",
        href: "tel:999",
        icon: "emergency",
      },
      {
        id: "police",
        title: "বাংলাদেশ পুলিশ",
        description:
          "সাইবার অপরাধে সহায়তার জন্য বাংলাদেশ পুলিশের সঙ্গে যোগাযোগ করুন বা নিকটস্থ থানায় যান।",
        action: "বাংলাদেশ পুলিশ ওয়েবসাইট দেখুন",
        href: "https://www.police.gov.bd/",
        icon: "police",
      },
    ],
  },
};

function ResourceIcon({ name }) {
  const paths = {
    incident: (
      <>
        <path d="M24 5 38 10v10c0 10-6 17-14 21C16 37 10 30 10 20V10l14-5Z" />
        <path d="m18 23 4 4 8-9" />
      </>
    ),
    "women-support": (
      <>
        <circle cx="24" cy="15" r="6" />
        <path d="M12 38c1.8-7 5.8-10.5 12-10.5S34.2 31 36 38" />
        <path d="M34 10h7M37.5 6.5v7" />
      </>
    ),
    emergency: (
      <>
        <path d="M16 9h16a5 5 0 0 1 5 5v16a5 5 0 0 1-5 5h-3l-5 5-5-5h-3a5 5 0 0 1-5-5V14a5 5 0 0 1 5-5Z" />
        <path d="M19 18c1 6 5 10 11 11M20 17l-3 3m14 9 3-3" />
      </>
    ),
    police: (
      <>
        <path d="M7 39h34M11 39V19h26v20M7 19 24 7l17 12" />
        <path d="M18 39V27h12v12M16 24h3m12 0h3" />
      </>
    ),
  };

  return (
    <span className={`resource-card__icon resource-card__icon--${name}`} aria-hidden="true">
      <svg viewBox="0 0 48 48" fill="none">
        {paths[name]}
      </svg>
    </span>
  );
}

export default function Report({ isBangla }) {
  const text = isBangla ? translations.bn : translations.en;

  return (
    <main className="report-page">
      <div className="report-page__content">
        <header className="report-heading">
          <h1>{text.title}</h1>
          <p>{text.subtitle}</p>
        </header>

        <section
          className="official-resources"
          aria-label={isBangla ? "অফিশিয়াল সহায়তা রিসোর্স" : "Official help resources"}
        >
          {text.resources.map((resource) => (
            <article
              className={`resource-card resource-card--${resource.id}`}
              key={resource.id}
            >
              <div className="resource-card__heading">
                <ResourceIcon name={resource.icon} />
                <h2>{resource.title}</h2>
              </div>

              <p className="resource-card__description">{resource.description}</p>

              {(resource.phone || resource.email) && (
                <div className="resource-card__contacts">
                  {resource.phone && (
                    <p>
                      <span>{resource.phoneLabel}:</span>{" "}
                      <a href={`tel:${resource.phone}`}>{resource.phone}</a>
                    </p>
                  )}
                  {resource.email && (
                    <p>
                      <span>{resource.emailLabel}:</span>{" "}
                      <a href={`mailto:${resource.email}`}>{resource.email}</a>
                    </p>
                  )}
                </div>
              )}

              <a
                className="resource-card__action"
                href={resource.href}
                target={resource.href.startsWith("https://") ? "_blank" : undefined}
                rel={
                  resource.href.startsWith("https://")
                    ? "noopener noreferrer"
                    : undefined
                }
              >
                {resource.action}
                {resource.href.startsWith("https://") && (
                  <span aria-hidden="true">↗</span>
                )}
              </a>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
