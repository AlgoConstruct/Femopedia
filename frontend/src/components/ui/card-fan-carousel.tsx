import { useCallback, useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ChevronLeft, ChevronRight } from "lucide-react";

export interface CardItem { imgUrl: string; alt?: string; linkUrl?: string; label?: string; }
interface SocialCardsProps { cards: CardItem[]; }

const MAX_VISIBLE = 7;
const HALF = 3;
const FAN_POSITIONS = [
  { rot: -21, scale: 0.7756, x: -30, y: 7.3, zIndex: 1 },
  { rot: -14, scale: 0.8498, x: -22, y: 4, zIndex: 2 },
  { rot: -7, scale: 0.9346, x: -11, y: 1.3, zIndex: 3 },
  { rot: 0, scale: 1, x: 0, y: 0, zIndex: 10 },
  { rot: 7, scale: 0.9346, x: 11, y: 1.3, zIndex: 3 },
  { rot: 14, scale: 0.8498, x: 22, y: 4, zIndex: 2 },
  { rot: 21, scale: 0.7756, x: 30, y: 7.3, zIndex: 1 },
];

function getResponsiveMultiplier(width: number) {
  if (width < 480) return 0.28;
  if (width < 640) return 0.38;
  if (width < 768) return 0.5;
  if (width < 1024) return 0.75;
  return 1;
}
function getHeightMultiplier(width: number) {
  const idealPx = width < 480 ? 352 : width < 640 ? 416 : width < 768 ? 448 : width < 1024 ? 544 : 608;
  const available = window.innerHeight * 0.7;
  return available >= idealPx ? 1 : available / idealPx;
}
function getSlotConfig(totalCards: number, slot: number) {
  if (totalCards >= MAX_VISIBLE) return FAN_POSITIONS[slot];
  const center = totalCards >> 1;
  const distance = totalCards > 1 ? (slot - center) / center : 0;
  const absDistance = Math.abs(distance);
  return { rot: distance * 21, scale: 1 - 0.2244 * absDistance * absDistance, x: distance * 30, y: absDistance * absDistance * 7.3, zIndex: 10 - Math.abs(slot - center) };
}

