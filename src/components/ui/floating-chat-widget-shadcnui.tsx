import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ChatInput, ChatInputSubmit, ChatInputTextArea } from "@/components/ui/chat-input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AnimatePresence, motion, useReducedMotion, type Variants } from "framer-motion";
import {
  Baby,
  HeartHandshake,
  MessageSquare,
  NotebookPen,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { type ElementType, useCallback, useId, useState } from "react";

interface GuideMode {
  id: string;
  name: string;
  role: string;
  icon: ElementType;
  greeting: string;
}
interface ChatMessage {
  id: number;
  from: "user" | "guide";
  text: string;
}

const GUIDE_MODES: GuideMode[] = [
  {
    id: "general",
    name: "Femopedia AI",
    role: "General health education",
    icon: Sparkles,
    greeting:
      "Hi, I’m Femopedia AI. I can help you understand health information and prepare thoughtful next steps. What’s on your mind?",
  },
  {
    id: "pregnancy",
    name: "Pregnancy Guide",
    role: "Pregnancy education",
    icon: HeartHandshake,
    greeting:
      "I can help explain common pregnancy changes, questions to ask, and when professional care may be important.",
  },
  {
    id: "postpartum",
    name: "Postpartum Guide",
    role: "Recovery and new parent support",
    icon: Baby,
    greeting:
      "Your recovery and emotional wellbeing matter too. What would you like to understand today?",
  },
  {
    id: "journal",
    name: "Journal Guide",
    role: "Private reflection prompts",
    icon: NotebookPen,
    greeting:
      "I can help you reflect on patterns and prepare notes for a healthcare conversation. Where should we begin?",
  },
];

const containerVariants: Variants = {
  hidden: { opacity: 0, y: 20, scale: 0.96 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: "spring", damping: 25, stiffness: 300 },
  },
  exit: { opacity: 0, y: 15, scale: 0.97, transition: { duration: 0.18 } },
};

