import { useState } from "react";
import "./Report.css";

const translations = {
  en: {
    title: "Report Suspicious Activity",
    subtitle:
      "Help protect yourself and others by identifying suspicious online activities.",
    reportType: "Report Type",
    chooseReportType: "Select a report type",
    reportTypes: [
      "Suspicious SMS",
      "Phishing Link",
      "Online Scam",
      "Fake Offer or Giveaway",
      "Impersonation",
      "Other",
    ],
    platform: "Platform",
    choosePlatform: "Select a platform",
    platforms: ["SMS", "WhatsApp", "Facebook", "Email", "Website", "Other"],
    detailsLabel: "Suspicious Message or URL",
    detailsPlaceholder: "Paste the suspicious message or URL here...",
    descriptionLabel: "Description",
    descriptionPlaceholder: "Explain what happened...",
    submit: "Submit Report",
    confirmationTitle: "Thank you for sharing this information!",
    confirmation:
      "Your report has been reviewed by this page's local interface only. No information has been uploaded or sent anywhere.",
    another: "Submit Another Report",
    safetyTitle: "Safety Advice",
    safetyAdvice: {
      "Suspicious SMS": [
        "Do not reply to suspicious messages or share OTPs, PINs, or passwords.",
        "Verify the sender using an official contact method.",
      ],
      "Phishing Link": [
        "Do not open unfamiliar links or enter personal information on suspicious sites.",
        "Check the domain carefully and verify it through an official website.",
      ],
      "Online Scam": [
        "Do not send money or share financial details before independently verifying a request.",
        "Keep records of suspicious communications for your own reference.",
      ],
      "Fake Offer or Giveaway": [
        "Be cautious of offers that require a fee or sensitive information to claim a prize.",
        "Verify promotions through the organization's official channels.",
      ],
      Impersonation: [
        "Contact the person or organization through a known, official channel to verify their identity.",
        "Do not share codes, passwords, or payment details with an unverified contact.",
      ],
      Other: [
        "Pause before responding, clicking links, or sharing personal information.",
        "Verify unexpected requests through an official channel.",
      ],
    },
    officialTitle: "Need Official Help?",
    officialDescription:
      "Bipod Erao AI is an awareness tool, not a law enforcement service. For official assistance, use verified Bangladesh cybercrime reporting resources. Official links will be added here after verification.",
    officialPending: "Verified official resources will be listed here.",
    requiredError: "Please complete all fields before submitting.",
  },
  bn: {
    title: "সন্দেহজনক কার্যকলাপ রিপোর্ট করুন",
    subtitle:
      "সন্দেহজনক অনলাইন কার্যকলাপ শনাক্ত করে নিজেকে ও অন্যদের নিরাপদ রাখতে সাহায্য করুন।",
    reportType: "রিপোর্টের ধরন",
    chooseReportType: "রিপোর্টের ধরন নির্বাচন করুন",
    reportTypes: [
      "সন্দেহজনক SMS",
      "ফিশিং লিংক",
      "অনলাইন প্রতারণা",
      "ভুয়া অফার বা উপহার",
      "ছদ্মবেশ ধারণ",
      "অন্যান্য",
    ],
    platform: "প্ল্যাটফর্ম",
    choosePlatform: "প্ল্যাটফর্ম নির্বাচন করুন",
    platforms: ["SMS", "WhatsApp", "Facebook", "ইমেইল", "ওয়েবসাইট", "অন্যান্য"],
    detailsLabel: "সন্দেহজনক মেসেজ বা URL",
    detailsPlaceholder: "সন্দেহজনক মেসেজ বা URL এখানে পেস্ট করুন...",
    descriptionLabel: "বিবরণ",
    descriptionPlaceholder: "কী ঘটেছে তা ব্যাখ্যা করুন...",
    submit: "রিপোর্ট জমা দিন",
    confirmationTitle: "তথ্যটি শেয়ার করার জন্য ধন্যবাদ!",
    confirmation:
      "আপনার রিপোর্টটি শুধু এই পেজে দেখানো হয়েছে। কোনো তথ্য কোথাও আপলোড বা পাঠানো হয়নি।",
    another: "আরেকটি রিপোর্ট জমা দিন",
    safetyTitle: "নিরাপত্তা পরামর্শ",
    safetyAdvice: {
      "Suspicious SMS": [
        "সন্দেহজনক মেসেজের উত্তর দেবেন না বা OTP, PIN, পাসওয়ার্ড শেয়ার করবেন না।",
        "অফিশিয়াল যোগাযোগ মাধ্যমে প্রেরকের পরিচয় যাচাই করুন।",
      ],
      "Phishing Link": [
        "অপরিচিত লিংক খুলবেন না বা সন্দেহজনক সাইটে ব্যক্তিগত তথ্য দেবেন না।",
        "ডোমেইনটি সতর্কভাবে পরীক্ষা করে অফিসিয়াল ওয়েবসাইট থেকে যাচাই করুন।",
      ],
      "Online Scam": [
        "অনুরোধটি নিজে থেকে যাচাই না করে টাকা পাঠাবেন না বা আর্থিক তথ্য শেয়ার করবেন না।",
        "নিজের রেকর্ডের জন্য সন্দেহজনক যোগাযোগের তথ্য সংরক্ষণ করতে পারেন।",
      ],
      "Fake Offer or Giveaway": [
        "পুরস্কার পেতে ফি বা সংবেদনশীল তথ্য চায়—এমন অফার সম্পর্কে সতর্ক থাকুন।",
        "প্রতিষ্ঠানের অফিসিয়াল মাধ্যমে প্রচারণাটি যাচাই করুন।",
      ],
      Impersonation: [
        "পরিচয় যাচাই করতে পরিচিত অফিসিয়াল মাধ্যমে ব্যক্তি বা প্রতিষ্ঠানের সঙ্গে যোগাযোগ করুন।",
        "যাচাই না করা কারও সঙ্গে কোড, পাসওয়ার্ড বা পেমেন্টের তথ্য শেয়ার করবেন না।",
      ],
      Other: [
        "উত্তর দেওয়া, লিংকে ক্লিক করা বা ব্যক্তিগত তথ্য শেয়ার করার আগে থামুন।",
        "অপ্রত্যাশিত অনুরোধ অফিসিয়াল মাধ্যমে যাচাই করুন।",
      ],
    },
    officialTitle: "অফিশিয়াল সহায়তা প্রয়োজন?",
    officialDescription:
      "Bipod Erao AI একটি সচেতনতামূলক টুল, আইন প্রয়োগকারী সংস্থা নয়। অফিসিয়াল সহায়তার জন্য যাচাইকৃত বাংলাদেশ সাইবার অপরাধ রিপোর্টিং রিসোর্স ব্যবহার করুন। যাচাইয়ের পর অফিসিয়াল লিংক এখানে যোগ করা হবে।",
    officialPending: "যাচাইকৃত অফিসিয়াল রিসোর্স এখানে তালিকাভুক্ত করা হবে।",
    requiredError: "জমা দেওয়ার আগে অনুগ্রহ করে সবগুলো ঘর পূরণ করুন।",
  },
};

