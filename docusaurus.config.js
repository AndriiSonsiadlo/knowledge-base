import { themes as prismThemes } from "prism-react-renderer";
import knowledgeGraphPlugin from "./src/plugins/knowledge-graph-plugin.js";
import remarkWavedrom from "./src/plugins/remark-wavedrom.js";

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "Knowledge Base by Andrii Sonsiadlo",
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
    // The Linux section is pinned to one LTS. Every source link on every page
    // is generated from this value by <Src>. Bumping it re-points the whole
    // section; see docs/superpowers/specs/2026-08-28-linux-kernel-docs-design.md.
    // v6.18: released 2025-11-30, longterm, projected EOL Dec 2028.
    linuxKernelVersion: "v6.18",
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
    // Only the CSS minimizer: cssnano/clean-css can't parse the `@layer` rules
    // emitted by `v4.useCssCascadeLayers` and silently drops infima's :root.
    faster: { lightningCssMinimizer: true },
    v4: true,
  },

  headTags: [
    {
      tagName: "script",
      attributes: {},
      innerHTML: `(function(){try{if(localStorage.getItem("docs-sidebar-collapsed")==="true"){document.documentElement.setAttribute("data-sidebar-collapsed","true");}}catch(e){}})();`,
    },
  ],

  stylesheets: [
    {
      href: "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css",
      type: "text/css",
      crossorigin: "anonymous",
    },
  ],

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: "./sidebars.js",
          // Internal working artifacts (design specs, implementation plans).
          // Not knowledge-base content, not in any sidebar, and their relative
          // links point at other sections — which breaks `onBrokenLinks: throw`.
          // `exclude` replaces rather than merges with the plugin defaults, so
          // the defaults are repeated here alongside the new entry to keep the
          // standard underscore-prefixed-partial convention working.
          exclude: [
            "**/_*.{js,jsx,ts,tsx,md,mdx}",
            "**/_*/**",
            "**/*.test.{js,jsx,ts,tsx}",
            "**/__tests__/**",
            "superpowers/**",
          ],
          showLastUpdateTime: true,
          editUrl:
            "https://github.com/AndriiSonsiadlo/knowledge-base/tree/master/",
          remarkPlugins: [require("remark-math"), remarkWavedrom],
          rehypePlugins: [require("rehype-katex")],
        },
        blog: false,
        theme: {
          customCss: ["./src/css/custom.css", "./src/css/linux-components.css"],
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: "img/social-card-v2.png",
      docs: {
        sidebar: {
          hideable: true,
        },
      },
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
            icon: "code",
          },
          {
            type: "dropdown",
            position: "left",
            label: "Systems",
            items: [
              {
                type: "docSidebar",
                sidebarId: "computerScienceSidebar",
                label: "Computer Science",
                description:
                  "Deep dive into systems, architecture, memory, networking, and core algorithms.",
                icon: "cpu",
              },
              {
                type: "docSidebar",
                sidebarId: "gpuComputingSidebar",
                label: "GPU & Accelerators",
                description:
                  "CUDA, GPU architecture, kernel optimization, and NPU/inference accelerators.",
                icon: "rocket",
              },
              {
                type: "docSidebar",
                sidebarId: "embeddedSidebar",
                label: "Embedded Systems",
                description:
                  "Bare-metal firmware, Cortex-M architecture, RTOS, embedded Linux, safety and security.",
                icon: "plug",
              },
              {
                type: "docSidebar",
                sidebarId: "linuxSidebar",
                label: "Linux & Kernel",
                description:
                  "How Linux actually works: boot, syscalls, scheduling, memory, VFS, networking, drivers, containers, eBPF.",
                icon: "terminal",
              },
            ],
          },
          {
            type: "dropdown",
            position: "left",
            label: "AI & Data",
            items: [
              {
                type: "docSidebar",
                sidebarId: "machineLearningSidebar",
                label: "Machine Learning",
                description:
                  "Master fundamentals, neural networks, NLP, and modern ML architectures.",
                icon: "bot",
              },
              {
                type: "docSidebar",
                sidebarId: "dataToolsSidebar",
                label: "Data Science",
                description:
                  "Practical analysis, wrangling, ETL, querying, visualization, and notebook-first workflows.",
                icon: "database",
              },
            ],
          },
          {
            type: "docSidebar",
            sidebarId: "gameDevSidebar",
            position: "left",
            label: "Game Development",
            description:
              "Build games with Unreal Engine 5 and C++ — from engine internals to shipping.",
            icon: "gamepad",
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
              {
                label: "GPU & Accelerators",
                to: "/docs/gpu-computing/",
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
        additionalLanguages: [
          "armasm",
          "bash",
          "c",
          "cmake",
          "cpp",
          "csharp",
          "diff",
          "docker",
          "glsl",
          "hlsl",
          "ini",
          "json",
          "makefile",
          "nasm",
          "python",
          "systemd",
          "toml",
          "wgsl",
          "yaml",
        ],
        additionalPlugins: ["line-numbers", "show-language"],
      },
    }),

  themes: [
    "@docusaurus/theme-mermaid",
    "@docusaurus/theme-live-codeblock",
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
    [knowledgeGraphPlugin, { scopes: ["linux/"] }],
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
      "docusaurus-plugin-image-zoom",
      { selector: ".markdown img, .kb-figure__plate img" },
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
