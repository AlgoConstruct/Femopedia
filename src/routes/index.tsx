import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  ArrowRight,
  Baby,
  BookOpen,
  Check,
  ChevronDown,
  HeartHandshake,
  Menu,
  MessageCircle,
  NotebookPen,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  Users,
  X,
} from "lucide-react";
import { NavigationMenu, NavigationMenuContent, NavigationMenuItem, NavigationMenuLink, NavigationMenuList, NavigationMenuTrigger, navigationMenuTriggerStyle } from "@/components/ui/navigation-menu";
import PhoneMockupBasic from "@/components/ui/phone-mockups-1";
import { StaggerTestimonials } from "@/components/ui/stagger-testimonials";
import { FloatingChatWidget } from "@/components/ui/floating-chat-widget-shadcnui";

const title = "Femopedia — Women's Health, Understood";
const description =
  "A trusted, AI-powered companion for women's health education, life-stage guidance, and care navigation.";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title },
      { name: "description", content: description },
      { property: "og:title", content: title },
      { property: "og:description", content: description },
      { property: "og:image", content: "/brand/social-card.png" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: FemopediaLanding,
});

const ecosystem = [
  { icon: MessageCircle, name: "Femopedia AI", text: "Ask sensitive questions and get calm, contextual guidance—without judgment." },
  { icon: Stethoscope, name: "Femopedia Care", text: "Understand when to seek care and prepare for more productive appointments." },
  { icon: HeartHandshake, name: "Pregnancy", text: "Evidence-informed support through pregnancy, birth preparation, and recovery." },
  { icon: Baby, name: "Baby", text: "Practical postpartum and early parenting guidance for the whole family." },
  { icon: NotebookPen, name: "Journal", text: "A private health timeline that helps you notice patterns in your own story." },
  { icon: Users, name: "Community", text: "Thoughtful conversations in a moderated, stigma-free space." },
];

const stages = ["First changes", "Cycle health", "Everyday wellbeing", "Fertility", "Pregnancy", "Postpartum", "Parenting", "Midlife & beyond"];
const questions = [
  ["Is Femopedia a medical service?", "No. Femopedia provides educational guidance and care navigation. It does not diagnose, prescribe, or replace a qualified healthcare professional."],
  ["How does the AI handle uncertainty?", "It separates established evidence from general guidance, explains when information is uncertain, and clearly highlights when professional or urgent care may be needed."],
  ["Is my health information private?", "Privacy is a product principle, not an afterthought. Femopedia is designed to collect only what is useful, explain why it is needed, and keep personal reflections under your control."],
];

