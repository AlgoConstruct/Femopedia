"use client";

import { VoiceChat, type VoiceChatUser } from "@/components/ui/chat-bubble";

const previewMembers: VoiceChatUser[] = [
  { id: "maya", name: "Maya", avatarUrl: "/images/perspectives/maya.webp", isSpeaking: true },
  { id: "priya", name: "Priya", avatarUrl: "/images/perspectives/priya.webp" },
  { id: "leah", name: "Leah", avatarUrl: "/images/perspectives/leah.webp" },
  { id: "sofia", name: "Sofia", avatarUrl: "/images/perspectives/sofia.webp" },
  { id: "amara", name: "Amara", avatarUrl: "/images/perspectives/amara.webp" },
];

export function CommunityVoicePreview() {
  return (
    <VoiceChat
      users={previewMembers}
      maxVisibleAvatars={3}
      className="mt-5 self-start"
      onJoin={() => document.querySelector("#early-access")?.scrollIntoView({ behavior: "smooth" })}
    />
  );
}
