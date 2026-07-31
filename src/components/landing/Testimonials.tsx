import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Quote } from "lucide-react";
import { useEffect, useState } from "react";

import { SectionHeading } from "@/components/landing/Reveal";
import { Button } from "@/components/ui/button";

const testimonials = [
  {
    quote:
      "I've used four cycle apps. Aria is the first one that explained why my symptoms changed instead of just logging them.",
    name: "Maya R.",
    role: "Product designer, 29",
  },
  {
    quote:
      "During postpartum I was awake at 3am with questions I felt embarrassed to ask anyone. It answered kindly, every single time.",
    name: "Anika S.",
    role: "New mother, 34",
  },
  {
    quote:
      "It told me a symptom warranted a same-week appointment. My GP confirmed it. That honesty is why I trust it.",
    name: "Elena V.",
    role: "Teacher, 41",
  },
  {
    quote:
      "Perimenopause finally makes sense. I feel informed instead of dismissed, and my consultations are far more productive.",
    name: "Priya K.",
    role: "Operations lead, 47",
  },
];

export function Testimonials() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => setIndex((i) => (i + 1) % testimonials.length), 6500);
    return () => window.clearInterval(id);
  }, []);

  const current = testimonials[index]!;

  return (
    <section id="testimonials" className="relative overflow-hidden py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <SectionHeading
          eyebrow="Testimonials"
          title="Women who tested Aria first"
          description="Names shortened at their request. Quotes from our 2026 closed beta."
        />

        <div className="relative mx-auto mt-14 max-w-3xl">
          <AnimatePresence mode="wait">
            <motion.figure
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              className="glass-panel rounded-3xl p-8 sm:p-10"
            >
              <Quote className="size-6 text-primary" />
              <blockquote className="mt-5 font-display text-xl leading-relaxed text-foreground sm:text-2xl">
                “{current.quote}”
              </blockquote>
              <figcaption className="mt-6 text-sm text-muted-foreground">
                <span className="font-semibold text-foreground">{current.name}</span> · {current.role}
              </figcaption>
            </motion.figure>
          </AnimatePresence>

          <div className="mt-6 flex items-center justify-center gap-3">
            <Button
              variant="outline"
              size="icon"
              aria-label="Previous testimonial"
              onClick={() => setIndex((i) => (i - 1 + testimonials.length) % testimonials.length)}
            >
              <ChevronLeft />
            </Button>
            <div className="flex items-center gap-2">
              {testimonials.map((t, i) => (
                <button
                  key={t.name}
                  type="button"
                  aria-label={`Show testimonial from ${t.name}`}
                  aria-current={i === index}
                  onClick={() => setIndex(i)}
                  className={`h-1.5 rounded-full transition-all ${
                    i === index ? "w-8 bg-primary" : "w-3 bg-border"
                  }`}
                />
              ))}
            </div>
            <Button
              variant="outline"
              size="icon"
              aria-label="Next testimonial"
              onClick={() => setIndex((i) => (i + 1) % testimonials.length)}
            >
              <ChevronRight />
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}