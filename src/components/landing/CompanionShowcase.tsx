import { AnimatePresence, motion } from "framer-motion";
import { Sparkle } from "lucide-react";
import { useEffect, useState } from "react";

import { SectionHeading } from "@/components/landing/Reveal";
import { Button } from "@/components/ui/button";

type Turn = { role: "user" | "ai"; text: string };

const conversations: { id: string; label: string; turns: Turn[] }[] = [
  {
    id: "cycle",
    label: "Cycle",
    turns: [
      { role: "user", text: "My period is four days late and I'm not pregnant." },
      {
        role: "ai",
        text: "Late cycles often follow stress, travel or sleep changes—your sleep dropped 90 minutes last week. Let's watch the next two cycles together, and if it happens a third time it's worth a conversation with your clinician.",
      },
      { role: "user", text: "That's reassuring. Can you remind me to check in?" },
      { role: "ai", text: "Done. I'll check in on day 28 with a short two-question review." },
    ],
  },
  {
    id: "pregnancy",
    label: "Pregnancy",
    turns: [
      { role: "user", text: "I'm 22 weeks and my back aches constantly." },
      {
        role: "ai",
        text: "Very common in the second trimester as your centre of gravity shifts. Side-sleeping with a pillow between the knees and daily pelvic tilts help most people. If the pain becomes sharp or one-sided, tell your midwife the same day.",
      },
      { role: "user", text: "What should I ask at my next appointment?" },
      { role: "ai", text: "I've drafted three questions on posture, iron levels and glucose screening." },
    ],
  },
  {
    id: "mental-health",
    label: "Mental Health",
    turns: [
      { role: "user", text: "I feel flat and I can't tell why." },
      {
        role: "ai",
        text: "Thank you for telling me. Flatness is real information, not a failure. Your last three check-ins show lower energy and less time outside. Would a five-minute grounding exercise help now, or would you rather just talk?",
      },
      { role: "user", text: "Let's talk." },
      { role: "ai", text: "I'm here. What did today ask of you that felt heaviest?" },
    ],
  },
  {
    id: "baby-care",
    label: "Baby Care",
    turns: [
      { role: "user", text: "She wakes every 90 minutes at 4 months old." },
      {
        role: "ai",
        text: "That timing matches the four-month sleep progression—shorter cycles are developmentally normal. A consistent wind-down and a slightly earlier bedtime usually help within two weeks.",
      },
      { role: "user", text: "And feeding at night?" },
      { role: "ai", text: "At four months night feeds are still expected. I'll track her pattern for you." },
    ],
  },
  {
    id: "nutrition",
    label: "Nutrition",
    turns: [
      { role: "user", text: "What should I eat during the luteal phase?" },
      {
        role: "ai",
        text: "Steady blood sugar helps most: protein at breakfast, magnesium-rich foods like pumpkin seeds and leafy greens, and slower carbohydrates in the evening to ease cravings.",
      },
      { role: "user", text: "Give me three easy dinners." },
      { role: "ai", text: "Salmon with quinoa, lentil dal with spinach, and a chicken-and-sweet-potato tray bake." },
    ],
  },
];

export function CompanionShowcase() {
  const [tab, setTab] = useState(conversations[0]!.id);
  const active = conversations.find((c) => c.id === tab) ?? conversations[0]!;
  const [visible, setVisible] = useState(1);

  useEffect(() => {
    setVisible(1);
    const timers = active.turns.map((_, i) =>
      window.setTimeout(() => setVisible(i + 1), i * 900),
    );
    return () => timers.forEach(window.clearTimeout);
  }, [active]);

  return (
    <section id="companion" className="relative overflow-hidden py-24 sm:py-32">
      <div className="animated-gradient pointer-events-none absolute inset-x-0 top-1/4 h-1/2 opacity-40 blur-3xl" />
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6">
        <SectionHeading
          eyebrow="AI companion"
          title="See how Aria actually talks"
          description="Real conversation patterns from our closed beta—calm, specific, and always clear about the limits of AI."
        />

        <div className="mt-14 grid items-center gap-14 lg:grid-cols-[1fr_auto]">
          <div>
            <div role="tablist" aria-label="Conversation topics" className="flex flex-wrap gap-2">
              {conversations.map((c) => (
                <Button
                  key={c.id}
                  role="tab"
                  aria-selected={tab === c.id}
                  variant={tab === c.id ? "hero" : "outline"}
                  onClick={() => setTab(c.id)}
                >
                  {c.label}
                </Button>
              ))}
            </div>
            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              {[
                { t: "Context that carries", d: "Aria references your history instead of asking again." },
                { t: "Evidence-informed", d: "Guidance mapped to current clinical literature." },
                { t: "Escalates honestly", d: "Flags when a symptom needs a real clinician, fast." },
                { t: "Never judgmental", d: "No shame, no scolding—whatever you bring." },
              ].map((item) => (
                <div key={item.t} className="card-soft rounded-2xl p-5">
                  <p className="text-sm font-semibold text-foreground">{item.t}</p>
                  <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{item.d}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="mx-auto w-[19.5rem]">
            <div className="rounded-[2.75rem] border border-border bg-surface p-3 shadow-[var(--shadow-lift)]">
              <div className="relative h-[36rem] overflow-hidden rounded-[2.25rem] bg-background">
                <div className="mx-auto mt-3 h-6 w-24 rounded-full bg-muted" />
                <div className="flex items-center gap-2.5 px-5 pb-3 pt-4">
                  <span className="grid size-8 place-items-center rounded-full bg-primary/12 text-primary">
                    <Sparkle className="size-4" />
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-foreground">Aria</p>
                    <p className="text-[0.7rem] text-muted-foreground">{active.label} support</p>
                  </div>
                </div>
                <div className="space-y-3 px-4 pb-6">
                  <AnimatePresence mode="popLayout">
                    {active.turns.slice(0, visible).map((turn, i) => (
                      <motion.div
                        key={`${active.id}-${i}`}
                        initial={{ opacity: 0, y: 14, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                        className={
                          turn.role === "user"
                            ? "ml-auto max-w-[86%] rounded-2xl rounded-br-md bg-primary px-3.5 py-2.5 text-[0.8rem] leading-relaxed text-primary-foreground"
                            : "max-w-[92%] rounded-2xl rounded-bl-md bg-muted px-3.5 py-2.5 text-[0.8rem] leading-relaxed text-foreground"
                        }
                      >
                        {turn.text}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}