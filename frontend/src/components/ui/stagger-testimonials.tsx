import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Quote } from "lucide-react";
import { cn } from "@/lib/utils";

export interface Testimonial {
  id: number;
  testimonial: string;
  by: string;
  imgSrc: string;
}

const testimonials: Testimonial[] = [
  {
    id: 0,
    testimonial:
      "I want health information that explains what is known, what is uncertain, and what I can do next.",
    by: "Maya, navigating cycle changes",
    imgSrc: "/images/perspectives/maya.webp",
  },
  {
    id: 1,
    testimonial:
      "Sometimes I need context before I decide whether a symptom is worth bringing to my doctor.",
    by: "Nina, working professional",
    imgSrc: "/images/perspectives/nina.webp",
  },
  {
    id: 2,
    testimonial:
      "Pregnancy advice is everywhere. I want one calm place that helps me separate evidence from noise.",
    by: "Leah, expecting her first baby",
    imgSrc: "/images/perspectives/leah.webp",
  },
  {
    id: 3,
    testimonial:
      "After birth, everyone asked about the baby. I needed someone to ask how I was recovering too.",
    by: "Amara, new mother",
    imgSrc: "/images/perspectives/amara.webp",
  },
  {
    id: 4,
    testimonial:
      "I do not want another app that turns my body into streaks, scores, and reminders I can fail.",
    by: "Sofia, living with PCOS",
    imgSrc: "/images/perspectives/sofia.webp",
  },
  {
    id: 5,
    testimonial:
      "My health history should feel like one continuous story, not scattered notes I have to reconstruct.",
    by: "Priya, caregiver and parent",
    imgSrc: "/images/perspectives/priya.webp",
  },
  {
    id: 6,
    testimonial:
      "Midlife came with questions I was never prepared to ask. Clear language would have changed everything.",
    by: "Elena, navigating perimenopause",
    imgSrc: "/images/perspectives/elena.webp",
  },
];

interface TestimonialCardProps {
  position: number;
  testimonial: Testimonial;
  handleMove: (steps: number) => void;
  cardSize: number;
}

function TestimonialCard({ position, testimonial, handleMove, cardSize }: TestimonialCardProps) {
  const isCenter = position === 0;
  return (
    <article
      onClick={() => handleMove(position)}
      className={cn("testimonial-card", isCenter && "center-card")}
      style={{
        width: cardSize,
        height: cardSize,
        transform: `translate(-50%,-50%) translateX(${(cardSize / 1.55) * position}px) translateY(${isCenter ? -48 : position % 2 ? 13 : -13}px) rotate(${isCenter ? 0 : position % 2 ? 2.2 : -2.2}deg)`,
      }}
      aria-hidden={!isCenter}
    >
      <Quote className="testimonial-quote" />
      <img
        src={testimonial.imgSrc}
        alt={testimonial.by.split(",")[0]}
        width="240"
        height="280"
        loading="lazy"
        decoding="async"
      />
      <blockquote>“{testimonial.testimonial}”</blockquote>
      <p>— {testimonial.by}</p>
    </article>
  );
}

export function StaggerTestimonials() {
  const [cardSize, setCardSize] = useState(365);
  const [items, setItems] = useState(testimonials);
  const handleMove = (steps: number) => {
    if (!steps) return;
    setItems((current) => {
      const next = [...current];
      if (steps > 0) for (let i = 0; i < steps; i++) next.push(next.shift()!);
      else for (let i = 0; i > steps; i--) next.unshift(next.pop()!);
      return next;
    });
  };
  useEffect(() => {
    const updateSize = () =>
      setCardSize(window.matchMedia("(min-width: 640px)").matches ? 365 : 286);
    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, []);
  return (
    <div
      className="stagger-testimonials"
      aria-roledescription="carousel"
      aria-label="Community perspectives"
    >
      {items.map((testimonial, index) => (
        <TestimonialCard
          key={testimonial.id}
          testimonial={testimonial}
          handleMove={handleMove}
          position={index - Math.floor(items.length / 2)}
          cardSize={cardSize}
        />
      ))}
      <div className="testimonial-controls">
        <button onClick={() => handleMove(-1)} aria-label="Previous perspective">
          <ChevronLeft />
        </button>
        <span>
          {Math.floor(items.length / 2) + 1} / {items.length}
        </span>
        <button onClick={() => handleMove(1)} aria-label="Next perspective">
          <ChevronRight />
        </button>
      </div>
    </div>
  );
}
