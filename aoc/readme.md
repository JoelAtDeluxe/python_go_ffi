# Advent of Code 2016, day 12 solution, made hard

This side of the project focuses on the speed implications of adopting an FFI solution. The logic for both the python portion and go portion are largely the same from my solution from much earlier. Those solutions can be found here:

- [Go Solution](https://github.com/JoelAtDeluxe/AdventOfCode2016/tree/master/12)
- [Python solution](https://github.com/JoelAtDeluxe/AdventOfCode2016/tree/master/12_python3)

## About the problem

This problem comes from [adventofcode.com](https://adventofcode.com/2016/day/12), from the 2016, day 12 set. This problem focuses on trying to compute the output of a computer, given a very small instruction set. Advent of Code lays out the details of this quite well, so I'll leave it as an exercise for the reader to... well, do more reading. Imporantly, it's worth talking through my solution, and why I chose this problem as an example.

The nieve approach combines the parsing of the rules in conjunction with the processing. This has a few negative impacts: repeated string comparisons, repeated conditionals, multiple map lookups, and overall, just a huge speed impact. My original solution, which seems to be lost to time, used regular expressions for string parsing. As an aside, I realized with this project just how slow regular expression are, and have kind of avoided them ever since.

This solution instead separates the problem into two stages: a compilation stage, where I interpret each action as a series of inputs, and generally try to reduce strings into integers, and the execution phase, where we act on these integers directly. When compiling, I also differentiated between copying/jumping between a value vs a register. This allowed me to ignore the register names, and instead simply point to a pre-allocated section of memory (i.e. a specific index in a slice). These optimizations _dramatically_ speeds up the execution, which reduced this computation into the sub-second time.

Personally, when I was solving this, I was also quite interested with python and cython. So, I created a python solution to measure against, and the most basic cython version to time that as well. Unfortunately, I don't remember the cython timing, which would make a good counter point to this exploration. However, the python version was _exactly_ what I needed for this test. It was implemented to be functionally identical in procedure to what the Go version did, so it provided a nice comparison at the time -- and I got to re-use it again for this project.

Per Advent of Code requests, I am not posting my input files here -- though I made that mistake in the other project.

### More optimizations?

I'd be remiss if I didn't at least mention what, I think, is the intention of the problem: trying to solve the problem by parsing the commands as high level statements, and not as low level statements. This never dawned on me at the time, and I still struggle with this. However, a subset of instructions shows that this isn't super difficult:

```plain
inc a
dec b
jnz b -2
```

Here, we increment A, decrement B, and then check if B is 0 -- if it's _not_ 0, then we jump back to the `inc a` step. Looking at this a bit abstractly, what we really seem to be doing is to add the contents of B into A -- so these statements can be replaced with: `a += b; b = 0;`, which is a big improvement.

## The Go/Python split

These applications already have a nice bound built in since they share the same structure, and fundamentally the file loading and compilation step is trivially fast. The real burden comes in the evaluation step. As such, all that had to happen to test this was to simply reduce the Go version to the Evaluate function, with the proper typings (along with adding building, etc). Likewise, the Python version got to stay largely the same -- essentially, _only_ remove the evaluate solution, and replace it with a call to the Go version.

Timing, then, was broken down into the following sections:

- All-Go solution: _only_ the time to call the `evaluate` function
- All-Python solution: _only_ the time to call the `evaluate` function
- Hybrid solution:
  - copying the memory into a compatible C structure
  - copying the program instructions into a compatible c structure
  - calling Go's evaluate solution, which itself was burdened with:
    - interpretting the memory and program as slices (though no memory copy)
    - converting every c int32_t into a Go `int32`

This felt like a fair comparison, as the adoption of a Shared Object would have similar overheads, in addition to the loading of the SO itself, which typically can be amoritized over the entire run of an application.

## The result