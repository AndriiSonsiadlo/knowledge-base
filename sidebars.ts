import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

/**
 * Creating a sidebar enables you to:
 * - create an ordered group of docs
 * - render a sidebar for each doc of that group
 * - provide next/previous navigation
 *
 * The sidebars can be generated from the filesystem, or explicitly defined here.
 */
const sidebars: SidebarsConfig = {
    pythonSidebar: [
        'programming/python/intro',
        {
            type: 'category',
            label: 'Python',
            items: [
                'programming/python/intro',
                'programming/python/basics',
                'programming/python/advanced',
            ],
        },
    ],
    cppSidebar: [
        {
            type: 'category',
            label: 'C++',
            items: [
                'programming/c++/intro',
                'programming/c++/stl',
            ],
        },
    ],
};

export default sidebars;
