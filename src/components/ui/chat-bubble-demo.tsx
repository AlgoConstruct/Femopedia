"use client";

import { VoiceChat, type VoiceChatUser } from "@/components/ui/chat-bubble";

const communityMembers: VoiceChatUser[] = [
  { id: "member-1", name: "Maya", avatarUrl: "/images/perspectives/maya.webp", isSpeaking: true },
  { id: "member-2", name: "Priya", avatarUrl: "/images/perspectives/priya.webp" },
  { id: "member-3", name: "Leah", avatarUrl: "/images/perspectives/leah.webp" },
  { id: "member-4", name: "Sofia", avatarUrl: "/images/perspectives/sofia.webp" },
  { id: "member-5", name: "Amara", avatarUrl: "/images/perspectives/amara.webp" },
  { id: "member-6", name: "Nina", avatarUrl: "/images/perspectives/nina.webp" },
  { id: "member-7", name: "Elena", avatarUrl: "/images/perspectives/elena.webp" },
];

export default function VoiceChatDemo() {
  return (
    <div className="flex min-h-52 items-start justify-center rounded-2xl bg-background p-8">
      <VoiceChat
        users={communityMembers}
        onJoin={() => {
          // Connect this callback to the future Femopedia Community voice-room flow.
        }}
      />
    </div>
  );
}
