import { motion } from "framer-motion";
import { useState } from "react";

import { SectionHeading } from "@/components/landing/Reveal";

const stages = [
  { name: "Teen", note: "First periods explained clearly, without embarrassment." },
  { name: "Menstrual Health", note: "Symptom patterns, pain tracking, and when to seek care." },
  { name: "College", note: "Sleep, stress and study seasons that shape your hormones." },
  { name: "Career", note: "Energy management, burnout signals, and long-term health habits." },
  { name: "Marriage", note: "Shared health planning and honest conversations about the future." },
  { name: "Trying to Conceive", note: "Fertile windows, ovulation signals, and realistic timelines." },
  { name: "Pregnancy", note: "Week-by-week guidance and questions worth asking your clinician." },
  { name: "Motherhood", note: "Identity, rest, and building a support system that holds." },
  { name: "Postpartum", note: "Recovery milestones, feeding support, and mood screening." },
  { name: "Childcare", note: "Sleep, feeding and development, grounded in evidence." },
  { name: "Perimenopause", note: "Understanding shifting cycles and new symptoms early." },
  { name: "Menopause", note: "Bone, heart and brain health for the decades ahead." },
];

export function JourneyTimeline() {
  const [active, setActive] = useState(0);
  const current = stages[active] ?? stages[0]!;

  return (
    <section id="life-stages" className="relative overflow-hidden py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <SectionHeading
          eyebrow="Life stages"
          title="One journey, twelve chapters"
          description="Aria doesn't restart when your life changes. Hover a stage to see how support adapts."
        />

        <div className="relative mt-16 overflow-x-auto pb-6">
          <div className="min-w-[52rem]">
            <motion.div
              initial={{ scaleX: 0 }}
              whileInView={{ scaleX: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
              style={{ originX: 0 }}
              className="h-px w-full rounded-full bg-gradient-to-r from-primary via-accent to-secondary"
            />
            <ul className="mt-0 grid grid-cols-12">
              {stages.map((stage, i) => (
                <li
                  key={stage.name}
                  onMouseEnter={() => setActive(i)}
                  onFocus={() => setActive(i)}
                  className="group relative flex flex-col items-center pt-0"
                >
                  <button
                    type="button"
                    aria-pressed={active === i}
                    onClick={() => setActive(i)}
                    className="-mt-2 grid size-4 place-items-center rounded-full border-2 border-primary bg-background transition-transform duration-300 group-hover:scale-125"
                  >
                    <span
                      className={`size-1.5 rounded-full transition-colors ${
                        active === i ? "bg-primary" : "bg-transparent"
                      }`}
                    />
                  </button>
                  <p
                    className={`mt-4 max-w-[7rem] text-center text-xs font-semibold leading-snug transition-colors ${
                      active === i ? "text-foreground" : "text-muted-foreground"
                    }`}
                  >
                    {stage.name}
                  </p>
                  <motion.span
                    initial={false}
                    animate={{ opacity: active === i ? 1 : 0 }}
                    className="mt-2 block h-1 w-6 rounded-full bg-primary"
                  />
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="card-soft mx-auto mt-8 max-w-2xl rounded-3xl p-6 text-center">
          <p className="font-display text-lg font-semibold text-foreground">{current.name}</p>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{current.note}</p>
        </div>
      </div>
    </section>
  );
}