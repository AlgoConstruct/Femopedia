import { motion } from "framer-motion";
import {
  Activity,
  Brain,
  Droplets,
  Heart,
  Moon,
  Play,
  ShieldCheck,
  Sparkle,
  Waves,
} from "lucide-react";

import { Blobs } from "@/components/landing/Blobs";
import { Button } from "@/components/ui/button";

const floatingCards = [
  { icon: Heart, label: "Mood", value: "Balanced", tone: "text-primary", pos: "-left-14 -top-8 lg:-left-24" },
  { icon: Moon, label: "Sleep", value: "7h 20m", tone: "text-accent", pos: "-right-10 -top-10 lg:-right-16" },
  { icon: Waves, label: "Cycle", value: "Day 18 · Luteal", tone: "text-primary", pos: "-left-16 top-1/2 lg:-left-28" },
  { icon: Droplets, label: "Hydration", value: "1.8 L", tone: "text-secondary-foreground", pos: "-right-12 top-2/3 lg:-right-20" },
  { icon: Activity, label: "Energy", value: "Steady", tone: "text-primary", pos: "-left-10 -bottom-10 lg:-left-16" },
  { icon: Brain, label: "Stress", value: "Low", tone: "text-accent", pos: "-right-6 -bottom-12 lg:-right-14" },
];

export function Hero() {
  return (
    <section id="home" className="relative overflow-hidden pb-20 pt-32 sm:pt-40">
      <Blobs />
      <div className="relative mx-auto grid max-w-7xl items-center gap-16 px-4 sm:px-6 lg:grid-cols-[1.05fr_1fr]">
        <div>
          <motion.span
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-1.5 text-xs font-semibold text-muted-foreground"
          >
            <Sparkle className="size-3.5 text-primary" />
            Evidence-informed AI · Private by design
          </motion.span>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
            className="mt-6 text-4xl font-semibold leading-[1.06] text-foreground sm:text-5xl lg:text-6xl"
          >
            Your AI Companion Through Every Stage of{" "}
            <span className="text-gradient">Womanhood.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.16 }}
            className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground"
          >
            Supporting your physical, emotional, and mental wellbeing with personalized guidance
            that grows with you—from your first period to motherhood and beyond.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.24 }}
            className="mt-9 flex flex-wrap items-center gap-3"
          >
            <Button variant="hero" size="xl" asChild>
              <a href="#waitlist">Join Waitlist</a>
            </Button>
            <Button variant="glass" size="xl" asChild>
              <a href="#companion">
                <Play className="size-4" /> Watch Demo
              </a>
            </Button>
          </motion.div>

          <motion.dl
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.36 }}
            className="mt-12 grid max-w-lg grid-cols-3 gap-6"
          >
            {[
              { k: "24 000+", v: "women on the waitlist" },
              { k: "12", v: "life stages supported" },
              { k: "End-to-end", v: "encrypted conversations" },
            ].map((stat) => (
              <div key={stat.k}>
                <dt className="font-display text-xl font-semibold text-foreground">{stat.k}</dt>
                <dd className="mt-1 text-sm text-muted-foreground">{stat.v}</dd>
              </div>
            ))}
          </motion.dl>
        </div>

        <div className="relative mx-auto w-full max-w-md">
          {floatingCards.map((card, i) => (
            <motion.div
              key={card.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1, y: [0, -9, 0] }}
              transition={{
                opacity: { duration: 0.6, delay: 0.3 + i * 0.08 },
                scale: { duration: 0.6, delay: 0.3 + i * 0.08 },
                y: { duration: 6 + i, repeat: Infinity, ease: "easeInOut", delay: i * 0.4 },
              }}
              className={`glass-panel absolute z-0 hidden rounded-2xl px-3.5 py-2.5 sm:block ${card.pos}`}
            >
              <div className="flex items-center gap-2.5">
                <card.icon className={`size-4 ${card.tone}`} />
                <div>
                  <p className="text-[0.65rem] font-semibold uppercase tracking-wider text-muted-foreground">
                    {card.label}
                  </p>
                  <p className="text-sm font-medium text-foreground">{card.value}</p>
                </div>
              </div>
            </motion.div>
          ))}

          <motion.div
            initial={{ opacity: 0, y: 30, rotateX: 8 }}
            animate={{ opacity: 1, y: 0, rotateX: 0 }}
            transition={{ duration: 0.9, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 rounded-[2rem] border border-border bg-surface p-5 shadow-[var(--shadow-lift)]"
          >
            <div className="flex items-center gap-3 border-b border-border pb-4">
              <span className="grid size-9 place-items-center rounded-full bg-primary/12 text-primary">
                <Sparkle className="size-4" />
              </span>
              <div>
                <p className="text-sm font-semibold text-foreground">Aria</p>
                <p className="text-xs text-muted-foreground">
                  <span className="mr-1.5 inline-block size-1.5 rounded-full bg-success align-middle" />
                  Listening, always private
                </p>
              </div>
              <ShieldCheck className="ml-auto size-4 text-muted-foreground" />
            </div>

            <div className="space-y-4 pt-5">
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.7 }}
                className="ml-auto max-w-[85%] rounded-2xl rounded-br-md bg-primary px-4 py-3 text-sm leading-relaxed text-primary-foreground"
              >
                I've been feeling unusually emotional today.
              </motion.div>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 1.2 }}
                className="max-w-[92%] rounded-2xl rounded-bl-md bg-muted px-4 py-3 text-sm leading-relaxed text-foreground"
              >
                Based on your cycle, hormonal changes may be contributing. Let's talk through how
                you're feeling, and if you'd like, I can suggest ways to support yourself today.
              </motion.div>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.7 }}
                className="flex flex-wrap gap-2"
              >
                {["Let's talk", "Suggest a reset", "Track my mood"].map((chip) => (
                  <span
                    key={chip}
                    className="rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground"
                  >
                    {chip}
                  </span>
                ))}
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}