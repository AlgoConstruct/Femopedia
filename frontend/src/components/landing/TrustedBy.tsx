import { Building2, FlaskConical, HeartPulse, Users } from "lucide-react";

import { Reveal } from "@/components/landing/Reveal";

const partners = [
  { icon: HeartPulse, name: "Northbridge Health", type: "Healthcare" },
  { icon: FlaskConical, name: "Ceres Research Lab", type: "Researchers" },
  { icon: Users, name: "HerCircle Collective", type: "Women's Communities" },
  { icon: Building2, name: "Lumen Technologies", type: "Technology Partners" },
];

export function TrustedBy() {
  return (
    <section aria-label="Trusted by" className="border-y border-border bg-surface/60 py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <Reveal>
          <p className="text-center text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
            Built with clinicians, researchers and the communities we serve
          </p>
        </Reveal>
        <ul className="mt-8 grid grid-cols-2 gap-6 md:grid-cols-4">
          {partners.map((partner, i) => (
            <Reveal as="li" key={partner.name} delay={i * 0.06}>
              <div className="flex items-center gap-3 opacity-60 grayscale transition-all duration-300 hover:opacity-100 hover:grayscale-0">
                <span className="grid size-10 place-items-center rounded-xl border border-border bg-surface">
                  <partner.icon className="size-5 text-foreground" />
                </span>
                <div>
                  <p className="font-display text-sm font-semibold text-foreground">
                    {partner.name}
                  </p>
                  <p className="text-xs text-muted-foreground">{partner.type}</p>
                </div>
              </div>
            </Reveal>
          ))}
        </ul>
      </div>
    </section>
  );
}