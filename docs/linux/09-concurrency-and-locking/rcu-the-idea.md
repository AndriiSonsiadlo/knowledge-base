---
id: rcu-the-idea
title: "RCU: The Idea"
sidebar_label: "RCU: the idea"
sidebar_position: 8
tags: [linux, kernel, locking]
prerequisites:
  - linux/concurrency-and-locking/memory-ordering-and-barriers
draft: false
---

# RCU: The Idea

Readers that take no locks and pay nothing, writers that publish a new version and defer reclamation until every reader has left.

:::info[Not yet written]
This page is a stub. See [the roadmap](../00-overview/roadmap.md) for what lands when.
:::