export function FloatingChatWidget({ initialOpen = false }: { initialOpen?: boolean }) {
  const [isOpen, setIsOpen] = useState(initialOpen);
  const [selectedMode, setSelectedMode] = useState(GUIDE_MODES[0].id);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const reducedMotion = useReducedMotion();
  const titleId = useId();
  const toggleOpen = useCallback(() => setIsOpen((open) => !open), []);
  const currentMode = GUIDE_MODES.find((mode) => mode.id === selectedMode) || GUIDE_MODES[0];
  const ModeIcon = currentMode.icon;

  const changeMode = (value: string) => {
    setSelectedMode(value);
    setMessages([]);
  };
  const submit = () => {
    const trimmed = message.trim();
    if (!trimmed) return;
    const nextId = Date.now();
    setMessages((current) => [
      ...current,
      { id: nextId, from: "user", text: trimmed },
      {
        id: nextId + 1,
        from: "guide",
        text: "Thanks for sharing that. Early access chat is a preview, so I can’t assess your situation yet. Femopedia is being designed to explain general possibilities, help you prepare questions, and clearly suggest professional care when needed.",
      },
    ]);
    setMessage("");
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3 sm:bottom-6 sm:right-6">
      <AnimatePresence>
        {isOpen && (
          <motion.aside
            key="chat-window"
            variants={reducedMotion ? undefined : containerVariants}
            initial={reducedMotion ? false : "hidden"}
            animate="visible"
            exit="exit"
            className="w-[min(380px,calc(100vw-2rem))] overflow-hidden rounded-[1.35rem] border border-border/70 bg-background/95 shadow-2xl backdrop-blur-xl"
            role="dialog"
            aria-modal="false"
            aria-labelledby={titleId}
          >
            <header className="relative overflow-hidden border-b border-border/70 bg-[linear-gradient(135deg,rgba(113,140,123,.18),rgba(119,116,174,.14))] p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <Avatar className="h-10 w-10 border border-white/70 bg-white shadow-sm">
                      <AvatarImage src="/brand/mark.svg" alt="" />
                      <AvatarFallback>F</AvatarFallback>
                    </Avatar>
                    <span className="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background bg-emerald-500" />
                  </div>
                  <div>
                    <h2 id={titleId} className="text-sm font-bold text-foreground">
                      {currentMode.name}
                    </h2>
                    <p className="text-[10px] text-muted-foreground">
                      Educational guidance · Preview
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setIsOpen(false)}
                  aria-label="Close Femopedia AI"
                >
                  <X />
                </Button>
              </div>
            </header>
            <div className="border-b border-border/60 p-3">
              <Select value={selectedMode} onValueChange={changeMode}>
                <SelectTrigger className="h-auto w-full border-0 bg-muted/60 px-3 py-2.5 shadow-none">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {GUIDE_MODES.map((mode) => {
                    const Icon = mode.icon;
                    return (
                      <SelectItem key={mode.id} value={mode.id}>
                        <span className="flex items-center gap-2.5">
                          <span className="grid h-7 w-7 place-items-center rounded-lg bg-primary/10 text-primary">
                            <Icon className="h-3.5 w-3.5" />
                          </span>
                          <span className="flex flex-col text-left">
                            <strong className="text-xs">{mode.name}</strong>
                            <small className="text-[9px] text-muted-foreground">{mode.role}</small>
                          </span>
                        </span>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
            <div
              className="flex h-[300px] flex-col gap-3 overflow-y-auto bg-gradient-to-b from-background to-muted/30 p-4"
              aria-live="polite"
            >
              <div className="flex gap-2.5">
                <Avatar className="h-7 w-7 border border-border bg-white">
                  <AvatarImage src="/brand/mark.svg" />
                  <AvatarFallback>F</AvatarFallback>
                </Avatar>
                <div className="max-w-[84%]">
                  <span className="mb-1 block text-[9px] font-bold text-muted-foreground">
                    {currentMode.name}
                  </span>
                  <div className="rounded-2xl rounded-tl-sm border border-border/60 bg-card px-3.5 py-2.5 text-xs leading-relaxed shadow-sm">
                    {currentMode.greeting}
                  </div>
                </div>
              </div>
              {messages.map((item) => (
                <motion.div
                  initial={reducedMotion ? false : { opacity: 0, y: 7 }}
                  animate={{ opacity: 1, y: 0 }}
                  key={item.id}
                  className={
                    item.from === "user"
                      ? "ml-auto max-w-[84%] rounded-2xl rounded-tr-sm bg-primary px-3.5 py-2.5 text-xs leading-relaxed text-primary-foreground"
                      : "max-w-[84%] rounded-2xl rounded-tl-sm border border-border/60 bg-card px-3.5 py-2.5 text-xs leading-relaxed shadow-sm"
                  }
                >
                  {item.text}
                </motion.div>
              ))}
              <div className="mt-auto flex items-start gap-2 rounded-xl bg-secondary/70 px-3 py-2 text-[9px] leading-relaxed text-secondary-foreground">
                <ShieldCheck className="mt-0.5 h-3 w-3 shrink-0" /> Femopedia does not diagnose or
                replace professional medical care. If symptoms are severe or urgent, contact local
                emergency services.
              </div>
            </div>
            <div className="border-t border-border/60 bg-background p-3">
              <label htmlFor={`${titleId}-message`} className="sr-only">
                Message Femopedia AI
              </label>
              <ChatInput
                variant="default"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                onSubmit={submit}
                rows={1}
                className="flex-row rounded-2xl bg-muted/35 p-1.5 pl-2"
              >
                <ChatInputTextArea
                  id={`${titleId}-message`}
                  aria-label={`Message ${currentMode.name}`}
                  placeholder={`Message ${currentMode.name}…`}
                  className="min-w-0 flex-1 bg-transparent px-2 py-2 text-xs"
                />
                <ChatInputSubmit />
              </ChatInput>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
      <motion.button
        whileHover={reducedMotion ? undefined : { scale: 1.05 }}
        whileTap={reducedMotion ? undefined : { scale: 0.95 }}
        onClick={toggleOpen}
        className={
          isOpen
            ? "grid h-14 w-14 cursor-pointer place-items-center rounded-full bg-foreground text-background shadow-2xl"
            : "group relative grid h-14 w-14 cursor-pointer place-items-center rounded-full bg-primary text-primary-foreground shadow-2xl"
        }
        aria-label={isOpen ? "Close Femopedia AI" : "Open Femopedia AI"}
        aria-expanded={isOpen}
      >
        <span className="absolute inset-0 -z-10 rounded-full bg-primary/30 blur-xl" />
        {isOpen ? (
          <X className="h-5 w-5" />
        ) : (
          <>
            <MessageSquare className="h-5 w-5" />
            <span className="absolute -right-1 -top-1 h-4 w-4 rounded-full border-2 border-background bg-emerald-500" />
          </>
        )}
      </motion.button>
    </div>
  );
}
