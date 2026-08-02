import { createFileRoute } from "@tanstack/react-router";
import FemopediaLandingPage from "@/features/marketing/pages/FemopediaLandingPage";
import { homeLinks, homeMeta, homeStructuredData } from "@/features/marketing/seo/home-seo";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: homeMeta,
    links: homeLinks,
    scripts: [{ type: "application/ld+json", children: JSON.stringify(homeStructuredData) }],
  }),
  component: FemopediaLandingPage,
});
