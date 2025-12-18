import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebars: SidebarsConfig = {
  programmingSidebar: [
    "programming/intro",
    {
      type: "category",
      label: "Python",
      items: ["programming/python/intro"],
    },
    {
      type: "category",
      label: "C++",
      items: [
        "programming/cpp/intro",
        "programming/cpp/basics",
        {
          type: "category",
          label: "Concurrency",
          items: [
            "programming/cpp/concurrency/intro",
            "programming/cpp/concurrency/threads",
            "programming/cpp/concurrency/mutexes",
            "programming/cpp/concurrency/atomic",
          ],
        },
        {
          type: "category",
          label: "STL",
          items: [
            "programming/cpp/stl/intro",
            "programming/cpp/stl/containers",
            "programming/cpp/stl/iterators",
            "programming/cpp/stl/algorithms",
          ],
        },
      ],
    },
  ],

  computerScienceSidebar: [
    "computer-science/intro",
    {
      type: "category",
      label: "Operating Systems",
      items: [
        "computer-science/os/intro",
        "computer-science/os/processes",
        "computer-science/os/scheduling",
        "computer-science/os/memory",
      ],
    },
    {
      type: "category",
      label: "Architecture",
      items: [
        "computer-science/architecture/intro",
        "computer-science/architecture/cpu-design",
        "computer-science/architecture/instruction-sets",
      ],
    },
    {
      type: "category",
      label: "Bit Manipulation",
      items: [
        "computer-science/bit-manipulation/intro",
        "computer-science/bit-manipulation/basics",
        "computer-science/bit-manipulation/techniques",
      ],
    },
    {
      type: "category",
      label: "Processor",
      items: [
        "computer-science/processor/intro",
        "computer-science/processor/pipelining",
      ],
    },
    {
      type: "category",
      label: "Memory Management",
      items: [
        "computer-science/memory-management/intro",
        "computer-science/memory-management/allocation",
        "computer-science/memory-management/garbage-collection",
      ],
    },
  ],

  dataStructuresSidebar: [
    "data-structures-algorithms/intro",
    {
      type: "category",
      label: "Sorting",
      items: [
        "data-structures-algorithms/sorting/intro",
        "data-structures-algorithms/sorting/bubble-sort",
        "data-structures-algorithms/sorting/quicksort",
        "data-structures-algorithms/sorting/mergesort",
      ],
    },
    {
      type: "category",
      label: "Searching",
      items: [
        "data-structures-algorithms/searching/intro",
        "data-structures-algorithms/searching/binary-search",
        "data-structures-algorithms/searching/linear-search",
      ],
    },
  ],

  dataToolsSidebar: [
    {
      type: "category",
      label: "Pandas",
      items: [
        "data-tools/pandas/overview",
        {
          type: "category",
          label: "Foundations",
          items: [
            "data-tools/pandas/foundations/core-concepts",
            "data-tools/pandas/foundations/io-reading-writing",
          ],
        },
        {
          type: "category",
          label: "Selection",
          items: [
            "data-tools/pandas/selection/selecting-columns",
            "data-tools/pandas/selection/boolean-filtering",
            "data-tools/pandas/selection/loc-vs-iloc",
          ],
        },
      ],
    },
  ],

  machineLearningSidebar: [
    "machine-learning/intro",
    {
      type: "category",
      label: "Fundamentals",
      items: [
        "machine-learning/fundamentals/intro",
        "machine-learning/fundamentals/supervised-learning",
        "machine-learning/fundamentals/unsupervised-learning",
      ],
    },
    {
      type: "category",
      label: "Neural Networks",
      items: [
        "machine-learning/neural-networks/intro",
        "machine-learning/neural-networks/perceptron",
        "machine-learning/neural-networks/backpropagation",
      ],
    },
    {
      type: "category",
      label: "NLP",
      items: [
        "machine-learning/nlp/intro",
        "machine-learning/nlp/transformers",
      ],
    },
  ],
};

export default sidebars;
