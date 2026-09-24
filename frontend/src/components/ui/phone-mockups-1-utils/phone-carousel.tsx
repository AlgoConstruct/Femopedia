import { type CSSProperties, useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, LockKeyhole, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface ImageItem {
  src: string;
  alt?: string;
  eyebrow?: string;
  title?: string;
  copy?: string;
}

interface PhoneCarouselProps {
  images: ImageItem[];
}

export function PhoneCarousel({ images }: PhoneCarouselProps) {
  const [active, setActive] = useState(0);
  const total = images.length;
  const move = (direction: number) => setActive((current) => (current + direction + total) % total);

  useEffect(() => {
    if (total < 2) return;
    const timer = window.setInterval(() => setActive((current) => (current + 1) % total), 6000);
    return () => window.clearInterval(timer);
  }, [total]);

  if (!total) return null;

  return (
    <div
      className="phone-carousel"
      aria-roledescription="carousel"
      aria-label="Femopedia mobile experience"
    >
      <div className="phone-stage">
        {images.map((image, index) => {
          const offset = (((index - active + total) % total) + total) % total;
          const signedOffset = offset > total / 2 ? offset - total : offset;
          return (
            <article
              className="phone-device"
              data-active={signedOffset === 0}
              key={image.src}
              aria-hidden={signedOffset !== 0}
              style={{ "--phone-offset": signedOffset } as CSSProperties}
            >
              <div className="phone-hardware">
                <span className="phone-speaker" />
                <div className="phone-screen">
                  <img
                    src={image.src}
                    alt={image.alt || "Femopedia mobile screen"}
                    width="900"
                    height="1500"
                    loading="lazy"
                    decoding="async"
                  />
                  <div className="phone-screen-shade" />
                  <div className="phone-status">
                    <span>9:41</span>
                    <LockKeyhole />
                  </div>
                  <div className="phone-brand">
                    <img src="/brand/mark.svg" alt="" width="150" height="150" /> Femopedia
                  </div>
                  <div className="phone-copy">
                    <span>
                      <Sparkles /> {image.eyebrow}
                    </span>
                    <h3>{image.title}</h3>
                    <p>{image.copy}</p>
                    <div className="phone-action">
                      Explore guidance <ChevronRight />
                    </div>
                  </div>
                </div>
              </div>
            </article>
          );
        })}
      </div>
      {total > 1 && (
        <div className="phone-controls">
          <Button
            variant="outline"
            size="icon"
            onClick={() => move(-1)}
            aria-label="Previous screen"
          >
            <ChevronLeft />
          </Button>
          <div>
            {images.map((_, index) => (
              <button
                key={index}
                className={index === active ? "active" : ""}
                onClick={() => setActive(index)}
                aria-label={`Show screen ${index + 1}`}
                aria-current={index === active}
              />
            ))}
          </div>
          <Button variant="outline" size="icon" onClick={() => move(1)} aria-label="Next screen">
            <ChevronRight />
          </Button>
        </div>
      )}
    </div>
  );
}
