import Link from "next/link";
import type { ReactNode } from "react";
import { LangSwitcher } from "@/components/LangSwitcher";
import { I18nText } from "@/components/I18nText";

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      <Footer />
    </div>
  );
}

function Header() {
  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-sky-700 to-cyan-600 grid place-items-center text-white font-bold shadow-sm">
            B
          </div>
          <div className="leading-tight">
            <div className="text-base font-semibold text-slate-900 group-hover:text-sky-800">AP-BidIQ</div>
            <div className="text-xs text-slate-500">Bid Evaluation for AP Procurement</div>
          </div>
        </Link>
        <nav className="flex items-center gap-1">
          <NavLink href="/"><I18nText k="nav_tenders" /></NavLink>
          <NavLink href="/tenders/1/bids"><I18nText k="nav_bids" /></NavLink>
          <NavLink href="/tenders/1/compare"><I18nText k="nav_compare" /></NavLink>
          <NavLink href="/tenders/1/anomalies"><I18nText k="nav_anomalies" /></NavLink>
          <NavLink href="/tenders/1/benchmark"><I18nText k="nav_benchmark" /></NavLink>
          <NavLink href="/draft"><I18nText k="nav_drafting" /></NavLink>
          <NavLink href="/upload">Upload</NavLink>
          <NavLink href="/audit"><I18nText k="nav_audit" /></NavLink>
          <LangSwitcher />
        </nav>
      </div>
    </header>
  );
}

function NavLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link
      href={href}
      className="px-3 py-1.5 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition"
    >
      {children}
    </Link>
  );
}

function Footer() {
  return (
    <footer className="mt-16 border-t border-slate-200 bg-white">
      <div className="max-w-7xl mx-auto px-6 py-6 text-xs text-slate-500 flex items-center justify-between">
        <div>
          AP-BidIQ — Hackathon Demo · Infrastructure & Investment Department, Government of Andhra Pradesh
        </div>
        <div>v0.1 · {new Date().getFullYear()}</div>
      </div>
    </footer>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
  breadcrumbs,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  breadcrumbs?: { href: string; label: string }[];
}) {
  return (
    <div className="mb-8">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="mb-2 text-xs text-slate-500 flex items-center gap-1.5">
          {breadcrumbs.map((b, i) => (
            <span key={b.href} className="flex items-center gap-1.5">
              <Link href={b.href} className="hover:text-sky-700">{b.label}</Link>
              {i < breadcrumbs.length - 1 && <span className="text-slate-300">/</span>}
            </span>
          ))}
        </nav>
      )}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-slate-600">{subtitle}</p>}
        </div>
        {actions && <div className="shrink-0 flex items-center gap-2">{actions}</div>}
      </div>
    </div>
  );
}
