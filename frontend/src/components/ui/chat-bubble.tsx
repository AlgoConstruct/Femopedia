"use client";

import * as React from "react";
import { AnimatePresence, motion, type Variants } from "framer-motion";
import { ChevronRight, Mic } from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

export interface VoiceChatUser {
  id: string;
  name: string;
  avatarUrl: string;
  isSpeaking?: boolean;
}

export interface VoiceChatProps {
  users: VoiceChatUser[];
  maxVisibleAvatars?: number;
  onJoin: () => void;
  className?: string;
}

const indicatorHeights = ["35%", "80%", "52%"];

function SpeakingIndicator() {
  return (
    <span
      className="absolute -left-1 -top-1 flex size-6 items-center justify-center rounded-full bg-card p-0.5"
      aria-label="Speaking"
    >
      <span className="flex size-full items-end justify-center gap-0.5 rounded-full bg-primary p-1">
        {indicatorHeights.map((height, index) => (
          <motion.span
            key={height}
            className="w-1 rounded-full bg-primary-foreground"
            initial={{ height }}
            animate={{ height: [height, "100%", "25%", height] }}
            transition={{
              duration: 0.9,
              delay: index * 0.12,
              repeat: Number.POSITIVE_INFINITY,
              ease: "easeInOut",
            }}
          />
        ))}
      </span>
    </span>
  );
}

function UserAvatar({ user, size = "small" }: { user: VoiceChatUser; size?: "small" | "large" }) {
  const initials = user.name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="relative">
      <Avatar className={cn(size === "large" ? "size-14" : "size-10", "border-2 border-card")}>
        <AvatarImage src={user.avatarUrl} alt={user.name} className="object-cover" />
        <AvatarFallback>{initials}</AvatarFallback>
      </Avatar>
      {user.isSpeaking ? <SpeakingIndicator /> : null}
    </div>
  );
}

const popoverVariants: Variants = {
  hidden: { opacity: 0, scale: 0.95, y: -20 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { duration: 0.2, ease: "easeOut" },
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: -20,
    transition: { duration: 0.15, ease: "easeIn" },
  },
};

export function VoiceChat({ users, maxVisibleAvatars = 4, onJoin, className }: VoiceChatProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const visibleUsers = users.slice(0, maxVisibleAvatars);
  const hiddenUsersCount = Math.max(0, users.length - maxVisibleAvatars);
  const hasSpeaker = visibleUsers.some((user) => user.isSpeaking);

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn(
            "group relative flex min-h-14 max-w-full cursor-pointer items-center justify-center rounded-full border bg-card p-2 pr-4 shadow-sm transition-colors hover:border-primary/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            className,
          )}
          aria-label={`Open voice chat with ${users.length} participants`}
        >
          <span className="relative flex size-10 shrink-0 items-center justify-center rounded-full bg-muted">
            <Mic className="size-5 text-muted-foreground" aria-hidden="true" />
            {hasSpeaker ? <SpeakingIndicator /> : null}
          </span>
          <span className="ml-2 flex -space-x-4" aria-hidden="true">
            {visibleUsers.map((user) => (
              <UserAvatar key={user.id} user={{ ...user, isSpeaking: false }} />
            ))}
          </span>
          {hiddenUsersCount > 0 ? (
            <span className="ml-3 text-sm font-medium text-muted-foreground">
              +{hiddenUsersCount}
            </span>
          ) : null}
          <ChevronRight
            className="ml-1 size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-1"
            aria-hidden="true"
          />
        </button>
      </PopoverTrigger>

      <AnimatePresence>
        {isOpen ? (
          <PopoverContent
            sideOffset={12}
            align="start"
            collisionPadding={16}
            className="w-[min(20rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border-none bg-transparent p-0 shadow-2xl"
          >
            <motion.div
              initial="hidden"
              animate="visible"
              exit="exit"
              variants={popoverVariants}
              className="flex flex-col overflow-hidden rounded-2xl border bg-card"
              style={{ transformOrigin: "var(--radix-popover-content-transform-origin)" }}
            >
              <div className="p-6 pb-4">
                <h2 className="text-center text-lg font-semibold">Voice chat</h2>
                <p className="mt-1 text-center text-xs text-muted-foreground" aria-live="polite">
                  {users.length} {users.length === 1 ? "participant" : "participants"}
                </p>
              </div>
              <div className="grid grid-cols-4 gap-x-2 gap-y-6 p-6 pt-0">
                {users.map((user, index) => (
                  <motion.div
                    key={user.id}
                    className="flex min-w-0 flex-col items-center gap-2"
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.08 + index * 0.04, duration: 0.25 }}
                  >
                    <UserAvatar user={user} size="large" />
                    <span className="w-full truncate text-center text-xs font-medium text-foreground">
                      {user.name}
                    </span>
                  </motion.div>
                ))}
              </div>
              <Separator />
              <div className="flex flex-col gap-2 bg-muted/50 p-6">
                <Button
                  size="lg"
                  className="w-full"
                  onClick={() => {
                    onJoin();
                    setIsOpen(false);
                  }}
                >
                  Join now
                </Button>
                <p className="text-center text-xs text-muted-foreground">
                  Your microphone will be muted initially.
                </p>
              </div>
            </motion.div>
          </PopoverContent>
        ) : null}
      </AnimatePresence>
    </Popover>
  );
}
