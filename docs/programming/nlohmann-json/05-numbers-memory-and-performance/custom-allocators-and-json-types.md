---
id: custom-allocators-and-json-types
title: Custom allocators and JSON types
sidebar_label: Custom types
sidebar_position: 2
tags: [c++, nlohmann-json, allocators, basic-json]
---

# Custom allocators and JSON types

`json` is one instantiation of a template; changing its parameters is how you get ordered keys, a different map, or a different allocator.
