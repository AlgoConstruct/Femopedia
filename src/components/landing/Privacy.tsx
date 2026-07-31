import { Eye, FileHeart, KeyRound, Lock, Stethoscope } from "lucide-react";

import shieldArt from "@/assets/privacy-shield.png";
import { Reveal, SectionHeading } from "@/components/landing/Reveal";

const cards = [
  {
    icon: Lock,
    title: "Private by Design",
    body: "We collect the minimum needed to help you—never data for advertising.",
  },
  {
    icon: KeyRound,
    title: "Encrypted",
    body: "Conversations are encrypted in transit and at rest with per-account keys.",
  },
  {
    icon: FileHeart,
    title: "You Control Your Data",
    body: "Export or permanently delete everything from settings, any time.",
  },
  {
    icon: Eye,
    title: "Transparent AI",
    body: "Every answer can show its sources and how confident the model is.",
  },
  {
    icon: Stethoscope,
    title: "Medical Disclaimer",
    body: "Aria offers education and support—it does not replace a licensed clinician.",
  },
];

export function Privacy() {
  return (
    <section id="privacy" className="relative py-24 sm:py-32">
      <div className="mx-auto grid max-w-7xl items-center gap-14 px-4 sm:px-6 lg:grid-cols-[0.85fr_1fr]">
        <Reveal>
          <div className="relative mx-auto max-w-sm">
            <div className="blob absolute inset-8 bg-primary/25" />
            <img
              src={shieldArt}
              alt="Illustration of a layered translucent shield representing encrypted health data"
              width={1024}
              height={1024}
              loading="lazy"
              className="floaty relative w-full"
            />
          </div>
        </Reveal>

        <div>
          <SectionHeading
            align="left"
            eyebrow="Privacy"
            title="Trust is the product"
            description="Health data is the most personal data there is. We built Aria so you never have to trade privacy for support."
          />
          <ul className="mt-10 grid gap-4 sm:grid-cols-2">
            {cards.map((card, i) => (
              <Reveal as="li" key={card.title} delay={i * 0.06}>
                <div className="card-soft h-full rounded-2xl p-5">
                  <span className="grid size-10 place-items-center rounded-xl bg-secondary/25 text-secondary-foreground">
                    <card.icon className="size-4" />
                  </span>
                  <h3 className="mt-4 text-sm font-semibold text-foreground">{card.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{card.body}</p>
                </div>
              </Reveal>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}