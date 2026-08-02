import type { CSSProperties, ReactNode } from "react";
import { Baby, BookOpen, HeartPulse, MessageCircle, NotebookPen, ShieldCheck } from "lucide-react";

interface GlassEffectProps { children: ReactNode; className?: string; style?: CSSProperties; href?: string; }
interface DockItem { icon: ReactNode; label: string; href: string; }

function GlassEffect({ children, className = "", style = {}, href }: GlassEffectProps) {
  const glassStyle = { boxShadow: "0 8px 28px rgba(23,35,63,.2), 0 0 30px rgba(255,255,255,.1)", transitionTimingFunction: "cubic-bezier(.175,.885,.32,1.4)", ...style };
  const content = <div className={`liquid-glass relative overflow-hidden ${className}`} style={glassStyle}><div className="liquid-glass-distortion" /><div className="liquid-glass-tint" /><div className="liquid-glass-shine" /><div className="liquid-glass-content">{children}</div></div>;
  return href ? <a href={href} className="block">{content}</a> : content;
}
function GlassDock({ items }: { items: DockItem[] }) {
  return <GlassEffect className="glass-dock"><div className="glass-dock-items">{items.map((item) => <a href={item.href} key={item.label} aria-label={item.label}><span>{item.icon}</span><small>{item.label}</small></a>)}</div></GlassEffect>;
}
function GlassButton({ children, href }: { children: ReactNode; href: string }) { return <GlassEffect href={href} className="glass-question">{children}</GlassEffect>; }
function GlassFilter() {
  return <svg aria-hidden="true" className="glass-filter"><filter id="glass-distortion" x="0%" y="0%" width="100%" height="100%" filterUnits="objectBoundingBox"><feTurbulence type="fractalNoise" baseFrequency="0.001 0.005" numOctaves="1" seed="17" result="turbulence" /><feComponentTransfer in="turbulence" result="mapped"><feFuncR type="gamma" amplitude="1" exponent="10" offset="0.5" /><feFuncG type="gamma" amplitude="0" exponent="1" offset="0" /><feFuncB type="gamma" amplitude="0" exponent="1" offset="0.5" /></feComponentTransfer><feGaussianBlur in="turbulence" stdDeviation="3" result="softMap" /><feSpecularLighting in="softMap" surfaceScale="5" specularConstant="1" specularExponent="100" lightingColor="white" result="specLight"><fePointLight x="-200" y="-200" z="300" /></feSpecularLighting><feComposite in="specLight" operator="arithmetic" k1="0" k2="1" k3="1" k4="0" result="litImage" /><feDisplacementMap in="SourceGraphic" in2="softMap" scale="120" xChannelSelector="R" yChannelSelector="G" /></filter></svg>;
}
export function Component() {
  const items: DockItem[] = [
    { icon: <MessageCircle />, label: "Ask AI", href: "#companion" }, { icon: <BookOpen />, label: "Learn", href: "#ecosystem" }, { icon: <HeartPulse />, label: "Wellbeing", href: "#stages" }, { icon: <Baby />, label: "Pregnancy", href: "#stages" }, { icon: <NotebookPen />, label: "Journal", href: "#ecosystem" }, { icon: <ShieldCheck />, label: "Care", href: "#safety" },
  ];
  return <div className="liquid-showcase"><GlassFilter /><div className="liquid-showcase-copy"><img src="/brand/mark.svg" alt="" /><p>Femopedia understands that every day is different.</p><h2>What do you need<br />today?</h2></div><div className="liquid-actions"><GlassDock items={items} /><GlassButton href="#companion"><span>Ask anything about your health</span><MessageCircle /></GlassButton></div><p className="liquid-boundary"><ShieldCheck /> Educational support with clear medical boundaries</p></div>;
}
