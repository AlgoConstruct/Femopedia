export function Blobs({ className = "" }: { className?: string }) {
  return (
    <div className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`} aria-hidden>
      <div
        className="blob size-[38rem] -left-40 -top-52 bg-primary/40"
        style={{ animationDelay: "0s" }}
      />
      <div
        className="blob size-[30rem] -right-32 top-10 bg-accent/35"
        style={{ animationDelay: "-6s" }}
      />
      <div
        className="blob size-[26rem] left-1/3 top-[60%] bg-secondary/40"
        style={{ animationDelay: "-12s" }}
      />
    </div>
  );
}