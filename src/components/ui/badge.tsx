import { cn } from "@/lib/utils";

const tones = {
  mute: "border-line text-muted",
  pass: "border-pass/40 text-pass",
  lock: "border-lock/40 text-lock",
  fragile: "border-fragile/40 text-fragile",
  missing: "border-missing/40 text-missing",
};

export function Badge({
  children,
  tone = "mute",
}: {
  children: React.ReactNode;
  tone?: keyof typeof tones;
}) {
  return (
    <span className={cn("inline-flex rounded-sm border px-2 py-0.5 font-mono text-[11px] tracking-wide", tones[tone])}>
      {children}
    </span>
  );
}
