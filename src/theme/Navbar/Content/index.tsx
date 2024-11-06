import React, {type ReactNode} from 'react';
import clsx from 'clsx';
import {
    useThemeConfig,
    ErrorCauseBoundary,
    ThemeClassNames,
    useColorMode,
} from '@docusaurus/theme-common';
import {
  splitNavbarItems,
  useNavbarMobileSidebar,
} from '@docusaurus/theme-common/internal';
import NavbarItem, {type Props as NavbarItemConfig} from '@theme/NavbarItem';
import NavbarColorModeToggle from '@theme/Navbar/ColorModeToggle';
import SearchBar from '@theme/SearchBar';
import NavbarMobileSidebarToggle from '@theme/Navbar/MobileSidebar/Toggle';
import NavbarLogo from '@theme/Navbar/Logo';
import NavbarSearch from '@theme/Navbar/Search';

import styles from './styles.module.css';

function useNavbarItems() {
    return useThemeConfig().navbar.items as NavbarItemConfig[];
}
function NavbarContentLayout({
                                 left,
                                 right,
                             }: {
    left: ReactNode;
    right: ReactNode;
}) {
    return (
        <div className="navbar__inner">
            <div
                className={clsx(
                    ThemeClassNames.layout.navbar.containerLeft,
                    'navbar__items',
                )}>
                {left}
            </div>
            <div
                className={clsx(
                    ThemeClassNames.layout.navbar.containerRight,
                    'navbar__items navbar__items--right',
                )}>
                {right}
            </div>
        </div>
    );
}


function NavbarItems({items, isMobile}: {
    items: NavbarItemConfig[],
    isMobile?: boolean
}): ReactNode {
    const {colorMode} = useColorMode();
    const isDarkTheme = colorMode === 'dark';

    return (
        <>
            {items.map((item, i) => {
                if (item.type === 'search') return null;

                return (
                    <ErrorCauseBoundary
                        key={i}
                        onError={(error) =>
                            new Error(
                                `A theme navbar item failed to render.
Please double-check the following navbar item (themeConfig.navbar.items) of your Docusaurus config:
${JSON.stringify(item, null, 2)}`,
                                {cause: error},
                            )
                        }>
                        {isMobile ? (
                            <div className={clsx(
                                'block px-4 py-2 rounded-lg transition-colors',
                                isDarkTheme
                                    ? 'text-slate-300 hover:text-white hover:bg-white/10'
                                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                            )}>
                                <NavbarItem {...item} />
                            </div>
                        ) : (
                            <div
                                className={clsx(
                                    'transition-colors relative group',
                                    isDarkTheme
                                        ? 'text-slate-300 hover:text-white'
                                        : 'text-slate-600 hover:text-slate-900'
                                )}>
                                <NavbarItem {...item} />
                                <span
                                    className="absolute bottom-0 left-0 w-0 h-0.5 bg-gradient-to-r from-purple-400 to-blue-400 group-hover:w-full transition-all duration-300"></span>
                            </div>
                        )}
                    </ErrorCauseBoundary>
                );
            })}
        </>
    );
}

export default function NavbarContent(): ReactNode {
    const mobileSidebar = useNavbarMobileSidebar();

    const {colorMode} = useColorMode();
    const isDarkTheme = colorMode === 'dark';

    const items = useNavbarItems();
    const [leftItems, rightItems] = splitNavbarItems(items);

    const searchBarItem = items.find((item) => item.type === 'search');

    return (
        <NavbarContentLayout
            left={
            <>
                {/* Desktop Navigation */}
                {/*<div className="hidden md:flex items-center gap-8">*/}
                    <NavbarItems items={leftItems}/>
                {/*</div>*/}
            </>
            }
            right={
            <>
                {/* Right side items */}
                {/*<div className="hidden md:flex items-center gap-4">*/}
                    <NavbarItems items={rightItems}/>
                    {/*{!searchBarItem && (*/}
                    {/*    <NavbarSearch>*/}
                    {/*        <SearchBar />*/}
                    {/*    </NavbarSearch>*/}
                    {/*)}*/}
                {/*</div>*/}
            </>
            }
        />
    );
}
