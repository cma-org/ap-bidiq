"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiBase } from "@/lib/api";

export function DetectAnomaliesButton({ tenderId }: { tenderId: number }) {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function run() {
    setLoading(true);
    try {
      await fetch(`${apiBase}/anomalies/detect?tender_id=${tenderId}`, { method: "POST" });
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
      {loading ? "Scanning…" : "Re-run detection"}
    </button>
  );
}
