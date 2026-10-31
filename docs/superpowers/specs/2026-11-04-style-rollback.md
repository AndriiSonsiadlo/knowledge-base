# Rolling back to the pre-Workbench style

The previous look is preserved by the git tag **`style/pre-workbench`** (commit `4fbc5a5`). Rolling back restores only site chrome — no file under `docs/` is touched, so content written since stays.

Push the tag once so it survives on GitHub: `git push origin style/pre-workbench`.

## Steps

```bash
git switch -c style-rollback

# 1. Stop loading the Workbench stylesheet (keep the rest of the config as it is now)
#    In docusaurus.config.js, remove "./src/css/workbench.css" from theme.customCss.

# 2. Restore chrome files from the tag
git checkout style/pre-workbench -- \
  src/components/CategoryCard src/components/CategoryGrid src/components/GlassCard \
  src/components/HomeIntro src/components/RecentDocs src/components/ScrollReveal \
  src/components/StatsSection src/hooks/useCountUp.ts \
  src/components/navbar/ResponsiveSearch \
  src/pages/index.tsx src/pages/index.module.css \
  src/theme/Navbar/Content/index.js src/theme/Navbar/Logo/index.js

# 3. Remove the Workbench stylesheet (optional; it is inert once unlisted)
git rm src/css/workbench.css

# 4. Verify
npm run build
git diff --stat style/pre-workbench -- docs/ | tail -1   # content diff is expected (new docs); nothing is reverted
git diff --stat HEAD -- docs/                            # must be empty
```

Notes:

- `@fontsource/inter` and `@fontsource/jetbrains-mono` become unused; remove them from `package.json` if you want a clean dependency list.
- `src/components/navbar/ResponsiveSearch` is restored with its old search-modal bug (input offset, focus on the close button); re-apply commit `4a6dee0` if you want to keep that fix.
- Sidebar category labels had hand-typed numbers removed in `73731a7` (auto-numbering lives in `workbench.css`). The old style has no auto-numbers; revert `73731a7` if you want them back.
