import { lazy, Suspense, useState } from "react";
import { MessageSquare } from "lucide-react";

const FloatingChatWidget = lazy(() =>
  import("@/components/ui/floating-chat-widget-shadcnui").then(({ FloatingChatWidget }) => ({
    default: FloatingChatWidget,
  })),
);

export function DeferredChatWidget() {
  const [activated, setActivated] = useState(false);
  const launcher = (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3 sm:bottom-6 sm:right-6">
      <button
        type="button"
        onClick={() => setActivated(true)}
        className="group relative grid h-14 w-14 cursor-pointer place-items-center rounded-full bg-primary text-primary-foreground shadow-2xl"
        aria-label="Open Femopedia AI"
        aria-expanded="false"
      >
        <span className="absolute inset-0 -z-10 rounded-full bg-primary/30 blur-xl" />
        <MessageSquare className="h-5 w-5" aria-hidden="true" />
        <span className="absolute -right-1 -top-1 h-4 w-4 rounded-full border-2 border-background bg-emerald-500" />
      </button>
    </div>
  );

  if (!activated) return launcher;
  return (
    <Suspense fallback={launcher}>
      <FloatingChatWidget initialOpen />
    </Suspense>
  );
}
