# Python / Go Ctype/CGo investigation

Goal: How easy/fast/convenient is it to hand off execution responsibilities from C to a SO/DLL/Dylib?

Background: Python is a notoriously slow language. However, it can be sped up dramatically by using C extensions, and libraries built off of that (e.g. Pydantic, Numpy). Python _also_ supports loading shared libraries. It stands to reason that the shared libraries likely can be faster executors than python -- after all, they're not tied to python, just merely interop with it.

But C is, if not difficult, then a little picky. But, there are other solutions - Rust, Zig, and Go are possible options. Go, in particular, is a pretty interesting option in what it theoretically offers -- an easier build environment being the primary reason it was picked here.

In general, this kind of interaction is referred to generically as an FFI -- or Foreign Function Interface. Many languages support this, both to create the .SO files, but also to load the .SO files. This project focuses explicitly on the go/python boundry, but in general, both parts can be interpreted in the context of a different language.

So, what is the experience like of using an SO file without writing (much) C?

## About this project

I came to this knowing Python and Go well, but never using ctypes or cgo. Thus, this project offers the following:

1. An example of how to pass values between the two, documented under [playground](./playground)
2. A test of speed, and moderate complexity. This is documented under [aoc](./aoc/readme.md), and is pulled from [my solution](https://github.com/JoelAtDeluxe/AdventOfCode2016/tree/master) for [Advent of Code 2016, day 12](https://adventofcode.com/2016/day/12) -- this hadn't been touch since I initially solved it 7 years ago, so I wanted to do a bit of updating before I really solved it, but the solution is fundamentally the same as it was then, which I document in more detail under aoc.

## Test Environment & Results

Note that I did the investigation on Linux, using x86_64 architecture (AMD Ryzen 7 7840U). Given the nature of this work, I assume that this should carry over to modern Mac and Windows computers, and in general modern hardware. I'm less confident as we get further away from modern.

Python version used: 3.14.7
Go version used: 1.27.0

Pure Go solution: 0.024 seconds to solve (average)
Pure Python solution: 1.89 seconds to solve (average)
Python w/ Go SO: 0.030 seconds to solve (average)

### Findings

1. Leveraging CTypes and SO objects on the python side is pretty easy overall. There are several downsides, which I'll detail, but this would not be something I shy away from in the future -- it's reasonable to use.
2. While this is something I wouldn't shy away from, I'm not sure I'd recommend it as a general solution. Frankly, it's a bit annoying. Each thing you want to pass needs to be wrapped in it's C equivalent package in python. Annotation of the types needs to be done. And, annoyingly, even though type annotations were provided, Python doesn't support typing of these SO functions directly -- each effectively needs a wrapper around it anyway. That's just as well, given how complex some of the encoding/decoding is needed here.
3. Speaking of C, even with this solution, you don't really get to avoid using C. Simple typedefs and imports are required on the Go side to smooth things over. And, even on the Python side, some understanding is required to properly use this once moving beyond (C's) primative types.
4. There's some mental overhead in bouncing between Go and Python. This can make maintaining both sides a little frustrating. As such, this technique is probably best applied only when the Go side is essentially solved, so that the python side can hand over stable APIs for Go to implement. This technique may not be appropriate for projects in rapid iteration.

Overall: Very interesting, very powerful. Probably useful in some corner cases, or when a team really needs to squeeze every last bit of performance out of a system -- or if a system needs absolute consistency between two different languages. But, in many cases, you might just be better writing everything in Go if you need speed.

### Notes

- You give up a lot when you begin to use CGo -- in particular, cross compilation, a bit of memory management and goroutines. In truth, this is more from reputation than this exploration. I acknowledge that there may be memory issues here, particularly around arrays and strings, however _I think_ python is doing the proper cleanup in these examples.
- CGo requires a C toolchain in order to actually work, so you can't completely get around not having a C environment set up.
- I stuck to a few basic tasks here just to get a feel for what it takes. In particular, I limited myself to primatives, strings, single-dimentional arrays and structs. Function pointers appear to be possible. Multi-dimentional arrays would probably be easy enough to figure out. Maps/dicts and similar probably require an encoding to do properly. Json is certainly possible, but depending on your data there might be better ways.
- This project uses go modules, but makes no imports, and it is not intended for consumption outside of locally developed projects -- as such, we keep a very simple module name -- `fun`.
- The miniprojects stick both the Go files and python files in the same directory. this is simply for convenience. In a regular project, I'd expect it'd make more sense to separate them.

### References

- [C? Go? Cgo!](https://go.dev/blog/cgo)
- [Go Wiki: cgo](https://go.dev/wiki/cgo)
- [The cost and complexity of Cgo](https://www.cockroachlabs.com/blog/the-cost-and-complexity-of-cgo/)
- [Python ctypes](https://docs.python.org/3/library/ctypes.html)
- Several queries to google (and thus gemini indirectly) to solve a few debugging issues.

Goals:

- Understand how to load "foreign code" (.so / .dll files)
- Create a simple SO in Go to verify it works in theory
  - [x] [go part](./basic/go_so/main.go); [python part](./basic/py_ctypes/main.py)
- Create an SO in a few different languages -- maybe Oliver can do one for rust?
  - [ ] Go
  - [ ] Rust
  - [ ] C/C++?
- [ ] Set up cross-env build (docker: xgo for mac-via-linux and go for linux-via-mac)
- [ ] Check on Features / Mappings
  - [ ] type compatibility
    - [x] [python/c list](https://docs.python.org/3/library/ctypes.html#fundamental-data-types)
    - [ ] Go int/int32 -> c.int
    - [ ] Go int64 ->
    - [ ] Go slice[int] ->
    - [ ] Go string ->
    - [ ] Go bool ->
    - [ ] Go (some object) -> 
    - [ ] Go map[string, string] ->
    - [ ] Go (no args) -> (Is this even useful? Maybe to fetch data?)
    - [ ] Go function -> [Maybe relevant](https://docs.python.org/3/library/ctypes.html#callback-functions); need to keep a reference to the function if using as a callback function
  - [ ] Unicode support?
  - [ ] Go pointer? -> Probably [this](https://docs.python.org/3/library/ctypes.html#fundamental-data-types)?
  - [ ] Go empty interface?
  - [ ] Go gofunc support?
  - [ ] python async or thread support?
  - [ ] Invoking dll in parallel? [Maybe relevant?](https://docs.python.org/3/library/ctypes.html#thread-safety-without-the-gil)
  - [ ] Python generator?
  - [ ] Saved state?
  - [ ] Python types for method calls?
  - [ ] how to communicate tuples
- Run speed test
  - [ ] Vs native python code (3.12 & 3.14)
  - [ ] Vs Go version
  - [ ] Vs Rust version
- Check vs C extension?
