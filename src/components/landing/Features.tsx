import {
  Baby,
  Brain,
  CalendarHeart,
  HeartHandshake,
  Lock,
  MessageCircleHeart,
  Route,
  Sprout,
} from "lucide-react";

import { Reveal, SectionHeading } from "@/components/landing/Reveal";

const features = [
  {
    icon: MessageCircleHeart,
    title: "AI Health Companion",
    body: "A personalized AI that remembers your journey and provides meaningful support.",
  },
  {
    icon: Brain,
    title: "Mental Wellness",
    body: "Daily emotional check-ins and personalized guidance.",
  },
  {
    icon: CalendarHeart,
    title: "Cycle Intelligence",
    body: "Understand your body beyond simple period tracking.",
  },
  { icon: Sprout, title: "Pregnancy Guide", body: "Week-by-week personalized insights." },
  {
    icon: HeartHandshake,
    title: "Postpartum Support",
    body: "Recovery, breastfeeding, emotional wellbeing.",
  },
  { icon: Baby, title: "Childcare Mentor", body: "Evidence-informed guidance for parents." },
  { icon: Route, title: "Health Timeline", body: "Your complete health journey in one place." },
  { icon: Lock, title: "Privacy First", body: "Your data belongs to you." },
];

export function Features() {
  return (
    <section id="features" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <SectionHeading
          eyebrow="Features"
          title={<>Intelligence that feels like care</>}
          description="Eight capabilities working as one companion—so nothing about your health has to be explained twice."
        />
        <ul className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature, i) => (
            <Reveal as="li" key={feature.title} delay={(i % 4) * 0.07}>
              <article className="card-soft group h-full rounded-3xl p-6">
                <span className="grid size-11 place-items-center rounded-2xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                  <feature.icon className="size-5" />
                </span>
                <h3 className="mt-5 text-base font-semibold text-foreground">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{feature.body}</p>
              </article>
            </Reveal>
          ))}
        </ul>
      </div>
    </section>
  );
}