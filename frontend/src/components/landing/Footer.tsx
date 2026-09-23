import { Github, Instagram, Linkedin, Twitter } from "lucide-react";

import logoMark from "@/assets/logo-mark.png";

const columns = [
  {
    title: "Product",
    links: ["Features", "How It Works", "Life Stages", "AI Companion", "Pricing"],
  },
  { title: "Resources", links: ["Health Library", "Research Notes", "Clinical Advisors", "Blog"] },
  { title: "Company", links: ["About", "Careers", "Press", "Contact"] },
];

const socials = [
  { icon: Twitter, label: "Aria on X" },
  { icon: Instagram, label: "Aria on Instagram" },
  { icon: Linkedin, label: "Aria on LinkedIn" },
  { icon: Github, label: "Aria on GitHub" },
];

export function Footer() {
  return (
    <footer className="border-t border-border bg-surface/70">
      <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6">
        <div className="grid gap-10 md:grid-cols-[1.4fr_repeat(3,1fr)]">
          <div>
            <div className="flex items-center gap-2.5">
              <img src={logoMark} alt="" width={32} height={32} loading="lazy" className="size-8" />
              <span className="font-display text-lg font-semibold text-foreground">Aria</span>
            </div>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
              An AI companion for women's health—calm, evidence-informed, and private by design.
            </p>
            <ul className="mt-6 flex items-center gap-2">
              {socials.map((social) => (
                <li key={social.label}>
                  <a
                    href="#home"
                    aria-label={social.label}
                    className="grid size-11 place-items-center rounded-full border border-border text-muted-foreground transition-colors hover:border-primary/40 hover:text-primary"
                  >
                    <social.icon className="size-4" />
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {columns.map((column) => (
            <nav key={column.title} aria-label={column.title}>
              <h3 className="text-sm font-semibold text-foreground">{column.title}</h3>
              <ul className="mt-4 space-y-2.5">
                {column.links.map((link) => (
                  <li key={link}>
                    <a
                      href="#home"
                      className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        <div className="mt-12 flex flex-col gap-4 border-t border-border pt-6 sm:flex-row sm:items-center">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} Aria Health. Not a substitute for professional medical care.
          </p>
          <div className="flex gap-5 sm:ml-auto">
            <a href="#privacy" className="text-xs text-muted-foreground hover:text-foreground">
              Privacy
            </a>
            <a href="#faq" className="text-xs text-muted-foreground hover:text-foreground">
              Terms
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}