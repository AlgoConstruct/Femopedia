import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { StaggerTestimonials } from "@/components/ui/stagger-testimonials";
import { faqs } from "@/features/marketing/data/content";

export function PromiseSection() {
  return (
    <section className="quote-section shell" aria-label="The Femopedia promise">
      <img src="/brand/mark.svg" alt="" className="quote-mark" width="150" height="150" />
      <blockquote>
        “Your body is not a problem to solve. Your questions are valid, and understanding should
        never feel out of reach.”
      </blockquote>
      <p>— The Femopedia promise</p>
    </section>
  );
}

export function PerspectivesSection() {
  return (
    <section
      className="perspectives-section"
      id="perspectives"
      aria-labelledby="perspectives-title"
    >
      <div className="shell perspectives-heading">
        <p className="section-kicker">Designed around real needs</p>
        <h2 id="perspectives-title">
          Health guidance should
          <br />
          <em>feel more human.</em>
        </h2>
        <p>
          Illustrative perspectives shaped by recurring needs in women’s health conversations—not
          medical or product claims.
        </p>
      </div>
      <StaggerTestimonials />
    </section>
  );
}

export function FaqSection() {
  const [openFaq, setOpenFaq] = useState(0);
  return (
    <section className="faq shell" id="faq" aria-labelledby="faq-title">
      <div>
        <p className="section-kicker">Questions, answered clearly</p>
        <h2 id="faq-title">Trust begins with transparency.</h2>
      </div>
      <div className="faq-list">
        {faqs.map(({ question, answer }, index) => (
          <div className="faq-item" key={question}>
            <button
              type="button"
              onClick={() => setOpenFaq(openFaq === index ? -1 : index)}
              aria-expanded={openFaq === index}
              aria-controls={`faq-answer-${index}`}
            >
              <span>{question}</span>
              <ChevronDown className={openFaq === index ? "rotated" : ""} aria-hidden="true" />
            </button>
            <p id={`faq-answer-${index}`} hidden={openFaq !== index}>
              {answer}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
