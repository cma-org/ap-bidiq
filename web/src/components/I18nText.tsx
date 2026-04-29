"use client";
import { useEffect, useState } from "react";
import type { Lang } from "@/lib/i18n";
import { t } from "@/lib/i18n";

/** Client-side text wrapper that re-renders when the lang switcher fires. */
export function I18nText({ k, fallback }: { k: Parameters<typeof t>[1]; fallback?: string }) {
  const [lang, setLang] = useState<Lang>("en");

  useEffect(() => {
    const stored = (typeof window !== "undefined" && localStorage.getItem("apbidiq-lang")) as Lang | null;
    if (stored === "te" || stored === "en") setLang(stored);
    function onChange(e: Event) {
      const ce = e as CustomEvent<Lang>;
      setLang(ce.detail);
    }
    window.addEventListener("apbidiq-lang-changed", onChange);
    return () => window.removeEventListener("apbidiq-lang-changed", onChange);
  }, []);

  return <>{t(lang, k) || fallback || k}</>;
}
