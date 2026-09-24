import { useLayoutEffect, useRef, type ComponentProps } from "react";

export function useTextareaResize(value: ComponentProps<"textarea">["value"], rows = 1) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const computedStyle = window.getComputedStyle(textarea);
    const lineHeight = Number.parseInt(computedStyle.lineHeight, 10) || 20;
    const padding =
      Number.parseInt(computedStyle.paddingTop, 10) +
      Number.parseInt(computedStyle.paddingBottom, 10);
    const minimumHeight = lineHeight * rows + padding;

    textarea.style.height = "0px";
    textarea.style.height = `${Math.max(textarea.scrollHeight, minimumHeight) + 2}px`;
  }, [value, rows]);

  return textareaRef;
}
