import { useState } from "react";
import {
  ArrowRight,
  Baby,
  HeartHandshake,
  Menu,
  MessageCircle,
  NotebookPen,
  Stethoscope,
  Users,
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
      <div className="shell nav-wrap">
        <a href="/" className="brand" aria-label="Femopedia home">
          <img src="/brand/logo-primary.svg" alt="Femopedia" width="620" height="150" />
        </a>
        <NavigationMenu className="desktop-nav" viewport={false} aria-label="Primary navigation">
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
                    <NavigationMenuLink href="#ecosystem-ai">
                      <MessageCircle />
                      <span>
                        <strong>Femopedia AI</strong>
                        <small>Compassionate guidance</small>
                      </span>
                    </NavigationMenuLink>
                    <NavigationMenuLink href="#ecosystem-care">
                      <Stethoscope />
                      <span>
                        <strong>Care</strong>
                        <small>Prepare and navigate care</small>
                      </span>
                    </NavigationMenuLink>
                    <NavigationMenuLink href="#ecosystem-pregnancy">
                      <HeartHandshake />
                      <span>
                        <strong>Pregnancy</strong>
                        <small>Every-trimester support</small>
                      </span>
                    </NavigationMenuLink>
                    <NavigationMenuLink href="#ecosystem-baby">
                      <Baby />
                      <span>
                        <strong>Baby</strong>
                        <small>Postpartum and parenting</small>
                      </span>
                    </NavigationMenuLink>
                    <NavigationMenuLink href="#ecosystem-journal">
                      <NotebookPen />
                      <span>
                        <strong>Journal</strong>
                        <small>Private health timeline</small>
                      </span>
                    </NavigationMenuLink>
                    <NavigationMenuLink href="#ecosystem-community">
                      <Users />
                      <span>
                        <strong>Community</strong>
                        <small>Moderated conversations</small>
                      </span>
                    </NavigationMenuLink>
                  </div>
                </div>
              </NavigationMenuContent>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <NavigationMenuLink href="#stages" className={navigationMenuTriggerStyle()}>
                Life stages
              </NavigationMenuLink>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <NavigationMenuLink href="#companion" className={navigationMenuTriggerStyle()}>
                AI companion
              </NavigationMenuLink>
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
      </div>
      {menuOpen && (
        <nav id="mobile-navigation" className="mobile-nav" aria-label="Mobile navigation">
          <a href="#why" onClick={() => setMenuOpen(false)}>
            Why Femopedia
          </a>
          <a href="#ecosystem" onClick={() => setMenuOpen(false)}>
            Ecosystem
          </a>
          <a href="#stages" onClick={() => setMenuOpen(false)}>
            Life stages
          </a>
          <a href="#companion" onClick={() => setMenuOpen(false)}>
            AI companion
          </a>
          <a href="#safety" onClick={() => setMenuOpen(false)}>
            Our approach
          </a>
          <a href="#perspectives" onClick={() => setMenuOpen(false)}>
            Perspectives
          </a>
          <a href="#faq" onClick={() => setMenuOpen(false)}>
            FAQ
          </a>
          <a href="#early-access" onClick={() => setMenuOpen(false)}>
            Join early access
          </a>
        </nav>
      )}
    </header>
  );
}
