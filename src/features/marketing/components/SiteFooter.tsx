export function SiteFooter() {
  return (
    <footer className="footer shell">
      <div>
        <img src="/brand/logo-primary.svg" alt="Femopedia" width="620" height="150" />
        <p>Living intelligence for every stage of womanhood.</p>
      </div>
      <nav className="footer-links" aria-label="Footer navigation">
        <a href="#ecosystem">Ecosystem</a>
        <a href="#safety">Safety</a>
        <a href="#faq">FAQ</a>
        <a href="#early-access">Early access</a>
        <a href="mailto:hello@femopedia.com">Contact</a>
      </nav>
      <div className="footer-bottom">
        <span>© 2026 Femopedia</span>
        <span>Educational support, never a replacement for professional medical care.</span>
      </div>
    </footer>
  );
}
