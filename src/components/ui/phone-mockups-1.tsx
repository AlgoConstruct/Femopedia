import { type ImageItem, PhoneCarousel } from "@/components/ui/phone-mockups-1-utils/phone-carousel";

const femopediaScreens: ImageItem[] = [
  { src: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=900&h=1500&q=88", alt: "Woman smiling in soft natural light", eyebrow: "Your daily check-in", title: "Good morning, Maya.", copy: "How are your body and mind feeling today?" },
  { src: "https://images.unsplash.com/photo-1488426862026-3ee34a7d66df?auto=format&fit=crop&w=900&h=1500&q=88", alt: "Woman enjoying a peaceful outdoor moment", eyebrow: "Femopedia AI", title: "Ask what feels hard to ask.", copy: "Get thoughtful context without judgment or overconfidence." },
  { src: "https://images.unsplash.com/photo-1678739201887-34001155c5e0?auto=format&fit=crop&w=900&h=1500&q=88", alt: "Pregnant woman standing in natural light", eyebrow: "Week 24", title: "Your pregnancy, understood.", copy: "Evidence-informed guidance for changes, choices, and questions." },
  { src: "https://images.unsplash.com/photo-1542385151-efd9000785a0?auto=format&fit=crop&w=900&h=1500&q=88", alt: "Mother holding her newborn", eyebrow: "Postpartum care", title: "Support for you, too.", copy: "Recovery and emotional wellbeing matter alongside newborn care." },
];

export default function PhoneMockupBasic() {
  return <PhoneCarousel images={femopediaScreens} />;
}
