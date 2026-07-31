import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Reveal, SectionHeading } from "@/components/landing/Reveal";

const faqs = [
  {
    q: "How does the AI work?",
    a: "Aria combines a large language model with a private timeline of the signals you choose to share—cycle, mood, sleep, symptoms. Responses are grounded in current clinical guidance from bodies like ACOG, NICE and the WHO, and you can always ask to see the reasoning behind an answer.",
  },
  {
    q: "Is my data private?",
    a: "Yes. Your conversations are encrypted in transit and at rest, never sold, and never used for advertising. You can export or permanently delete your entire history at any time from settings.",
  },
  {
    q: "Does this replace doctors?",
    a: "No—and it will never pretend to. Aria offers education, structure and emotional support, and it actively tells you when something should be reviewed by a licensed clinician. Many members use it to prepare better questions for appointments.",
  },
  {
    q: "Can my partner join?",
    a: "Yes. Shared spaces let you invite a partner or support person into specific areas—pregnancy, postpartum or childcare—while keeping your personal journal and mental-health conversations private by default.",
  },
  {
    q: "How much does it cost?",
    a: "There will be a free tier with daily check-ins and cycle intelligence, and a premium plan around $12/month for pregnancy, postpartum and childcare programs. Everyone on the waitlist gets three months of premium at launch.",
  },
];

export function Faq() {
  return (
    <section id="faq" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-3xl px-4 sm:px-6">
        <SectionHeading
          eyebrow="FAQ"
          title="Questions worth asking"
          description="Straight answers about how Aria works, what it costs, and where its limits are."
        />
        <Reveal delay={0.1}>
          <Accordion type="single" collapsible className="mt-12 space-y-3">
            {faqs.map((faq) => (
              <AccordionItem
                key={faq.q}
                value={faq.q}
                className="card-soft rounded-2xl border px-5 hover:translate-y-0"
              >
                <AccordionTrigger className="text-left text-base font-semibold text-foreground hover:no-underline">
                  {faq.q}
                </AccordionTrigger>
                <AccordionContent className="text-sm leading-relaxed text-muted-foreground">
                  {faq.a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </Reveal>
      </div>
    </section>
  );
}