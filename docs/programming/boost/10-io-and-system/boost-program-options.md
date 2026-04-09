---
id: boost-program-options
title: Boost.Program_options
sidebar_label: Boost.Program_options
sidebar_position: 3
tags: [c++, boost, program-options, cli, arguments]
---

# Boost.Program_options

`boost::program_options` parses **command-line arguments, config files, and environment variables**
into typed C++ variables. Instead of hand-rolling `getopt` wrappers or writing fragile `argv`
loops, you declare options with names, types, and defaults in one place, and the library handles
parsing, validation, help text generation, and multi-source composition.

:::info The problem it solves
Every non-trivial command-line tool needs option parsing — flags, positional args, defaults, help
text. Doing this with raw `argc`/`argv` is tedious and error-prone. `getopt` helps on POSIX but is
not portable and only handles `char` options. Boost.Program_options gives you a declarative,
type-safe, cross-platform solution that also reads from `.ini` config files.
:::

## Basic usage

```cpp showLineNumbers title="basic_options.cpp"
#include <boost/program_options.hpp>
#include <iostream>

namespace po = boost::program_options;

int main(int argc, char* argv[]) {
    po::options_description desc("Allowed options");
    desc.add_options()
        ("help,h",    "show help message")
        ("output,o",  po::value<std::string>()->default_value("out.txt"),
                       "output file path")
        ("verbose,v", po::bool_switch()->default_value(false),
                       "enable verbose output")
        ("count,n",   po::value<int>()->required(),
                       "number of iterations");

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);

    if (vm.count("help")) {
        std::cout << desc << "\n";
        return 0;
    }

    po::notify(vm);  // triggers required-option checks

    std::string output = vm["output"].as<std::string>();
    bool verbose       = vm["verbose"].as<bool>();
    int count          = vm["count"].as<int>();

    if (verbose)
        std::cout << "writing " << count << " items to " << output << "\n";
}
```

```bash
$ ./app --count 10 --verbose -o result.txt
writing 10 items to result.txt

$ ./app --help
Allowed options:
  -h [ --help ]                  show help message
  -o [ --output ] arg (=out.txt) output file path
  -v [ --verbose ]               enable verbose output
  -n [ --count ] arg             number of iterations
```

## Positional arguments

```cpp showLineNumbers title="positional.cpp"
#include <boost/program_options.hpp>
#include <iostream>
#include <vector>
#include <string>

namespace po = boost::program_options;

int main(int argc, char* argv[]) {
    po::options_description desc("Options");
    desc.add_options()
        ("input",  po::value<std::vector<std::string>>(), "input files")
        ("output", po::value<std::string>(),               "output file");

    po::positional_options_description pos;
    pos.add("input", -1);  // all remaining positional args are "input"

    po::variables_map vm;
    po::store(po::command_line_parser(argc, argv)
        .options(desc).positional(pos).run(), vm);
    po::notify(vm);

    if (vm.count("input")) {
        for (const auto& f : vm["input"].as<std::vector<std::string>>())
            std::cout << "input: " << f << "\n";
    }
}
```

## Config file parsing

Options can be loaded from `.ini`-style config files and composed with command-line arguments:

```cpp showLineNumbers title="config_file.cpp"
#include <boost/program_options.hpp>
#include <fstream>
#include <iostream>

namespace po = boost::program_options;

int main(int argc, char* argv[]) {
    po::options_description config("Config");
    config.add_options()
        ("db.host",  po::value<std::string>()->default_value("localhost"))
        ("db.port",  po::value<int>()->default_value(5432))
        ("db.name",  po::value<std::string>());

    po::variables_map vm;

    // command-line first (higher priority)
    po::store(po::parse_command_line(argc, argv, config), vm);

    // then config file (lower priority — won't overwrite CLI values)
    std::ifstream ifs("app.conf");
    if (ifs)
        po::store(po::parse_config_file(ifs, config), vm);

    po::notify(vm);

    std::cout << "connecting to "
              << vm["db.host"].as<std::string>() << ":"
              << vm["db.port"].as<int>() << "\n";
}
```

```bash
# app.conf
db.host=prod-db.internal
db.port=5433
db.name=myapp
```

:::tip Multi-source composition
`store()` does not overwrite values already in the `variables_map`. Call it once per source in
priority order: command-line first, then config file, then environment variables. The first source
to set a value wins.
:::

## Validation and custom types

Use `notifier` callbacks or custom validators for complex constraints:

```cpp showLineNumbers title="validation.cpp"
#include <boost/program_options.hpp>
#include <stdexcept>

namespace po = boost::program_options;

void validate_port(int port) {
    if (port < 1 || port > 65535)
        throw po::validation_error(
            po::validation_error::invalid_option_value, "port");
}

int main(int argc, char* argv[]) {
    po::options_description desc("Options");
    desc.add_options()
        ("port,p", po::value<int>()->notifier(validate_port), "listen port");

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);  // notifier fires here
}
```

:::warning notify() can throw
`notify()` is where required-option checks and notifier callbacks run. Always call it *after* all
`store()` calls, and be ready to catch `po::error` (or its subclasses like `required_option`).
:::

## Linking

Boost.Program_options is a **compiled** library:

```cmake
find_package(Boost REQUIRED COMPONENTS program_options)
target_link_libraries(myapp PRIVATE Boost::program_options)
```

## See also

- <Icon icon="lucide:hard-drive" inline /> [Boost.Filesystem](./boost-filesystem.md) — often combined for file-path arguments.
- <Icon icon="lucide:terminal" inline /> [Boost.Process](./boost-process.md) — launch subprocesses, sometimes with options forwarded.
- <Icon icon="lucide:hammer" inline /> [CMake integration](../01-build-and-integration/cmake-integration.md) — linking compiled Boost libraries.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
