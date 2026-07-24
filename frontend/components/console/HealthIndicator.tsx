"use client";

import { useHealth } from "@/hooks/useHealth";
import { cn } from "@/src/lib/utils";

export function HealthIndicator() {
  const { online, loading } = useHealth();

  return (
    <div className="flex items-center gap-2 rounded-lg border border-border/60 bg-card/50 px-3 py-2 text-xs shadow-sm backdrop-blur">
      <span
        className={cn(
          "relative size-2 rounded-full",
          loading ? "bg-muted-foreground" : online ? "bg-emerald-500" : "bg-red-500",
        )}
        aria-hidden
      >
        {online && !loading && (
          <span className="absolute inset-0 size-2 animate-ping rounded-full bg-emerald-500 opacity-75" />
        )}
      </span>
      <span className="font-medium text-foreground">
        {loading ? "Checking…" : online ? "API online" : "Offline"}
      </span>
    </div>
  );
}
