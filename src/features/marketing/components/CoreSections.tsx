import {
  ArrowRight,
  Baby,
  BookOpen,
  Check,
  HeartHandshake,
  MessageCircle,
  NotebookPen,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  Users,
} from "lucide-react";
import PhoneMockupBasic from "@/components/ui/phone-mockups-1";
import { CommunityVoicePreview } from "@/features/marketing/components/CommunityVoicePreview";
import { ecosystem, lifeStages } from "@/features/marketing/data/content";

const icons = {
  ai: MessageCircle,
  care: Stethoscope,
  pregnancy: HeartHandshake,
  baby: Baby,
  journal: NotebookPen,
  community: Users,
};

export function HeroSection() {
  return (
    <section className="hero shell" aria-labelledby="hero-title">
      <div className="hero-copy">
        <div className="eyebrow">
          <Sparkles /> Living intelligence for women's health
        </div>
        <h1 id="hero-title">
          Your health changes.
          <br />
          <em>Your support should too.</em>
        </h1>
        <p>
          Femopedia brings trusted women’s health education, thoughtful AI guidance, and lifelong
          support into one calm, connected place.
        </p>
        <div className="hero-actions">
          <a href="#early-access" className="primary-button">
            Join early access <ArrowRight />
          </a>
          <a href="#why" className="text-link">
            Discover Femopedia <span aria-hidden="true">↓</span>
          </a>
        </div>
        <div className="trust-line">
          <ShieldCheck />
          <span>Evidence-informed</span>
          <i />
          <span>Private by design</span>
          <i />
          <span>Never a diagnosis</span>
        </div>
      </div>
      <div className="hero-visual">
        <div className="photo-frame hero-photo">
          <img
            src="/images/hero-mother-baby.webp"
            alt="A mother holding her baby in warm natural light"
            width="1400"
            height="1000"
            fetchPriority="high"
            decoding="async"
          />
        </div>
        <div className="companion-card">
          <div className="companion-top">
            <span>
              <img src="/brand/mark.svg" alt="" width="150" height="150" />
              Femopedia AI
            </span>
            <span className="online">Available</span>
          </div>
          <p>
            “Help me understand what may be happening, what matters next, and when I should seek
            care.”
          </p>
          <div className="answer">
            <Sparkles /> I’ll help you work through it clearly, one step at a time.
          </div>
        </div>
        <div className="privacy-pill">
          <ShieldCheck /> Your questions stay yours
        </div>
      </div>
    </section>
  );
}

export function PrinciplesSection() {
  return (
    <section className="belief-strip" id="why" aria-labelledby="why-title">
      <div className="shell belief-grid">
        <p className="section-kicker">A different kind of health platform</p>
        <h2 id="why-title">
          Not another tracker.
          <br />A place to <em>understand.</em>
        </h2>
        <p className="belief-copy">
          Women’s health is not a collection of isolated symptoms or milestones. Femopedia connects
          the context across changing bodies, lives, relationships, and roles—so information feels
          useful, not overwhelming.
        </p>
      </div>
      <div className="principles shell">
        <article>
          <span>01</span>
          <BookOpen />
          <h3>Clarity over complexity</h3>
          <p>
            Plain-language guidance that helps you understand the evidence without unnecessary
            alarm.
          </p>
        </article>
        <article>
          <span>02</span>
          <HeartHandshake />
          <h3>Dignity before data</h3>
          <p>You are a whole person—not a set of metrics, symptoms, or reproductive choices.</p>
        </article>
        <article>
          <span>03</span>
          <ShieldCheck />
          <h3>Support, not substitution</h3>
          <p>
            Clear medical boundaries and thoughtful prompts to seek professional care when
            appropriate.
          </p>
        </article>
      </div>
    </section>
  );
}

