export function HyrepathLogo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className}>
      {/* H shape representing Hyrepath */}
      <path d="M4 6h4v12H4V6zm12 0h4v12h-4V6z" fill="currentColor" />
      <path d="M8 11h8v2H8v-2z" fill="currentColor" />
    </svg>
  );
}
