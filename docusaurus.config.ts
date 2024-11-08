import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

const config: Config = {
  title: "My Knowledge Base",
  tagline: "Organized notes and structured information",
  favicon: "img/favicon.ico",
  future: {
    v4: true,
  },
  url: "https://your-docusaurus-site.example.com",
  baseUrl: "/",
  organizationName: "AndriiSonsiadlo",
  projectName: "knowledge-base",
  onBrokenLinks: "throw",
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },
  plugins: [
    "./src/plugins/tailwind-config.js",
    [
      "@cmfcmf/docusaurus-search-local",
      {
        indexDocs: true,
        indexPages: true,
        language: "en",
        style: undefined,
      },
    ],
  ],
  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: "./sidebars.ts",
          editUrl:
            "https://github.com/AndriiSonsiadlo/knowledge-base/tree/master/",
        },
        blog: {
          showReadingTime: true,
          feedOptions: {
            type: ["rss", "atom"],
            xslt: true,
          },
          editUrl:
            "https://github.com/AndriiSonsiadlo/knowledge-base/tree/master/",
          onInlineTags: "warn",
          onInlineAuthors: "warn",
          onUntruncatedBlogPosts: "warn",
        },
        theme: {
          customCss: "./src/css/custom.css",
        },
      } satisfies Preset.Options,
    ],
  ],
  themeConfig: {
    image: "img/docusaurus-social-card.jpg",
    colorMode: {
      defaultMode: "dark",
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    navbar: {
      hideOnScroll: false,
      title: "My Knowledge Base",
      logo: {
        alt: "Knowledge Base Logo",
        src: "img/logo.svg",
        srcDark: "img/logo.svg",
      },
      items: [
        {
          type: "docSidebar",
          sidebarId: "programmingSidebar",
          position: "left",
          label: "Programming",
        },
        {
          type: "docSidebar",
          sidebarId: "computerScienceSidebar",
          position: "left",
          label: "Computer Science",
        },
        {
          type: "docSidebar",
          sidebarId: "dataStructuresSidebar",
          position: "left",
          label: "Data & Algorithms",
        },
        {
          type: "docSidebar",
          sidebarId: "machineLearningaSidebar",
          position: "left",
          label: "Machine Learning",
        },
        {
          to: "/blog",
          label: "Blog",
          position: "right",
        },
      ],
    },
    footer: {
      style: "light",
      links: [
        {
          title: "Topics",
          items: [
            {
              label: "Programming",
              to: "/docs/programming/intro",
            },
            {
              label: "Computer Science",
              to: "/docs/computer-science/intro",
            },
            {
              label: "Data & Algorithms",
              to: "/docs/data-structures-algorithms/intro",
            },
            {
              label: "Machine Learning",
              to: "/docs/machine-learning/intro",
            },
          ],
        },
        {
          title: "Resources",
          items: [
            {
              label: "Blog",
              to: "/blog",
            },
            {
              label: "GitHub",
              href: "https://github.com/AndriiSonsiadlo/knowledge-base",
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Andrii Sonsiadlo. Knowledge Base.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
