"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiBase } from "@/lib/api";

export function ValidateAllButton({ tenderId }: { tenderId: number }) {
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const router = useRouter();

  async function run() {
    setLoading(true);
    setDone(false);
    try {
      await fetch(`${apiBase}/bids/validate-all?tender_id=${tenderId}`, { method: "POST" });
      setDone(true);
      router.refresh();
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={run}
      disabled={loading}
      className="rounded-lg bg-sky-700 hover:bg-sky-800 text-white text-sm font-medium px-4 py-2 shadow-sm transition disabled:opacity-60"
    >
      {loading ? "Evaluating…" : done ? "✓ Re-evaluated" : "Re-evaluate all bids"}
    </button>
  );
}
