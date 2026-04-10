---
id: boost-beast
title: Boost.Beast
sidebar_label: Boost.Beast
sidebar_position: 2
tags: [c++, boost, beast, http, websocket, networking]
---

# Boost.Beast

Boost.Beast is a **header-only** C++ library for HTTP and WebSocket, built directly on top of
[Boost.Asio](../09-concurrency-and-async/boost-asio.md). It provides low-level message types for
HTTP (request, response, fields, body) and a complete WebSocket implementation — all with first-class
async support. Beast does not try to be a web framework; it gives you the protocol primitives and
lets you compose them.

:::info The problem it solves
Asio gives you TCP sockets. Turning raw bytes into structured HTTP messages or WebSocket frames is
a substantial amount of work: chunked transfer encoding, upgrade handshakes, header parsing, frame
masking. Beast handles all of that while staying in the Asio style — same patterns, same completion
tokens, same coroutine support.
:::

## HTTP client — synchronous GET

```cpp showLineNumbers title="http_get.cpp"
#include <boost/beast.hpp>
#include <boost/asio.hpp>
#include <iostream>

namespace beast = boost::beast;
namespace http = beast::http;
namespace net = boost::asio;
using tcp = net::ip::tcp;

int main() {
    net::io_context io;
    tcp::resolver resolver(io);
    beast::tcp_stream stream(io);

    auto results = resolver.resolve("example.com", "80");
    stream.connect(results);

    http::request<http::string_body> req(http::verb::get, "/", 11);
    req.set(http::field::host, "example.com");
    req.set(http::field::user_agent, "boost-beast");
    http::write(stream, req);

    beast::flat_buffer buf;
    http::response<http::string_body> res;
    http::read(stream, buf, res);

    std::cout << res.result_int() << " " << res.reason() << "\n";
    std::cout << res.body().substr(0, 200) << "\n";

    stream.socket().shutdown(tcp::socket::shutdown_both);
}
```

```mermaid
flowchart LR
    A[Create tcp_stream] --> B[Resolve + connect]
    B --> C[Build HTTP request]
    C --> D[http::write]
    D --> E[http::read response]
    E --> F[Process body]
```

## HTTP body types

Beast separates the message **header** (verb, target, fields) from the **body** using a body type
parameter. Several built-in body types cover common needs:

| Body type | Use case |
|-----------|----------|
| `string_body` | Small responses read entirely into a `std::string` |
| `dynamic_body` | Growing buffer, no size limit up front |
| `file_body` | Stream directly to/from a file on disk |
| `empty_body` | HEAD requests or responses with no content |
| `buffer_body` | Caller-provided buffer, useful for incremental reads |

:::tip Streaming large responses
Use `http::response_parser` with `buffer_body` to read a response chunk by chunk instead of
loading it all into memory. This is how you download a 2 GB file without allocating 2 GB of RAM.
:::

## Async HTTP client

Replace `http::write` / `http::read` with their async counterparts and the code becomes
non-blocking:

```cpp showLineNumbers title="async_http.cpp"
#include <boost/beast.hpp>
#include <boost/asio.hpp>
#include <iostream>

namespace beast = boost::beast;
namespace http = beast::http;
namespace net = boost::asio;
using tcp = net::ip::tcp;

net::awaitable<void> fetch() {
    auto executor = co_await net::this_coro::executor;
    tcp::resolver resolver(executor);
    beast::tcp_stream stream(executor);

    auto results = co_await resolver.async_resolve("example.com", "80", net::use_awaitable);
    co_await stream.async_connect(results, net::use_awaitable);

    http::request<http::string_body> req(http::verb::get, "/", 11);
    req.set(http::field::host, "example.com");
    co_await http::async_write(stream, req, net::use_awaitable);

    beast::flat_buffer buf;
    http::response<http::string_body> res;
    co_await http::async_read(stream, buf, res, net::use_awaitable);

    std::cout << res.body().substr(0, 200) << "\n";
}

int main() {
    net::io_context io;
    net::co_spawn(io, fetch(), net::detached);
    io.run();
}
```

:::note Coroutine support
The `co_await` style requires C++20 coroutines and `use_awaitable`. Beast also works with
callbacks, `yield_context` (stackful coroutines via Boost.Coroutine2), and futures.
:::

## WebSocket

Beast's WebSocket implementation handles the upgrade handshake, frame encoding/decoding, pings,
pongs, and close frames.

```cpp showLineNumbers title="ws_echo.cpp"
#include <boost/beast.hpp>
#include <boost/asio.hpp>
#include <iostream>

namespace beast = boost::beast;
namespace ws = beast::websocket;
namespace net = boost::asio;
using tcp = net::ip::tcp;

int main() {
    net::io_context io;
    tcp::resolver resolver(io);
    ws::stream<tcp::socket> stream(io);

    auto results = resolver.resolve("echo.websocket.events", "80");
    net::connect(stream.next_layer(), results);
    stream.handshake("echo.websocket.events", "/");

    stream.write(net::buffer(std::string("hello websocket")));

    beast::flat_buffer buf;
    stream.read(buf);
    std::cout << beast::make_printable(buf.data()) << "\n";

    stream.close(ws::close_code::normal);
}
```

## Server-side HTTP

Beast works equally well for servers. Accept a TCP connection, read a request, build a response,
write it back.

```cpp showLineNumbers title="http_server_snippet.cpp"
#include <boost/beast.hpp>
#include <boost/asio.hpp>

namespace beast = boost::beast;
namespace http = beast::http;
namespace net = boost::asio;
using tcp = net::ip::tcp;

void handle_request(beast::tcp_stream& stream) {
    beast::flat_buffer buf;
    http::request<http::string_body> req;
    http::read(stream, buf, req);

    http::response<http::string_body> res(http::status::ok, req.version());
    res.set(http::field::content_type, "text/plain");
    res.body() = "hello from beast";
    res.prepare_payload();
    http::write(stream, res);
}
```

:::warning Beast is not a framework
Beast gives you HTTP message types and I/O operations — it is not Express or Flask. Routing,
middleware, session management, and templating are your responsibility. Libraries like
Boost.URL can help with URL parsing.
:::

## Beast versus other C++ HTTP libraries

| Feature | Beast | cpp-httplib | libcurl |
|---------|-------|-------------|---------|
| Async | Full (Asio-native) | Blocking only | Callback-based multi |
| WebSocket | Yes | No | No |
| Header-only | Yes | Yes | No |
| SSL/TLS | Via Asio SSL | Built-in | Built-in |
| HTTP/2 | No | No | Yes |

## See also

- <Icon icon="lucide:network" inline /> [Asio Networking](./asio-networking.md) — TCP/UDP sockets underneath Beast.
- <Icon icon="lucide:cpu" inline /> [Boost.Asio](../09-concurrency-and-async/boost-asio.md) — the async model Beast builds on.
- <Icon icon="lucide:database" inline /> [Boost.JSON](../12-serialization-and-data/boost-json.md) — parse JSON payloads from HTTP responses.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
