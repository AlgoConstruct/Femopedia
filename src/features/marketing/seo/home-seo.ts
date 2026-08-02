import { faqs, HOME_DESCRIPTION, HOME_TITLE, SITE_URL } from "@/features/marketing/data/content";

export const homeMeta = [
  { title: HOME_TITLE },
  { name: "description", content: HOME_DESCRIPTION },
  { name: "author", content: "Femopedia" },
  { name: "application-name", content: "Femopedia" },
  {
    name: "robots",
    content: "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1",
  },
  { name: "theme-color", content: "#FAFBFA", media: "(prefers-color-scheme: light)" },
  { name: "theme-color", content: "#101620", media: "(prefers-color-scheme: dark)" },
  { property: "og:type", content: "website" },
  { property: "og:site_name", content: "Femopedia" },
  { property: "og:locale", content: "en_US" },
  { property: "og:url", content: `${SITE_URL}/` },
  { property: "og:title", content: HOME_TITLE },
  { property: "og:description", content: HOME_DESCRIPTION },
  { property: "og:image", content: `${SITE_URL}/brand/social-card.png` },
  { property: "og:image:width", content: "1200" },
  { property: "og:image:height", content: "630" },
  {
    property: "og:image:alt",
    content: "Femopedia—living intelligence for every stage of womanhood",
  },
  { name: "twitter:card", content: "summary_large_image" },
  { name: "twitter:title", content: HOME_TITLE },
  { name: "twitter:description", content: HOME_DESCRIPTION },
  { name: "twitter:image", content: `${SITE_URL}/brand/social-card.png` },
];

export const homeLinks = [
  { rel: "canonical", href: `${SITE_URL}/` },
  { rel: "manifest", href: "/brand/site.webmanifest" },
  { rel: "apple-touch-icon", href: "/brand/apple-touch-icon.png", sizes: "180x180" },
  { rel: "preconnect", href: "https://images.unsplash.com" },
];

export const homeStructuredData = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${SITE_URL}/#organization`,
      name: "Femopedia",
      url: `${SITE_URL}/`,
      logo: {
        "@type": "ImageObject",
        url: `${SITE_URL}/brand/icon-512.png`,
        width: 512,
        height: 512,
      },
      description: HOME_DESCRIPTION,
      email: "hello@femopedia.com",
    },
    {
      "@type": "WebSite",
      "@id": `${SITE_URL}/#website`,
      url: `${SITE_URL}/`,
      name: "Femopedia",
      description: HOME_DESCRIPTION,
      publisher: { "@id": `${SITE_URL}/#organization` },
      inLanguage: "en",
    },
    {
      "@type": "WebPage",
      "@id": `${SITE_URL}/#webpage`,
      url: `${SITE_URL}/`,
      name: HOME_TITLE,
      description: HOME_DESCRIPTION,
      isPartOf: { "@id": `${SITE_URL}/#website` },
      about: { "@id": `${SITE_URL}/#organization` },
      primaryImageOfPage: { "@type": "ImageObject", url: `${SITE_URL}/brand/social-card.png` },
      inLanguage: "en",
    },
    {
      "@type": "FAQPage",
      "@id": `${SITE_URL}/#faq`,
      mainEntity: faqs.map(({ question, answer }) => ({
        "@type": "Question",
        name: question,
        acceptedAnswer: { "@type": "Answer", text: answer },
      })),
    },
  ],
};
