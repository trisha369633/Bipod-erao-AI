import "./Navbar.css";

const labels = {
  en: {
    home: "Home",
    message: "Message Check",
    link: "Link Check",
    report: "Report",
  },
  bn: {
    home: "হোম",
    message: "মেসেজ চেক",
    link: "লিংক চেক",
    report: "রিপোর্ট",
  },
};

export default function Navbar({
  isBangla,
  onLanguageChange,
  onNavigate,
  pathname,
}) {
  const text = isBangla ? labels.bn : labels.en;

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <a
          className="brand"
          href="/"
          onClick={(event) => onNavigate(event, "/")}
          aria-label="Bipod Erao AI home"
        >
          <span className="brand__mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none">
              <path
                d="M3 16c3.5-5.8 7.8-8.7 13-8.7S25.5 10.2 29 16c-3.5 5.8-7.8 8.7-13 8.7S6.5 21.8 3 16Z"
                stroke="currentColor"
                strokeWidth="1.8"
              />
              <circle cx="16" cy="16" r="4" fill="currentColor" />
            </svg>
          </span>
          <span>Bipod Erao AI</span>
        </a>

        <nav
          className="main-nav"
          aria-label={isBangla ? "প্রধান নেভিগেশন" : "Main navigation"}
        >
          <a
            className={`main-nav__link${pathname === "/" ? " main-nav__link--active" : ""}`}
            href="/"
            onClick={(event) => onNavigate(event, "/")}
            aria-current={pathname === "/" ? "page" : undefined}
          >
            {text.home}
          </a>
          <a
            className={`main-nav__link${pathname === "/message-check" ? " main-nav__link--active" : ""}`}
            href="/message-check"
            onClick={(event) => onNavigate(event, "/message-check")}
            aria-current={pathname === "/message-check" ? "page" : undefined}
          >
            {text.message}
          </a>
          <a
            className={`main-nav__link${pathname === "/link-check" ? " main-nav__link--active" : ""}`}
            href="/link-check"
            onClick={(event) => onNavigate(event, "/link-check")}
            aria-current={pathname === "/link-check" ? "page" : undefined}
          >
            {text.link}
          </a>
          <a
            className={`main-nav__link${pathname === "/report" ? " main-nav__link--active" : ""}`}
            href="/report"
            onClick={(event) => onNavigate(event, "/report")}
            aria-current={pathname === "/report" ? "page" : undefined}
          >
            {text.report}
          </a>
        </nav>

        <label className="language-toggle">
          <span
            className={
              isBangla
                ? "language-toggle__label is-active"
                : "language-toggle__label"
            }
          >
            বাং
          </span>
          <input
            aria-label={
              isBangla ? "Switch language to English" : "Switch language to Bangla"
            }
            checked={isBangla}
            onChange={(event) => onLanguageChange(event.target.checked)}
            role="switch"
            type="checkbox"
          />
          <span className="language-toggle__track" aria-hidden="true">
            <span className="language-toggle__thumb" />
          </span>
          <span
            className={
              !isBangla
                ? "language-toggle__label is-active"
                : "language-toggle__label"
            }
          >
            EN
          </span>
        </label>
      </div>
    </header>
  );
}