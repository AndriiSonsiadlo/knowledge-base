import { themes as prismThemes } from "prism-react-renderer";

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "My Knowledge Base",
  tagline: "Organized notes and structured information",
  favicon: "img/favicon.ico",

  // Set the production url of your site here
  url: "https://andriisonsiadlo.github.io/",
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: "/knowledge-base/",

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: "AndriiSonsiadlo",
  projectName: "knowledge-base",
  onBrokenLinks: "throw",
  customFields: {
    githubUrl: "https://github.com/AndriiSonsiadlo/knowledge-base",
  },
  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: "warn",
    },
  },

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  // Enable Docusaurs Faster: https://github.com/facebook/docusaurus/issues/10556
  future: {
    faster: true,
    v4: true,
  },

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: "./sidebars.js",
          showLastUpdateTime: true,
          editUrl:
            "https://github.com/AndriiSonsiadlo/knowledge-base/tree/master/",
        },
        blog: false,
        theme: {
          customCss: "./src/css/custom.css",
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: "img/social-card.png",
      navbar: {
        hideOnScroll: false,
        items: [
          {
            type: "docSidebar",
            sidebarId: "programmingSidebar",
            position: "left",
            label: "Programming",
            description:
              "Learn Python, C++, and master modern programming languages with practical examples.",
            icon: "💻",
          },
          {
            type: "docSidebar",
            sidebarId: "gameDevSidebar",
            position: "left",
            label: "Game Development",
            description:
              "Build games with Unreal Engine 5 and C++ — from engine internals to shipping.",
            icon: "🎮",
          },
          {
            type: "docSidebar",
            sidebarId: "computerScienceSidebar",
            position: "left",
            label: "Computer Science",
            description:
              "Deep dive into systems, architecture, memory, networking, and core algorithms.",
            icon: "⚙️",
          },
          {
            type: "docSidebar",
            sidebarId: "dataToolsSidebar",
            position: "left",
            label: "Data Science",
            description:
              "Practical analysis, wrangling, ETL, querying, visualization, and notebook-first workflows.",
            icon: "🔧",
          },
          {
            type: "docSidebar",
            sidebarId: "machineLearningSidebar",
            position: "left",
            label: "Machine Learning",
            description:
              "Master fundamentals, neural networks, NLP, and modern ML architectures.",
            icon: "🤖",
          },
          // {
          //   to: "/blog",
          //   label: "Blog",
          //   position: "right",
          // },
          // {
          //   to: '/about-me',
          //   label: 'About Me',
          //   position: 'right'
          // },
          {
            href: "https://github.com/AndriiSonsiadlo/knowledge-base",
            position: "right",
            className: "header-github-link",
            "aria-label": "GitHub repository",
          },
        ],
      },
      footer: {
        style: "dark", // light
        links: [
          {
            title: "Docs",
            items: [
              {
                label: "Programming",
                to: "/docs/programming/intro",
              },
              {
                label: "Game Development",
                to: "/docs/category/unreal-engine-5",
              },
              {
                label: "Computer Science",
                to: "/docs/computer-science/intro",
              },
              {
                label: "Data Science",
                to: "/docs/data-tools",
              },
              {
                label: "Machine Learning",
                to: "/docs/machine-learning/intro",
              },
            ],
          },
          {
            title: "More",
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
        additionalLanguages: ["bash", "cmake", "csharp", "ini"],
        additionalPlugins: ["line-numbers", "show-language"],
      },
    }),

  themes: [
    "@docusaurus/theme-mermaid",
    [
      require.resolve("@easyops-cn/docusaurus-search-local"),
      {
        indexPages: true,
        docsRouteBasePath: "/docs",
        hashed: true,
        language: ["en"],
        highlightSearchTermsOnTargetPage: false,
        searchResultContextMaxLength: 50,
        searchResultLimits: 8,
        searchBarShortcut: true,
        searchBarShortcutHint: true,
      },
    ],
  ],
  plugins: [
    ["./src/plugins/webpack-alias.js", {}],
    ["./src/plugins/tailwind-config.js", {}],
    ["./src/plugins/recent-docs-plugin.js", { limit: 6 }],
    [
      "ideal-image",
      /** @type {import('@docusaurus/plugin-ideal-image').PluginOptions} */
      ({
        quality: 70,
        max: 1030,
        min: 640,
        steps: 2,
        // Use false to debug, but it incurs huge perf costs
        disableInDev: true,
      }),
    ],
    [
      "./src/plugins/blog-plugin",
      {
        path: "blog",
        editLocalizedFiles: false,
        blogTitle: "Blog",
        blogDescription: "Blog description is here ...",
        blogSidebarCount: "ALL",
        blogSidebarTitle: "List blog",
        routeBasePath: "blog",
        include: ["**/*.md", "**/*.mdx"],
        exclude: [
          "**/_*.{js,jsx,ts,tsx,md,mdx}",
          "**/_*/**",
          "**/*.test.{js,jsx,ts,tsx}",
          "**/__tests__/**",
        ],
        postsPerPage: 6,
        truncateMarker: /<!--\s*(truncate)\s*-->/,
        showReadingTime: true,
        onUntruncatedBlogPosts: "ignore",
        // Remove this to remove the "edit this page" links.
        editUrl:
          "https://github.com/namnguyenthanhwork/docusaurus-tailwind-shadcn-template/tree/main/",
        remarkPlugins: [
          [require("@docusaurus/remark-plugin-npm2yarn"), { sync: true }],
        ],
      },
    ],
  ],
};

export default config;
