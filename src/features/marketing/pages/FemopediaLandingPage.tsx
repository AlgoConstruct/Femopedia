import { FloatingChatWidget } from "@/components/ui/floating-chat-widget-shadcnui";
import {
  EcosystemSection,
  HeroSection,
  LifeStagesSection,
  PrinciplesSection,
  ProductPreviewSection,
  SafetySection,
} from "@/features/marketing/components/CoreSections";
import { SiteFooter } from "@/features/marketing/components/SiteFooter";
import { SiteHeader } from "@/features/marketing/components/SiteHeader";
import {
  FaqSection,
  PerspectivesSection,
  PromiseSection,
} from "@/features/marketing/components/TrustSections";
import { WaitlistSection } from "@/features/marketing/components/WaitlistSection";

export default function FemopediaLandingPage() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-background text-foreground">
      <SiteHeader />
      <main id="top">
        <HeroSection />
        <PrinciplesSection />
        <EcosystemSection />
        <LifeStagesSection />
        <ProductPreviewSection />
        <SafetySection />
        <PromiseSection />
        <PerspectivesSection />
        <FaqSection />
        <WaitlistSection />
      </main>
      <SiteFooter />
      <FloatingChatWidget />
    </div>
  );
}
