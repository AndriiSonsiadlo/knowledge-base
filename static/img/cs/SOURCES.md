# Image sources — `static/img/cs/`

Third-party figures republished under `docs/computer-science/`. Every image referenced from a
page in that section has a row here, so any figure can be located, re-sourced, or removed
without searching 70+ Markdown files.

All figures come from Wikimedia Commons and are used under the licence named in the table. SVG
sources are stored as Commons' own PNG rendering so they display identically in every browser;
animated GIFs are stored as originals so the animation survives.

Convention: figures are placed with the global `<Figure>` MDX component (`src/components/Figure.jsx`),
never a bare Markdown image, because it supplies the light plate that keeps dark-stroke diagrams
readable against the dark theme, plus the visible caption and attribution the licences require.

```md
<Figure src="/img/cs/<section>/<name>.png"
        alt="..." caption="..."
        source="Wikimedia Commons"
        href="https://commons.wikimedia.org/wiki/File:..."
        license="CC BY-SA 3.0" />
```

Add `photo` for photographs and screenshots, which want no plate.

Refetch everything with `node tools/fetch-commons.mjs <manifest.json>`.

| file | source | author | licence |
|---|---|---|---|
| `algorithms/avl-rotation.gif` | https://commons.wikimedia.org/wiki/File:AVL_Tree_Example.gif | Bruno Schalch | CC BY-SA 4.0 |
| `algorithms/bfs-order.png` | https://commons.wikimedia.org/wiki/File:Breadth-first-tree.svg | Alexander Drichel | CC BY 3.0 |
| `algorithms/big-o-definition.png` | https://commons.wikimedia.org/wiki/File:Big-O-notation.png | w:it:User:Fede_Reghe | Public domain |
| `algorithms/binary-search-tree.png` | https://commons.wikimedia.org/wiki/File:Binary_search_tree.svg | No machine-readable author provided. Dcoetzee assumed (based on copyright claims). | Public domain |
| `algorithms/binary-search.png` | https://commons.wikimedia.org/wiki/File:Binary_Search_Depiction.svg | AlwaysAngry | CC BY-SA 4.0 |
| `algorithms/bubble-sort.gif` | https://commons.wikimedia.org/wiki/File:Sorting_bubblesort_anim.gif | Simpsons contributor | CC BY-SA 3.0 |
| `algorithms/complexity-growth-rates.png` | https://commons.wikimedia.org/wiki/File:Comparison_computational_complexity.svg | Cmglee | CC BY-SA 4.0 |
| `algorithms/dag.png` | https://commons.wikimedia.org/wiki/File:Directed_acyclic_graph_2.svg | Johannes Rössel ( talk ) | Public domain |
| `algorithms/dfs-order.png` | https://commons.wikimedia.org/wiki/File:Depth-first-tree.svg | Alexander Drichel | CC BY-SA 3.0 |
| `algorithms/dijkstra.gif` | https://commons.wikimedia.org/wiki/File:Dijkstra_Animation.gif | Ibmua | Public domain |
| `algorithms/hash-table-chaining.png` | https://commons.wikimedia.org/wiki/File:Hash_table_4_1_1_0_0_1_0_LL.svg | Jorge Stolfi | Public domain |
| `algorithms/hash-table-load-factor.png` | https://commons.wikimedia.org/wiki/File:Hash_table_average_insertion_time.png | Derrick Coetzee ( User:Dcoetzee ) | Public domain |
| `algorithms/hash-table.png` | https://commons.wikimedia.org/wiki/File:Hash_table_3_1_1_0_1_0_0_SP.svg | Jorge Stolfi | CC BY-SA 3.0 |
| `algorithms/heapsort.gif` | https://commons.wikimedia.org/wiki/File:Sorting_heapsort_anim.gif | de:User:RolandH | CC BY-SA 3.0 |
| `algorithms/insertion-sort.gif` | https://commons.wikimedia.org/wiki/File:Insertion-sort-example.gif | Swfung8 | CC BY-SA 3.0 |
| `algorithms/max-heap.png` | https://commons.wikimedia.org/wiki/File:Max-Heap.svg | Ermishin | CC BY-SA 3.0 |
| `algorithms/mergesort-diagram.png` | https://commons.wikimedia.org/wiki/File:Merge_sort_algorithm_diagram.svg | VineetKumar at English Wikipedia | Public domain |
| `algorithms/mergesort.gif` | https://commons.wikimedia.org/wiki/File:Merge-sort-example-300px.gif | Swfung8 | CC BY-SA 3.0 |
| `algorithms/quicksort-diagram.png` | https://commons.wikimedia.org/wiki/File:Quicksort-diagram.svg | Znupi | Public domain |
| `algorithms/quicksort.gif` | https://commons.wikimedia.org/wiki/File:Sorting_quicksort_anim.gif | Wikipedia:en:User:RolandH | CC BY-SA 3.0 |
| `algorithms/red-black-tree.png` | https://commons.wikimedia.org/wiki/File:Red-black_tree_example.svg | Cburnett | CC BY-SA 3.0 |
| `algorithms/selection-sort.gif` | https://commons.wikimedia.org/wiki/File:Selection-Sort-Animation.gif | en:Joestape89 | CC BY-SA 3.0 |
| `algorithms/singly-linked-list.png` | https://commons.wikimedia.org/wiki/File:Singly-linked-list.svg | Vectorization: Lasindi | Public domain |
| `algorithms/stack.png` | https://commons.wikimedia.org/wiki/File:Data_stack.svg | User:Boivie | Public domain |
| `algorithms/topological-order.png` | https://commons.wikimedia.org/wiki/File:Topological_Ordering.svg | David Eppstein | CC0 |
| `algorithms/trie.png` | https://commons.wikimedia.org/wiki/File:Trie_example.svg | Booyabazooka (based on PNG image by Deco ). Modifications by Superm401 . | Public domain |
| `algorithms/undirected-graph.png` | https://commons.wikimedia.org/wiki/File:6n-graf.svg | AzaToth | Public domain |
| `assembly/call-stack-layout.png` | https://commons.wikimedia.org/wiki/File:Call_stack_layout.svg | R. S. Shaw | Public domain |
| `bit-manipulation/ascii-table.png` | https://commons.wikimedia.org/wiki/File:Ascii_Table-nocolor.svg | ZZT32 | Public domain |
| `bit-manipulation/ieee754-single.png` | https://commons.wikimedia.org/wiki/File:IEEE_754_Single_Floating_Point_Format.svg | Codekaizen | CC BY 3.0 |
| `buses-and-io/i2c-bus.png` | https://commons.wikimedia.org/wiki/File:I2C.svg | en:user:Cburnett | CC BY-SA 3.0 |
| `buses-and-io/pcie-slots.jpg` | https://commons.wikimedia.org/wiki/File:PCI-E_%26_PCI_slots_on_DFI_LanParty_nF4_SLI-DR_20050531.jpg | w:user:snickerdo | CC BY-SA 3.0 |
| `buses-and-io/spi-three-peripherals.png` | https://commons.wikimedia.org/wiki/File:SPI_three_slaves.svg | en:User:Cburnett | CC BY-SA 3.0 |
| `buses-and-io/usb-connectors.jpg` | https://commons.wikimedia.org/wiki/File:Usb_connectors.JPG | Viljo Viitanen | Public domain |
| `computer-networks/ethernet-frame.png` | https://commons.wikimedia.org/wiki/File:Ethernet_Type_II_Frame_format.svg | unknown | Public domain |
| `computer-networks/ipv4-packet.png` | https://commons.wikimedia.org/wiki/File:IPv4_Packet-en.svg | Michel Bakni | CC BY-SA 4.0 |
| `computer-networks/osi-model-communication.png` | https://commons.wikimedia.org/wiki/File:OSI-model-Communication.svg | Runtux | Public domain |
| `computer-networks/tcp-three-way-handshake.png` | https://commons.wikimedia.org/wiki/File:TCP_Three-Way_Handshake.svg | Fleshgrinder and The People from The Tango! Desktop Project . | Public domain |
| `computer-networks/udp-encapsulation.png` | https://commons.wikimedia.org/wiki/File:UDP_encapsulation.svg | en:User:Cburnett original work, colorization by en:User:Kbrose | CC BY-SA 3.0 |
| `cpu-architecture/amdahls-law.png` | https://commons.wikimedia.org/wiki/File:AmdahlsLaw.svg | Daniels220 at English Wikipedia | CC BY-SA 3.0 |
| `cpu-architecture/five-stage-pipeline.png` | https://commons.wikimedia.org/wiki/File:Fivestagespipeline.png | unknown | CC BY-SA 3.0 |
| `cpu-architecture/superscalar-pipeline.png` | https://commons.wikimedia.org/wiki/File:Superscalarpipeline.svg | Amit6 , original version ( File:Superscalarpipeline.png ) by User:Poil | CC BY-SA 3.0 |
| `cpu-architecture/topology-hwloc.png` | https://commons.wikimedia.org/wiki/File:Hwloc.png | The Portable Hardware Locality (hwloc) Project. (Screenshot by the Open Source Grid Engine Project) | BSD |
| `cpu-architecture/von-neumann.png` | https://commons.wikimedia.org/wiki/File:Von_Neumann_Architecture.svg | Kapooht | CC BY-SA 3.0 |
| `databases/b-tree.png` | https://commons.wikimedia.org/wiki/File:B-tree.svg | CyHawk | CC BY-SA 3.0 |
| `databases/cap-theorem.png` | https://commons.wikimedia.org/wiki/File:CAP_Theorem.svg | Mooond | CC BY-SA 4.0 |
| `databases/relational-terms.png` | https://commons.wikimedia.org/wiki/File:Relational_database_terms.svg | User:Booyabazooka | Public domain |
| `memory-hierarchy/cache-hierarchy.png` | https://commons.wikimedia.org/wiki/File:Cache_Hierarchy_Updated.png | Kbbuch | CC BY-SA 4.0 |
| `memory-hierarchy/dram-array.png` | https://commons.wikimedia.org/wiki/File:Square_array_of_mosfet_cells_read.png | Glogger at English Wikipedia | CC BY-SA 3.0 |
| `memory-hierarchy/memory-hierarchy.png` | https://commons.wikimedia.org/wiki/File:ComputerMemoryHierarchy.svg | ComputerMemoryHierarchy.png : User:Danlash at en.wikipedia.org | Public domain |
| `memory-hierarchy/virtual-memory.png` | https://commons.wikimedia.org/wiki/File:Virtual_memory.svg | Ehamberg | CC BY-SA 3.0 |
| `memory-hierarchy/x86-paging-4k.png` | https://commons.wikimedia.org/wiki/File:X86_Paging_4K.svg | RokerHRO | CC BY-SA 3.0 |
| `operating-systems/dining-philosophers.png` | https://commons.wikimedia.org/wiki/File:An_illustration_of_the_dining_philosophers_problem.png | Benjamin D. Esham ( bdesham ) | CC BY-SA 3.0 |
| `operating-systems/process-states.png` | https://commons.wikimedia.org/wiki/File:Process_states.svg | No machine-readable author provided. A3r0 assumed (based on copyright claims). | Public domain |
| `operating-systems/thread-pool.png` | https://commons.wikimedia.org/wiki/File:Thread_pool.svg | en:User:Cburnett | CC BY-SA 3.0 |
| `protocols/digital-signature.png` | https://commons.wikimedia.org/wiki/File:Digital_Signature_diagram.svg | Acdx | CC BY-SA 3.0 |
| `protocols/dns-name-space.png` | https://commons.wikimedia.org/wiki/File:Domain_name_space.svg | unknown | Public domain |
| `protocols/dns-resolution.png` | https://commons.wikimedia.org/wiki/File:DNS_Architecture.svg | Aaron Filbert | CC BY-SA 4.0 |
| `protocols/http-persistent-connection.png` | https://commons.wikimedia.org/wiki/File:HTTP_persistent_connection.svg | helix84 | Public domain |
| `protocols/public-key-encryption.png` | https://commons.wikimedia.org/wiki/File:Public_key_encryption.svg | Davidgothberg | Public domain |
| `protocols/symmetric-key-encryption.png` | https://commons.wikimedia.org/wiki/File:Symmetric_key_encryption.svg | Phayzfaustyn | CC0 |
| `storage/ext2-inode.png` | https://commons.wikimedia.org/wiki/File:Ext2-inode.svg | timtjtim | CC BY-SA 4.0 |
| `storage/flash-cell-structure.png` | https://commons.wikimedia.org/wiki/File:Flash_cell_structure.svg | Cyferz at English Wikipedia | CC BY 2.5 |
| `storage/hdd-anatomy.png` | https://commons.wikimedia.org/wiki/File:Hard_drive.svg | Surachit | CC BY-SA 3.0 |
| `storage/hdd-platters-and-head.jpg` | https://commons.wikimedia.org/wiki/File:Hard_disk_platters_and_head.jpg | Mfield , Matthew Field, http://www.photography.mattfield.com | CC BY-SA 3.0 |
