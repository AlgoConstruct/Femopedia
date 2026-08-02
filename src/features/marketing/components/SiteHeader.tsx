import { useState } from "react";
import {
  ArrowRight,
  Baby,
  HeartHandshake,
  Menu,
  MessageCircle,
  Stethoscope,
  X,
} from "lucide-react";
import { ThemeToggle } from "@/components/landing/ThemeToggle";
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";

export function SiteHeader() {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <header className="site-header">
      <nav className="shell nav-wrap" aria-label="Main navigation">
        <a href="#top" className="brand" aria-label="Femopedia home">
          <img src="/brand/logo-primary.svg" alt="Femopedia" width="620" height="150" />
        </a>
        <NavigationMenu className="desktop-nav" viewport={false}>
          <NavigationMenuList>
            <NavigationMenuItem>
              <NavigationMenuLink href="#why" className={navigationMenuTriggerStyle()}>
                Why Femopedia
              </NavigationMenuLink>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <NavigationMenuTrigger>Ecosystem</NavigationMenuTrigger>
              <NavigationMenuContent>
                <div className="nav-panel ecosystem-panel">
                  <a href="#ecosystem" className="nav-feature">
                    <img src="/brand/mark.svg" alt="" width="150" height="150" />
                    <span>
                      <strong>One connected ecosystem</strong>
                      <small>Explore every part of Femopedia</small>
                    </span>
                    <ArrowRight />
                  </a>
                  <div className="nav-grid">
                    <NavigationMenuLink href="#ecosystem">
                      <MessageCircle />
                      <span>
                        <strong>Femopedia AI</strong>
                        <small>Compassionate guidance</small>
                      </span>
                    </NavigationMenuLink>
                    <NavigationMenuLink href="#ecosystem">
                      <Stethoscope />
                      <span>
                        <strong>Care</strong>
                        <small>Prepare and navigate care</small>
                      </span>
                    </NavigationMenuLink>
                    <NavigationMenuLink href="#stages">
                      <HeartHandshake />
                      <span>
                        <strong>Pregnancy</strong>
                        <small>Every-trimester support</small>
                      </span>
                    </NavigationMenuLink>
                    <NavigationMenuLink href="#stages">
                      <Baby />
                      <span>
                        <strong>Baby</strong>
                        <small>Postpartum and parenting</small>
                      </span>
                    </NavigationMenuLink>
                  </div>
                </div>
              </NavigationMenuContent>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <NavigationMenuTrigger>Life stages</NavigationMenuTrigger>
              <NavigationMenuContent>
                <div className="nav-panel stages-panel">
                  <p>Support for where you are now</p>
                  <div>
                    {[
                      "Cycle health",
                      "Everyday wellbeing",
                      "Fertility",
                      "Pregnancy",
                      "Postpartum",
                      "Midlife & beyond",
                    ].map((item) => (
                      <NavigationMenuLink href="#stages" key={item}>
                        <span>{item}</span>
                        <ArrowRight />
                      </NavigationMenuLink>
                    ))}
                  </div>
                </div>
              </NavigationMenuContent>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <NavigationMenuLink href="#safety" className={navigationMenuTriggerStyle()}>
                Our approach
              </NavigationMenuLink>
            </NavigationMenuItem>
          </NavigationMenuList>
        </NavigationMenu>
        <ThemeToggle />
        <a href="#early-access" className="nav-cta">
          Join early access <ArrowRight />
        </a>
        <button
          className="menu-button"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-expanded={menuOpen}
          aria-controls="mobile-navigation"
          aria-label="Toggle menu"
        >
          {menuOpen ? <X /> : <Menu />}
        </button>
      </nav>
      {menuOpen && (
        <div id="mobile-navigation" className="mobile-nav">
          <a href="#why" onClick={() => setMenuOpen(false)}>
            Why Femopedia
          </a>
          <a href="#ecosystem" onClick={() => setMenuOpen(false)}>
            Ecosystem
          </a>
          <a href="#stages" onClick={() => setMenuOpen(false)}>
            Life stages
          </a>
          <a href="#safety" onClick={() => setMenuOpen(false)}>
            Our approach
          </a>
          <a href="#early-access" onClick={() => setMenuOpen(false)}>
            Join early access
          </a>
        </div>
      )}
    </header>
  );
}