const reportTypeKeys = [
  "Suspicious SMS",
  "Phishing Link",
  "Online Scam",
  "Fake Offer or Giveaway",
  "Impersonation",
  "Other",
];
const platformKeys = ["SMS", "WhatsApp", "Facebook", "Email", "Website", "Other"];

const emptyForm = {
  reportType: "",
  platform: "",
  details: "",
  description: "",
};

export default function Report({ isBangla }) {
  const text = isBangla ? translations.bn : translations.en;
  const [form, setForm] = useState(emptyForm);
  const [confirmation, setConfirmation] = useState(false);
  const [error, setError] = useState(false);
  const [confirmedReportType, setConfirmedReportType] = useState("");

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setError(false);
  }

  function handleSubmit(event) {
    event.preventDefault();
    if (Object.values(form).some((value) => !value.trim())) {
      setError(true);
      return;
    }

    setConfirmedReportType(form.reportType);
    setForm(emptyForm);
    setError(false);
    setConfirmation(true);
  }

  function handleAnotherReport() {
    setForm(emptyForm);
    setConfirmedReportType("");
    setError(false);
    setConfirmation(false);
  }

  return (
    <main className="report-page">
      <div className="report-page__content">
        <header className="report-heading">
          <h1>{text.title}</h1>
          <p>{text.subtitle}</p>
        </header>

        {confirmation ? (
          <section className="report-confirmation" aria-live="polite">
            <div className="report-confirmation__mark" aria-hidden="true">
              ✓
            </div>
            <h2>{text.confirmationTitle}</h2>
            <p className="report-confirmation__message">{text.confirmation}</p>

            <div className="report-advice">
              <h3>{text.safetyTitle}</h3>
              <ul>
                {text.safetyAdvice[confirmedReportType].map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>

            <button
              className="report-submit"
              type="button"
              onClick={handleAnotherReport}
            >
              {text.another}
              <span aria-hidden="true">→</span>
            </button>
          </section>
        ) : (
          <form className="report-form" onSubmit={handleSubmit} noValidate>
            <div className="report-form__grid">
              <label className="report-field">
                <span>{text.reportType}</span>
                <select
                  name="reportType"
                  value={form.reportType}
                  onChange={updateField}
                  required
                >
                  <option value="">{text.chooseReportType}</option>
                  {reportTypeKeys.map((key, index) => (
                    <option key={key} value={key}>
                      {text.reportTypes[index]}
                    </option>
                  ))}
                </select>
              </label>

              <label className="report-field">
                <span>{text.platform}</span>
                <select
                  name="platform"
                  value={form.platform}
                  onChange={updateField}
                  required
                >
                  <option value="">{text.choosePlatform}</option>
                  {platformKeys.map((key, index) => (
                    <option key={key} value={key}>
                      {text.platforms[index]}
                    </option>
                  ))}
                </select>
              </label>

              <label className="report-field report-field--full">
                <span>{text.detailsLabel}</span>
                <textarea
                  name="details"
                  value={form.details}
                  onChange={updateField}
                  placeholder={text.detailsPlaceholder}
                  rows={4}
                  required
                />
              </label>

              <label className="report-field report-field--full">
                <span>{text.descriptionLabel}</span>
                <textarea
                  name="description"
                  value={form.description}
                  onChange={updateField}
                  placeholder={text.descriptionPlaceholder}
                  rows={4}
                  required
                />
              </label>
            </div>

            {error && (
              <p className="report-form__error" role="alert">
                {text.requiredError}
              </p>
            )}

            <button className="report-submit" type="submit">
              {text.submit}
              <span aria-hidden="true">→</span>
            </button>
          </form>
        )}

        <aside className="official-help">
          <div className="official-help__icon" aria-hidden="true">
            i
          </div>
          <div>
            <h2>{text.officialTitle}</h2>
            <p>{text.officialDescription}</p>
            <div className="official-help__resources">{text.officialPending}</div>
          </div>
        </aside>
      </div>
    </main>
  );
}
