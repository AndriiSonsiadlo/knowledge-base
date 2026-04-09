---
id: boost-interprocess
title: Boost.Interprocess
sidebar_label: Boost.Interprocess
sidebar_position: 7
tags: [c++, boost, interprocess, shared-memory, ipc]
---

# Boost.Interprocess

`Boost.Interprocess` provides portable **inter-process communication (IPC)** primitives: shared
memory regions, memory-mapped files, named mutexes and condition variables, and message queues. Its
most powerful feature is the ability to place STL-compatible containers — vectors, maps, strings —
directly in shared memory so that multiple processes can read and modify them without serialization.

:::info The problem it solves
When two processes need to share data, the options are sockets, pipes, files, or shared memory. Shared
memory is the fastest — no kernel copies, no serialization — but the POSIX and Windows APIs are
completely different and managing offsets manually is error-prone. Boost.Interprocess wraps this in a
portable, high-level C++ API with allocators that let you use standard containers in shared memory.
:::

## Managed shared memory

`managed_shared_memory` creates a named shared memory segment and provides an allocator-aware heap
inside it. You construct named objects directly in the segment.

```cpp showLineNumbers title="shm_create.cpp"
#include <boost/interprocess/managed_shared_memory.hpp>
#include <iostream>

namespace bip = boost::interprocess;

int main() {
    bip::shared_memory_object::remove("MyShm");

    bip::managed_shared_memory segment(bip::create_only, "MyShm", 65536);

    int* val = segment.construct<int>("answer")(42);
    std::cout << "created: " << *val << "\n";
}
```

```cpp showLineNumbers title="shm_open.cpp"
#include <boost/interprocess/managed_shared_memory.hpp>
#include <iostream>

namespace bip = boost::interprocess;

int main() {
    bip::managed_shared_memory segment(bip::open_only, "MyShm");

    auto result = segment.find<int>("answer");
    if (result.first)
        std::cout << "found: " << *result.first << "\n";
}
```

## STL containers in shared memory

The key insight: standard containers use allocators, and Boost.Interprocess provides allocators that
draw memory from a shared segment. This lets you place a `vector`, `map`, or `string` in shared
memory without manual offset arithmetic.

```cpp showLineNumbers title="shm_vector.cpp"
#include <boost/interprocess/managed_shared_memory.hpp>
#include <boost/interprocess/containers/vector.hpp>
#include <boost/interprocess/allocators/allocator.hpp>

namespace bip = boost::interprocess;

using ShmAllocator = bip::allocator<int, bip::managed_shared_memory::segment_manager>;
using ShmVector = boost::container::vector<int, ShmAllocator>;

int main() {
    bip::shared_memory_object::remove("VecShm");
    bip::managed_shared_memory segment(bip::create_only, "VecShm", 65536);

    ShmAllocator alloc(segment.get_segment_manager());
    ShmVector* vec = segment.construct<ShmVector>("data")(alloc);

    vec->push_back(10);
    vec->push_back(20);
    vec->push_back(30);
}
```

:::warning Pointers do not work across processes
A raw pointer in shared memory is useless to another process — the segment may be mapped at a
different virtual address. Use `offset_ptr` (Boost.Interprocess provides this) instead of raw
pointers for anything stored in shared memory.
:::

## Named synchronization

Named mutexes and condition variables let processes synchronize access to shared data:

```cpp showLineNumbers title="named_mutex.cpp"
#include <boost/interprocess/sync/named_mutex.hpp>
#include <boost/interprocess/sync/scoped_lock.hpp>

namespace bip = boost::interprocess;

int main() {
    bip::named_mutex mtx(bip::open_or_create, "MyMutex");
    {
        bip::scoped_lock<bip::named_mutex> lock(mtx);
        // critical section — safe across processes
    }
}
```

## Message queues

For simple send/receive communication without shared memory management:

```cpp showLineNumbers title="message_queue.cpp"
#include <boost/interprocess/ipc/message_queue.hpp>

namespace bip = boost::interprocess;

void sender() {
    bip::message_queue::remove("mq");
    bip::message_queue mq(bip::create_only, "mq", 100, sizeof(int));
    int val = 42;
    mq.send(&val, sizeof(val), 0);
}

void receiver() {
    bip::message_queue mq(bip::open_only, "mq");
    int val;
    bip::message_queue::size_type recvd;
    unsigned int prio;
    mq.receive(&val, sizeof(val), recvd, prio);
}
```

## Memory-mapped files

`managed_mapped_file` works identically to `managed_shared_memory` but backs the segment with a
file on disk. Data persists across reboots.

```cpp showLineNumbers
#include <boost/interprocess/managed_mapped_file.hpp>

namespace bip = boost::interprocess;

int main() {
    bip::managed_mapped_file file(bip::open_or_create, "/tmp/data.bin", 65536);
    int* val = file.find_or_construct<int>("counter")(0);
    ++(*val);
}
```

:::tip Shared memory versus memory-mapped files
Shared memory is faster (no filesystem overhead) but volatile — it vanishes on reboot. Memory-mapped
files persist but involve filesystem I/O. Choose based on whether you need persistence.
:::

## Cleanup

Shared memory segments and named primitives persist in the OS until explicitly removed. Always clean
up:

```cpp showLineNumbers
bip::shared_memory_object::remove("MyShm");
bip::named_mutex::remove("MyMutex");
bip::message_queue::remove("mq");
```

:::danger Leaked shared memory
If a process crashes without calling `remove`, the shared memory segment remains in the OS. On Linux,
check `/dev/shm/` for stale segments. Use RAII wrappers (`remove_shared_memory_on_destroy`) to
reduce the risk.
:::

## See also

- <Icon icon="lucide:waypoints" inline /> [Boost.Thread](./boost-thread.md) — in-process threading and synchronization.
- <Icon icon="lucide:lock" inline /> [Boost.Lockfree](./boost-lockfree.md) — lock-free queues for in-process communication.
- <Icon icon="lucide:memory-stick" inline /> [Smart Pointers](../03-smart-pointers-and-memory/smart-ptr-overview.md) — in-process memory management.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
