import { motion } from "framer-motion";
import { Baby, BookHeart, Brain, Target, TrendingUp, Waves } from "lucide-react";

import { Reveal, SectionHeading } from "@/components/landing/Reveal";

const cards = [
  { icon: TrendingUp, title: "Mood Trends", detail: "Seven-day emotional pattern, gently summarized." },
  { icon: Waves, title: "Cycle Insights", detail: "Phase-aware guidance, not just calendar dates." },
  { icon: BookHeart, title: "Daily Journal", detail: "Two lines a day becomes a year of context." },
  { icon: Target, title: "Health Goals", detail: "Small, realistic goals that flex with your week." },
  { icon: Baby, title: "Baby Timeline", detail: "Milestones, feeds and sleep in one calm view." },
  { icon: Brain, title: "Mental Wellness", detail: "Screening prompts and grounding exercises." },
];

export function Personalization() {
  return (
    <section className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <SectionHeading
          eyebrow="Personalization"
          title="One Companion. Every Chapter."
          description="Every signal you share feeds a single, private model of your health—so the advice you get today is shaped by everything before it."
        />
        <ul className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((card, i) => (
            <Reveal as="li" key={card.title} delay={(i % 3) * 0.08}>
              <motion.article
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 7 + i, repeat: Infinity, ease: "easeInOut", delay: i * 0.5 }}
                className="glass-panel h-full rounded-3xl p-6"
              >
                <span className="grid size-11 place-items-center rounded-2xl bg-gradient-to-br from-primary/15 to-secondary/25 text-primary">
                  <card.icon className="size-5" />
                </span>
                <h3 className="mt-5 text-base font-semibold text-foreground">{card.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{card.detail}</p>
              </motion.article>
            </Reveal>
          ))}
        </ul>
        <Reveal delay={0.2}>
          <p className="mt-10 text-center text-sm font-medium text-muted-foreground">
            All connected through AI—one thread, twelve chapters, zero re-explaining.
          </p>
        </Reveal>
      </div>
    </section>
  );
}