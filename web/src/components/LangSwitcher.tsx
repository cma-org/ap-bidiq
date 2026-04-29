"use client";
import { useEffect, useState } from "react";
import type { Lang } from "@/lib/i18n";
import { LANG_NAMES } from "@/lib/i18n";

export function LangSwitcher() {
  const [lang, setLang] = useState<Lang>("en");

  useEffect(() => {
    const stored = (typeof window !== "undefined" && localStorage.getItem("apbidiq-lang")) as Lang | null;
    if (stored && (stored === "en" || stored === "te")) setLang(stored);
  }, []);

  function update(next: Lang) {
    setLang(next);
    if (typeof window !== "undefined") {
      localStorage.setItem("apbidiq-lang", next);
      // Apply lang attr so CSS / screen readers see it.
      document.documentElement.setAttribute("lang", next);
      // Trigger a re-render of pages relying on lang via custom event.
      window.dispatchEvent(new CustomEvent("apbidiq-lang-changed", { detail: next }));
    }
  }

  return (
    <div className="flex items-center gap-0.5 rounded-md border border-slate-200 bg-white p-0.5 ml-2">
      {(Object.keys(LANG_NAMES) as Lang[]).map((l) => (
        <button
          key={l}
          onClick={() => update(l)}
          className={
            "px-2 py-0.5 rounded-sm text-xs font-medium transition " +
            (lang === l
              ? "bg-sky-700 text-white"
              : "text-slate-600 hover:bg-slate-100")
          }
          title={LANG_NAMES[l]}
        >
          {l === "en" ? "EN" : "తె"}
        </button>
      ))}
    </div>
  );
}
