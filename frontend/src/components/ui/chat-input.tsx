import {
  createContext,
  useContext,
  type ChangeEventHandler,
  type ComponentProps,
  type ReactNode,
} from "react";
import { ArrowUpIcon, SquareIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useTextareaResize } from "@/hooks/use-textarea-resize";
import { cn } from "@/lib/utils";

interface ChatInputContextValue {
  value?: string;
  onChange?: ChangeEventHandler<HTMLTextAreaElement>;
  onSubmit?: () => void;
  loading?: boolean;
  onStop?: () => void;
  variant?: "default" | "unstyled";
  rows?: number;
}

const ChatInputContext = createContext<ChatInputContextValue>({});

interface ChatInputProps extends Omit<ChatInputContextValue, "variant"> {
  children: ReactNode;
  className?: string;
  variant?: "default" | "unstyled";
}

function ChatInput({
  children,
  className,
  variant = "default",
  value,
  onChange,
  onSubmit,
  loading,
  onStop,
  rows = 1,
}: ChatInputProps) {
  return (
    <ChatInputContext.Provider
      value={{ value, onChange, onSubmit, loading, onStop, variant, rows }}
    >
      <div
        className={cn(
          variant === "default" &&
            "flex w-full flex-col items-end rounded-2xl border border-input bg-transparent p-2 focus-within:ring-1 focus-within:ring-ring",
          variant === "unstyled" && "flex w-full items-end gap-2",
          className,
        )}
      >
        {children}
      </div>
    </ChatInputContext.Provider>
  );
}

interface ChatInputTextAreaProps extends ComponentProps<typeof Textarea> {
  onSubmit?: () => void;
  variant?: "default" | "unstyled";
}

function ChatInputTextArea({
  onSubmit: onSubmitProp,
  value: valueProp,
  onChange: onChangeProp,
  className,
  variant: variantProp,
  ...props
}: ChatInputTextAreaProps) {
  const context = useContext(ChatInputContext);
  const value = valueProp ?? context.value ?? "";
  const onSubmit = onSubmitProp ?? context.onSubmit;
  const variant = variantProp ?? (context.variant === "default" ? "unstyled" : "default");
  const textareaRef = useTextareaResize(value, context.rows ?? 1);

  return (
    <Textarea
      ref={textareaRef}
      {...props}
      value={value}
      onChange={onChangeProp ?? context.onChange}
      onKeyDown={(event) => {
        props.onKeyDown?.(event);
        if (event.defaultPrevented || !onSubmit) return;
        if (event.key === "Enter" && !event.shiftKey && String(value).trim()) {
          event.preventDefault();
          onSubmit();
        }
      }}
      className={cn(
        "max-h-[160px] min-h-0 resize-none overflow-x-hidden",
        variant === "unstyled" && "border-none shadow-none focus-visible:ring-0",
        className,
      )}
      rows={context.rows ?? 1}
    />
  );
}

interface ChatInputSubmitProps extends ComponentProps<typeof Button> {
  onSubmit?: () => void;
  loading?: boolean;
  onStop?: () => void;
}

function ChatInputSubmit({
  onSubmit: onSubmitProp,
  loading: loadingProp,
  onStop: onStopProp,
  className,
  ...props
}: ChatInputSubmitProps) {
  const context = useContext(ChatInputContext);
  const loading = loadingProp ?? context.loading;
  const onStop = onStopProp ?? context.onStop;
  const isDisabled = typeof context.value !== "string" || context.value.trim().length === 0;

  if (loading && onStop) {
    return (
      <Button
        type="button"
        size="icon"
        onClick={onStop}
        className={cn("h-9 w-9 shrink-0 rounded-full", className)}
        aria-label="Stop response"
        {...props}
      >
        <SquareIcon />
      </Button>
    );
  }

  return (
    <Button
      type="button"
      size="icon"
      className={cn("h-9 w-9 shrink-0 rounded-full", className)}
      disabled={isDisabled}
      onClick={() => {
        if (!isDisabled) (onSubmitProp ?? context.onSubmit)?.();
      }}
      aria-label="Send message"
      {...props}
    >
      <ArrowUpIcon />
    </Button>
  );
}

export { ChatInput, ChatInputSubmit, ChatInputTextArea };
