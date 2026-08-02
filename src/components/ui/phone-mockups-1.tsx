import {
  type ImageItem,
  PhoneCarousel,
} from "@/components/ui/phone-mockups-1-utils/phone-carousel";

const femopediaScreens: ImageItem[] = [
  {
    src: "/images/app/daily-check-in.webp",
    alt: "Woman smiling in soft natural light",
    eyebrow: "Your daily check-in",
    title: "Good morning, Maya.",
    copy: "How are your body and mind feeling today?",
  },
  {
    src: "/images/app/ai-guidance.webp",
    alt: "Woman enjoying a peaceful outdoor moment",
    eyebrow: "Femopedia AI",
    title: "Ask what feels hard to ask.",
    copy: "Get thoughtful context without judgment or overconfidence.",
  },
  {
    src: "/images/app/pregnancy.webp",
    alt: "Pregnant woman standing in natural light",
    eyebrow: "Week 24",
    title: "Your pregnancy, understood.",
    copy: "Evidence-informed guidance for changes, choices, and questions.",
  },
  {
    src: "/images/app/postpartum.webp",
    alt: "Mother holding her newborn",
    eyebrow: "Postpartum care",
    title: "Support for you, too.",
    copy: "Recovery and emotional wellbeing matter alongside newborn care.",
  },
];

export default function PhoneMockupBasic() {
  return <PhoneCarousel images={femopediaScreens} />;
}
