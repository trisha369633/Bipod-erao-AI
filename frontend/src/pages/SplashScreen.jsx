import { useEffect, useState } from "react";
import "./SplashScreen.css";

const BRAND = "Bipod Erao AI";

// Timeline (ms): letters finish ≈ 2.7s, slide ≈ 3.8s, fade-out starts 4.2s
const LEAVE_AT = 4200;
const FINISH_AT = 4900;

function EyeIcon() {
  return (
    <svg
      className="splash__eye"
      viewBox="0 0 64 64"
      fill="none"
      aria-hidden="true"
    >
      <path
        className="splash__eye-outline"
        pathLength="1"
        d="M4 32C12 18 22 12 32 12s20 6 28 20c-8 14-18 20-28 20S12 46 4 32Z"
      />
      <circle className="splash__eye-iris" pathLength="1" cx="32" cy="32" r="9" />
      <circle className="splash__eye-pupil" cx="32" cy="32" r="3.5" />
    </svg>
  );
}

export default function SplashScreen({ onFinish }) {
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const leaveTimer = setTimeout(() => setLeaving(true), LEAVE_AT);
    const finishTimer = setTimeout(() => onFinish?.(), FINISH_AT);
    return () => {
      clearTimeout(leaveTimer);
      clearTimeout(finishTimer);
    };
  }, [onFinish]);

  return (
    <div className={`splash ${leaving ? "splash--leaving" : ""}`}>
      <EyeIcon />

      <h1 className="splash__title" aria-label={BRAND}>
        {BRAND.split("").map((char, i) => (
          <span
            key={i}
            className="splash__letter"
            style={{ "--i": i }}
            aria-hidden="true"
          >
            {char === " " ? "\u00A0" : char}
          </span>
        ))}
      </h1>
    </div>
  );
}