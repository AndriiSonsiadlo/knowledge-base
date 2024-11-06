import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Knowledge Base',
  tagline: 'Organized notes and structured information',
  favicon: 'img/favicon.ico',
  future: {
    v4: true,
  },
  url: 'https://your-docusaurus-site.example.com',
  baseUrl: '/',
  organizationName: 'AndriiSonsiadlo',
  projectName: 'knowledge-base',

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },
  plugins: ["./src/plugins/tailwind-config.js"],
  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/AndriiSonsiadlo/knowledge-base/tree/master/',
        },
        blog: {
          showReadingTime: true,
          feedOptions: {
            type: ['rss', 'atom'],
            xslt: true,
          },
          editUrl: 'https://github.com/AndriiSonsiadlo/knowledge-base/tree/master/',
          onInlineTags: 'warn',
          onInlineAuthors: 'warn',
          onUntruncatedBlogPosts: 'warn',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    navbar: {
      hideOnScroll: false,
      title: 'Knowledge Base',
      logo: {
        alt: 'Knowledge Base Logo',
        src: 'img/logo.svg',
        srcDark: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'pythonSidebar',
          position: 'left',
          label: 'Python',
        },
        {
          type: 'docSidebar',
          sidebarId: 'cppSidebar',
          position: 'left',
          label: 'C++',
        },
        {to: '/blog', label: 'Blog', position: 'left'},
        // {
        //   type: 'search',
        //   position: 'right',
        // },
        {
          href: 'https://github.com/AndriiSonsiadlo/knowledge-base',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Python',
              to: '/docs/programming/python/intro',
            },
            {
              label: 'C++',
              to: '/docs/programming/c++/intro',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'Blog',
              to: '/blog',
            },
            {
              label: 'GitHub',
              href: 'https://github.com/AndriiSonsiadlo/knowledge-base',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Andrii Sonsiadlo. Knowledge Base.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      // additionalLanguages: ['typescript', 'javascript', 'python', 'bash', 'json', 'yaml', 'cpp', 'c'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
