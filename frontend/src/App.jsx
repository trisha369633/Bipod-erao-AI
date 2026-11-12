import { useState, useCallback, useEffect } from "react";
import SplashScreen from "./pages/SplashScreen";
import Home from "./pages/Home";
import MessageCheck from "./pages/MessageCheck";
import LinkCheck from "./pages/LinkCheck";
import Report from "./pages/Report";
import Navbar from "./components/Navbar";

export default function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [isBangla, setIsBangla] = useState(false);
  const [pathname, setPathname] = useState(window.location.pathname);
  const handleFinish = useCallback(() => setShowSplash(false), []);

  useEffect(() => {
    const handlePopState = () => setPathname(window.location.pathname);
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigate = useCallback((event, path) => {
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return;
    }

    event.preventDefault();
    if (window.location.pathname !== path) {
      window.history.pushState({}, "", path);
      setPathname(path);
    }
  }, []);

  const page =
    pathname === "/message-check" ? (
      <MessageCheck isBangla={isBangla} />
    ) : pathname === "/link-check" ? (
      <LinkCheck isBangla={isBangla} />
    ) : pathname === "/report" ? (
      <Report isBangla={isBangla} />
    ) : (
      <Home isBangla={isBangla} onNavigate={navigate} />
    );

  return (
    <>
      <div className="page-fade-in">
        <Navbar
          isBangla={isBangla}
          onLanguageChange={setIsBangla}
          onNavigate={navigate}
          pathname={pathname}
        />
        {page}
      </div>

      {showSplash && <SplashScreen onFinish={handleFinish} />}
    </>
  );
}