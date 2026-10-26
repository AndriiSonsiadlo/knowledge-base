import Layout from "@theme/Layout";
import React from "react";
import {
  AboutSection,
  ContactSection,
  HeroSection,
  SkillsSection,
} from "@/components/Personal";

export default function About() {
  return (
    <Layout
      title="About Me"
      description="Software Engineer turned Entrepreneur. I love building things and helping people."
    >
      <div className="background-grid background-grid--fade-out">
        <HeroSection />
        <AboutSection />
        <SkillsSection />
        <ContactSection />
      </div>
    </Layout>
  );
}
