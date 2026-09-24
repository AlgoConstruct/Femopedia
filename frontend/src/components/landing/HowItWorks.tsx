import { ClipboardList, LineChart, MessagesSquare } from "lucide-react";

import { Reveal, SectionHeading } from "@/components/landing/Reveal";

const steps = [
  {
    icon: ClipboardList,
    title: "Share where you are today",
    body: "A gentle three-minute intake—your stage of life, your goals, what you'd like support with. No forms that feel like paperwork.",
  },
  {
    icon: MessagesSquare,
    title: "Talk the way you'd talk to a friend",
    body: "Aria listens, asks thoughtful follow-ups, and grounds every answer in current clinical guidance—never judgment, never guesswork.",
  },
  {
    icon: LineChart,
    title: "Watch your insights compound",
    body: "Mood, cycle, sleep and symptoms connect over time, so patterns surface early and your care conversations get sharper.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <SectionHeading
          eyebrow="How it works"
          title="Three steps to a companion that truly knows you"
          description="Set up once. Aria carries your context forward for every chapter that follows."
        />
        <ol className="mt-14 grid gap-5 md:grid-cols-3">
          {steps.map((step, i) => (
            <Reveal as="li" key={step.title} delay={i * 0.1}>
              <div className="card-soft relative h-full rounded-3xl p-7">
                <span className="font-display text-sm font-semibold text-primary">
                  0{i + 1}
                </span>
                <span className="mt-5 grid size-12 place-items-center rounded-2xl bg-gradient-to-br from-primary/15 to-accent/15 text-primary">
                  <step.icon className="size-5" />
                </span>
                <h3 className="mt-5 text-lg font-semibold text-foreground">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{step.body}</p>
              </div>
            </Reveal>
          ))}
        </ol>
      </div>
    </section>
  );
}