export function EcosystemSection() {
  return (
    <section className="ecosystem shell" id="ecosystem" aria-labelledby="ecosystem-title">
      <div className="section-heading">
        <div>
          <p className="section-kicker">One connected ecosystem</p>
          <h2 id="ecosystem-title">
            Support that grows
            <br />
            alongside you.
          </h2>
        </div>
        <p>
          Explore what you need today, with the reassurance that your context can travel with you
          tomorrow.
        </p>
      </div>
      <div className="ecosystem-grid">
        {ecosystem.map((item, index) => {
          const Icon = icons[item.id];
          return (
            <article
              id={`ecosystem-${item.id}`}
              className={index === 0 ? "featured" : ""}
              key={item.id}
            >
              <div className="card-icon">
                <Icon />
              </div>
              <div>
                <h3>{item.name}</h3>
                <p>{item.text}</p>
              </div>
              {item.id === "community" ? <CommunityVoicePreview /> : null}
              <ArrowRight className="card-arrow" aria-hidden="true" />
            </article>
          );
        })}
      </div>
    </section>
  );
}

export function LifeStagesSection() {
  return (
    <section className="stage-section" id="stages" aria-labelledby="stages-title">
      <div className="shell stage-grid">
        <div className="stage-photo photo-frame">
          <img
            src="/images/life-stage-pregnancy.webp"
            alt="Pregnant woman standing peacefully in natural light"
            width="1400"
            height="1800"
            loading="lazy"
            decoding="async"
          />
        </div>
        <div className="stage-content">
          <p className="section-kicker">Every stage belongs here</p>
          <h2 id="stages-title">
            A continuous story,
            <br />
            not disconnected chapters.
          </h2>
          <p>
            From first questions about your body to pregnancy, parenting, midlife, and everything
            that does not fit neatly into a label.
          </p>
          <div className="stage-list">
            {lifeStages.map((stage, index) => (
              <div key={stage}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                {stage}
                <Check />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export function ProductPreviewSection() {
  return (
    <section className="product-preview" id="companion" aria-labelledby="companion-title">
      <div className="shell product-preview-grid">
        <div className="product-preview-copy">
          <p className="section-kicker">A companion in your pocket</p>
          <h2 id="companion-title">
            Thoughtful support,
            <br />
            <em>beautifully simple.</em>
          </h2>
          <p>
            Femopedia brings complex health context into a calm, personal experience—ready when
            questions appear and quiet when you do not need it.
          </p>
          <div className="preview-points">
            <span>
              <Check /> Context that carries across life stages
            </span>
            <span>
              <Check /> Calm explanations in plain language
            </span>
            <span>
              <Check /> Private reflections under your control
            </span>
          </div>
          <a href="#early-access" className="primary-button">
            See what’s coming <ArrowRight />
          </a>
        </div>
        <PhoneMockupBasic />
      </div>
    </section>
  );
}

export function SafetySection() {
  return (
    <section className="safety shell" id="safety" aria-labelledby="safety-title">
      <div className="safety-card">
        <div className="safety-copy">
          <p className="section-kicker light">Carefully designed boundaries</p>
          <h2 id="safety-title">
            Warm support.
            <br />
            Clear limits.
          </h2>
          <p>
            Good health guidance should help you feel more informed—not falsely reassured. Femopedia
            communicates uncertainty honestly and knows when to step aside for professional care.
          </p>
          <div className="safety-points">
            <span>
              <Check /> Explains the “why,” not just the “what”
            </span>
            <span>
              <Check /> Distinguishes education from medical advice
            </span>
            <span>
              <Check /> Flags urgent situations clearly and calmly
            </span>
          </div>
        </div>
        <aside className="care-note" aria-label="Example care guidance">
          <div className="care-note-head">
            <ShieldCheck /> Care guidance
          </div>
          <p>
            Some symptoms can have many causes. I can help you prepare questions and understand
            common possibilities, but a clinician should assess persistent or severe changes.
          </p>
          <div className="care-actions">
            <span>Learn what to monitor</span>
            <span>Prepare for an appointment</span>
          </div>
        </aside>
      </div>
    </section>
  );
}