function FemopediaLanding() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [openFaq, setOpenFaq] = useState(0);
  const [email, setEmail] = useState("");
  const [joined, setJoined] = useState(false);

  return (
    <div className="min-h-screen overflow-x-hidden bg-background text-foreground">
      <header className="site-header">
        <nav className="shell nav-wrap" aria-label="Main navigation">
          <a href="#top" className="brand" aria-label="Femopedia home">
            <img src="/brand/logo-primary.svg" alt="Femopedia" />
          </a>
          <NavigationMenu className="desktop-nav" viewport={false}>
            <NavigationMenuList>
              <NavigationMenuItem><NavigationMenuLink href="#why" className={navigationMenuTriggerStyle()}>Why Femopedia</NavigationMenuLink></NavigationMenuItem>
              <NavigationMenuItem>
                <NavigationMenuTrigger>Ecosystem</NavigationMenuTrigger>
                <NavigationMenuContent><div className="nav-panel ecosystem-panel">
                  <a href="#ecosystem" className="nav-feature"><img src="/brand/mark.svg" alt="" /><span><strong>One connected ecosystem</strong><small>Explore every part of Femopedia</small></span><ArrowRight /></a>
                  <div className="nav-grid">
                    <NavigationMenuLink href="#ecosystem"><MessageCircle /><span><strong>Femopedia AI</strong><small>Compassionate guidance</small></span></NavigationMenuLink>
                    <NavigationMenuLink href="#ecosystem"><Stethoscope /><span><strong>Care</strong><small>Prepare and navigate care</small></span></NavigationMenuLink>
                    <NavigationMenuLink href="#stages"><HeartHandshake /><span><strong>Pregnancy</strong><small>Every-trimester support</small></span></NavigationMenuLink>
                    <NavigationMenuLink href="#stages"><Baby /><span><strong>Baby</strong><small>Postpartum and parenting</small></span></NavigationMenuLink>
                  </div>
                </div></NavigationMenuContent>
              </NavigationMenuItem>
              <NavigationMenuItem>
                <NavigationMenuTrigger>Life stages</NavigationMenuTrigger>
                <NavigationMenuContent><div className="nav-panel stages-panel"><p>Support for where you are now</p><div>{["Cycle health", "Everyday wellbeing", "Fertility", "Pregnancy", "Postpartum", "Midlife & beyond"].map((item) => <NavigationMenuLink href="#stages" key={item}><span>{item}</span><ArrowRight /></NavigationMenuLink>)}</div></div></NavigationMenuContent>
              </NavigationMenuItem>
              <NavigationMenuItem><NavigationMenuLink href="#safety" className={navigationMenuTriggerStyle()}>Our approach</NavigationMenuLink></NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>
          <a href="#early-access" className="nav-cta">Join early access <ArrowRight /></a>
          <button className="menu-button" onClick={() => setMenuOpen(!menuOpen)} aria-expanded={menuOpen} aria-label="Toggle menu">
            {menuOpen ? <X /> : <Menu />}
          </button>
        </nav>
        {menuOpen && <div className="mobile-nav"><a href="#why" onClick={() => setMenuOpen(false)}>Why Femopedia</a><a href="#ecosystem" onClick={() => setMenuOpen(false)}>Ecosystem</a><a href="#stages" onClick={() => setMenuOpen(false)}>Life stages</a><a href="#early-access" onClick={() => setMenuOpen(false)}>Join early access</a></div>}
      </header>

      <main id="top">
        <section className="hero shell">
          <div className="hero-copy">
            <div className="eyebrow"><Sparkles /> Living intelligence for women's health</div>
            <h1>Your health changes.<br /><em>Your support should too.</em></h1>
            <p>Femopedia brings trusted health education, thoughtful AI guidance, and lifelong support into one calm, connected place.</p>
            <div className="hero-actions">
              <a href="#early-access" className="primary-button">Join early access <ArrowRight /></a>
              <a href="#why" className="text-link">Discover Femopedia <span>↓</span></a>
            </div>
            <div className="trust-line"><ShieldCheck /><span>Evidence-informed</span><i /> <span>Private by design</span><i /> <span>Never a diagnosis</span></div>
          </div>
          <div className="hero-visual">
            <div className="photo-frame hero-photo"><img src="https://images.unsplash.com/photo-1542385151-efd9000785a0?auto=format&fit=crop&w=1400&q=88" alt="A mother holding her baby in warm natural light" /></div>
            <div className="companion-card"><div className="companion-top"><span><img src="/brand/mark.svg" alt="" />Femopedia AI</span><span className="online">Available</span></div><p>“Help me understand what may be happening, what matters next, and when I should seek care.”</p><div className="answer"><Sparkles /> I’ll help you work through it clearly, one step at a time.</div></div>
            <div className="privacy-pill"><ShieldCheck /> Your questions stay yours</div>
          </div>
        </section>

        <section className="belief-strip" id="why">
          <div className="shell belief-grid">
            <p className="section-kicker">A different kind of health platform</p>
            <h2>Not another tracker.<br />A place to <em>understand.</em></h2>
            <p className="belief-copy">Women’s health is not a collection of isolated symptoms or milestones. Femopedia connects the context across changing bodies, lives, relationships, and roles—so information feels useful, not overwhelming.</p>
          </div>
          <div className="principles shell">
            <div><span>01</span><BookOpen /><h3>Clarity over complexity</h3><p>Plain-language guidance that helps you understand the evidence without unnecessary alarm.</p></div>
            <div><span>02</span><HeartHandshake /><h3>Dignity before data</h3><p>You are a whole person—not a set of metrics, symptoms, or reproductive choices.</p></div>
            <div><span>03</span><ShieldCheck /><h3>Support, not substitution</h3><p>Clear medical boundaries and thoughtful prompts to seek professional care when appropriate.</p></div>
          </div>
        </section>

        <section className="ecosystem shell" id="ecosystem">
          <div className="section-heading">
            <div><p className="section-kicker">One connected ecosystem</p><h2>Support that grows<br />alongside you.</h2></div>
            <p>Explore what you need today, with the reassurance that your context can travel with you tomorrow.</p>
          </div>
          <div className="ecosystem-grid">
            {ecosystem.map((item, index) => <article className={index === 0 ? "featured" : ""} key={item.name}><div className="card-icon"><item.icon /></div><div><h3>{item.name}</h3><p>{item.text}</p></div><ArrowRight className="card-arrow" /></article>)}
          </div>
        </section>

        <section className="stage-section" id="stages">
          <div className="shell stage-grid">
            <div className="stage-photo photo-frame"><img src="https://images.unsplash.com/photo-1678739201887-34001155c5e0?auto=format&fit=crop&w=1400&q=88" alt="Pregnant woman standing peacefully in natural light" /></div>
            <div className="stage-content">
              <p className="section-kicker">Every stage belongs here</p>
              <h2>A continuous story,<br />not disconnected chapters.</h2>
              <p>From first questions about your body to pregnancy, parenting, midlife, and everything that does not fit neatly into a label.</p>
              <div className="stage-list">{stages.map((stage, i) => <div key={stage}><span>{String(i + 1).padStart(2, "0")}</span>{stage}<Check /></div>)}</div>
            </div>
          </div>
        </section>

        <section className="product-preview" id="companion">
          <div className="shell product-preview-grid">
            <div className="product-preview-copy"><p className="section-kicker">A companion in your pocket</p><h2>Thoughtful support,<br /><em>beautifully simple.</em></h2><p>Femopedia brings complex health context into a calm, personal experience—ready when questions appear and quiet when you do not need it.</p><div className="preview-points"><span><Check /> Context that carries across life stages</span><span><Check /> Calm explanations in plain language</span><span><Check /> Private reflections under your control</span></div><a href="#early-access" className="primary-button">See what’s coming <ArrowRight /></a></div>
            <PhoneMockupBasic />
          </div>
        </section>

        <section className="safety shell" id="safety">
          <div className="safety-card">
            <div className="safety-copy"><p className="section-kicker light">Carefully designed boundaries</p><h2>Warm support.<br />Clear limits.</h2><p>Good health guidance should help you feel more informed—not falsely reassured. Femopedia communicates uncertainty honestly and knows when to step aside for professional care.</p><div className="safety-points"><span><Check /> Explains the “why,” not just the “what”</span><span><Check /> Distinguishes education from medical advice</span><span><Check /> Flags urgent situations clearly and calmly</span></div></div>
            <div className="care-note"><div className="care-note-head"><ShieldCheck /> Care guidance</div><p>Some symptoms can have many causes. I can help you prepare questions and understand common possibilities, but a clinician should assess persistent or severe changes.</p><div className="care-actions"><span>Learn what to monitor</span><span>Prepare for an appointment</span></div></div>
          </div>
        </section>

        <section className="quote-section shell">
          <img src="/brand/mark.svg" alt="" className="quote-mark" />
          <blockquote>“Your body is not a problem to solve. Your questions are valid, and understanding should never feel out of reach.”</blockquote>
          <p>— The Femopedia promise</p>
        </section>

        <section className="perspectives-section" id="perspectives">
          <div className="shell perspectives-heading"><p className="section-kicker">Designed around real needs</p><h2>Health guidance should<br /><em>feel more human.</em></h2><p>Illustrative perspectives shaped by recurring needs in women’s health conversations—not medical or product claims.</p></div>
          <StaggerTestimonials />
        </section>

        <section className="faq shell">
          <div><p className="section-kicker">Questions, answered clearly</p><h2>Trust begins with transparency.</h2></div>
          <div className="faq-list">{questions.map(([q, a], i) => <button key={q} onClick={() => setOpenFaq(openFaq === i ? -1 : i)} aria-expanded={openFaq === i}><span>{q}</span><ChevronDown className={openFaq === i ? "rotated" : ""} />{openFaq === i && <p>{a}</p>}</button>)}</div>
        </section>

        <section className="join-section" id="early-access">
          <div className="shell join-grid">
            <div><p className="section-kicker light">Be here from the beginning</p><h2>A healthier relationship<br />with health starts here.</h2><p>Join the early community helping shape a more thoughtful future for women’s health.</p></div>
            <form onSubmit={(e) => {e.preventDefault(); if (email) setJoined(true);}} className="join-form">
              {joined ? <div className="success-message"><Check /> You’re on the list. Welcome to Femopedia.</div> : <><label htmlFor="email">Email address</label><div><input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" /><button type="submit">Join early access <ArrowRight /></button></div><small>No spam. No data selling. Just meaningful updates.</small></>}
            </form>
          </div>
        </section>
      </main>

      <footer className="footer shell">
        <div><img src="/brand/logo-primary.svg" alt="Femopedia" /><p>Living intelligence for every stage of womanhood.</p></div>
        <div className="footer-links"><a href="#ecosystem">Ecosystem</a><a href="#safety">Safety</a><a href="#early-access">Early access</a><a href="mailto:hello@femopedia.com">Contact</a></div>
        <div className="footer-bottom"><span>© 2026 Femopedia</span><span>Educational support, never a replacement for professional medical care.</span></div>
      </footer>
      <FloatingChatWidget />
    </div>
  );
}
