module.exports = function recentDocsPlugin(_context, options = {}) {
  return {
    name: "recent-docs-plugin",
    async allContentLoaded({ allContent, actions }) {
      const docsContent = allContent["docusaurus-plugin-content-docs"]?.default;

      if (!docsContent) {
        actions.setGlobalData({ docs: [] });
        return;
      }

      const docs = docsContent.loadedVersions
        .flatMap((version) => version.docs)
        .filter(
          (doc) =>
            !doc.unlisted &&
            !doc.draft &&
            !doc.id.startsWith("superpowers/") &&
            doc.lastUpdatedAt,
        )
        .sort((a, b) => b.lastUpdatedAt - a.lastUpdatedAt)
        .slice(0, options.limit ?? 6)
        .map((doc) => ({
          title: doc.title,
          description: doc.description,
          permalink: doc.permalink,
          lastUpdatedAt: doc.lastUpdatedAt,
        }));

      actions.setGlobalData({ docs });
    },
  };
};