export default function CardFanCarousel({ cards }: SocialCardsProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const isAnimating = useRef(false);
  const hasEntered = useRef(false);
  const directionRef = useRef<"left" | "right" | null>(null);
  const prevVisible = useRef<Set<number>>(new Set());
  const totalCards = cards.length;
  const needsPagination = totalCards > MAX_VISIBLE;
  const [centerIndex, setCenterIndex] = useState(needsPagination ? HALF : totalCards >> 1);

  const getVisibleMap = useCallback((center: number) => {
    const map = new Map<number, number>();
    if (!needsPagination) cards.forEach((_, i) => map.set(i, i));
    else for (let slot = 0; slot < MAX_VISIBLE; slot++) map.set(((center + slot - HALF) % totalCards + totalCards) % totalCards, slot);
    return map;
  }, [cards, needsPagination, totalCards]);

  const cycle = useCallback((direction: "left" | "right") => {
    if (isAnimating.current || !needsPagination) return;
    isAnimating.current = true;
    directionRef.current = direction;
    setCenterIndex((prev) => direction === "right" ? (prev + 1) % totalCards : (prev - 1 + totalCards) % totalCards);
  }, [needsPagination, totalCards]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !totalCards) return;
    const cardElements = Array.from(container.querySelectorAll<HTMLElement>(".fan-card"));
    const visibleMap = getVisibleMap(centerIndex);
    const previouslyVisible = prevVisible.current;
    const direction = directionRef.current;
    const isFirstMount = !hasEntered.current;
    const multiplier = getResponsiveMultiplier(window.innerWidth);
    const hMult = getHeightMultiplier(window.innerWidth);
    const slotCount = needsPagination ? MAX_VISIBLE : totalCards;
    const config = (slot: number) => getSlotConfig(slotCount, slot);
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (isFirstMount) isAnimating.current = true;
    let completedCount = 0;
    const onCardDone = () => { if (++completedCount >= visibleMap.size) { isAnimating.current = false; hasEntered.current = true; } };

    cardElements.forEach((card, cardIndex) => {
      const slot = visibleMap.get(cardIndex);
      const wasVisible = previouslyVisible.has(cardIndex);
      if (slot !== undefined) {
        const { x, y, rot, scale, zIndex } = config(slot);
        const target = { x: `${x * multiplier}rem`, y: `${y * hMult}rem`, rotation: rot, scale, opacity: 1, zIndex };
        if (reduceMotion) { gsap.set(card, target); onCardDone(); }
        else if (isFirstMount) { gsap.set(card, { x: 0, y: `${12 * hMult}rem`, rotation: 0, scale: 0.5, opacity: 0 }); gsap.to(card, { ...target, duration: 1.2, ease: "elastic.out(1.05,.78)", delay: 0.2 + slot * 0.06, onComplete: onCardDone }); }
        else if (!wasVisible) { const enterX = direction === "right" ? 40 : -40; gsap.set(card, { x: `${enterX}rem`, y: `${y * hMult}rem`, rotation: direction === "right" ? 30 : -30, scale: 0.5, opacity: 0 }); gsap.to(card, { ...target, duration: 0.6, ease: "power2.out", onComplete: onCardDone }); }
        else gsap.to(card, { ...target, duration: 0.5, ease: "power2.out", onComplete: onCardDone });
      } else if (wasVisible) {
        gsap.to(card, { x: `${direction === "right" ? -40 : 40}rem`, opacity: 0, scale: 0.5, rotation: direction === "right" ? -30 : 30, duration: 0.4, ease: "power2.in", zIndex: 0 });
      } else if (isFirstMount) gsap.set(card, { opacity: 0, scale: 0.3, x: 0, y: 0, zIndex: 0 });
    });
    prevVisible.current = new Set(visibleMap.keys());

    const visibleEntries = cardElements.map((el, i) => ({ el, slot: visibleMap.get(i) })).filter((entry): entry is { el: HTMLElement; slot: number } => entry.slot !== undefined).sort((a, b) => a.slot - b.slot);
    let leaveTimer: ReturnType<typeof setTimeout> | null = null;
    const updateHover = (hovered: number | null) => visibleEntries.forEach(({ el, slot }) => {
      const base = config(slot); let x = base.x * getResponsiveMultiplier(window.innerWidth); let y = base.y * getHeightMultiplier(window.innerWidth); let rotation = base.rot; let scale = base.scale;
      if (hovered !== null && slot === hovered) { y -= 2.5 * getHeightMultiplier(window.innerWidth); scale *= 1.08; }
      else if (hovered !== null) { const distance = Math.abs(slot - hovered); x += (slot < hovered ? -1 : 1) * (7 / (distance + 0.5)) * getResponsiveMultiplier(window.innerWidth); rotation += (slot < hovered ? -1 : 1) * 3 / (distance + 1); }
      gsap.to(el, { x: `${x}rem`, y: `${y}rem`, rotation, scale, duration: 0.45, ease: "power2.out", overwrite: "auto" });
    });
    const handlers = visibleEntries.map(({ el, slot }) => { const handler = () => { if (!isAnimating.current && !reduceMotion) updateHover(slot); }; el.addEventListener("mouseenter", handler); return { el, handler }; });
    const onLeave = () => { if (leaveTimer) clearTimeout(leaveTimer); leaveTimer = setTimeout(() => updateHover(null), 50); };
    const onResize = () => { if (!isAnimating.current) updateHover(null); };
    container.addEventListener("mouseleave", onLeave); window.addEventListener("resize", onResize);
    return () => { handlers.forEach(({ el, handler }) => el.removeEventListener("mouseenter", handler)); container.removeEventListener("mouseleave", onLeave); window.removeEventListener("resize", onResize); if (leaveTimer) clearTimeout(leaveTimer); gsap.killTweensOf(cardElements); };
  }, [centerIndex, getVisibleMap, needsPagination, totalCards]);

  if (!totalCards) return null;
  return <section className="fan-carousel" aria-label="Women across different life stages">
    <div className="fan-layout" ref={containerRef}>{cards.map((card, index) => {
      const image = <><img src={card.imgUrl} loading="lazy" alt={card.alt || `Life stage ${index + 1}`} />{card.label && <span>{card.label}</span>}</>;
      return card.linkUrl ? <a key={card.imgUrl} href={card.linkUrl} className="fan-card">{image}</a> : <div key={card.imgUrl} className="fan-card">{image}</div>;
    })}</div>
    {needsPagination && <div className="fan-controls"><button onClick={() => cycle("left")} aria-label="Previous life stage"><ChevronLeft /></button><div>{cards.map((_, i) => <span key={i} className={i === centerIndex ? "active" : ""} />)}</div><button onClick={() => cycle("right")} aria-label="Next life stage"><ChevronRight /></button></div>}
  </section>;
}
