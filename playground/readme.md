# Playground

The playground is mostly a testing ground. This page attempts to document each of these findings, but the project itself is interesting to review.

As a reminder, this was done with python 3.14 and Go 1.27; based on some casual browsing, I suspect that older versions of Go might require a few adjustments to get these examples to work.

## TODOs

If I keep exploring, I'll update the following

- [ ] Pass Multi-dimentional data
- [ ] Pass Maps/Dicts
- [ ] Pass function pointers (to/from)
- [ ] Can we pass receiver functions?
- [ ] How do we support multiple returns?
- [ ] Goroutines
- [ ] Python Async/await

## Basics

### Go

Go is a bit picky about how to do the export process properly. It also provides a few mechanisms to make this process easier, but it's still picky. Here's the important bits:

- Exporting functions
  - to export any function, add a comment above any function: `//export FunctionName`. You can also provide normal go comments, but those don't seem to be exported, unsurprisingly. Note that it must be `//export` -- spacing will cause problems. If you forget the annotation or make a mistake with it, then you'll see the error: `AttributeError: lib.so: undefined symbol: FunctionName`
- Building an SO (or Dylib or DLL -- all the same, depending on your OS).
  - Minimally, this command: `go build -o lib.so -buildmode=c-shared main.go`
  - In general, Linux and Mac use the extention `.so`, Windows uses `.dll`, and Mac _also_ uses `dylib`.
  - Only builds for the current OS by default. Theoretically possible to compile for other OSes, but that's well beyond this project.
- Creating a preamble
  - The preamble is placed above the import for C -- "usually", this is done as such:
  
  ```go
  package main

  /*
  // preamble goes here
  */
  import "C"
  ```

  - The preamble can include lots. Typically you'll need `#includes` to get specific functionality from C, such as `<stdlib.h>`.
  - You can also supply defintions you need here. This could be C functionality (not super sure why you'd need that?), or C definitions, like structs. [main.go](./main.go) has what I think is a fairly typical example.
- Other rules per my reading:
  - main needs to be empty
  - It's important to know that when you create a CString (or otherwise call malloc), Go creates memory, but does not clean it up. If Go uses the data and does not return it to the caller, then Go is responsible for cleaning up the memory. If the data is returned, then the calling application is responsible for the memory -- this is very similar (conceptually) to borrow mechanics from Rust.
- In general, once you adopt CGo, your Go application is essentially two portions: whatever is wholy Go, which behaves like a regular Go application. The other bit is the C portion, which you can exist in without ever stepping into Go, but that adds problems as the types usually don't line up. As with Python, you tend to need to move into the Go world when called, and then back to the C world when you want to return. Any translation like that will have a cost.

### Python

Python's [ctypes documentation](https://docs.python.org/3/library/ctypes.html) is actually pretty good, but dense. 

- Python needs special typing and translation to properly marshal the python data into a C-compatible shape. See [Primative Alignment](#primative-alignment) below to understand the datatype translation.
- When calling foreign functions, Python, similarly requires providing types for the foreign function -- the table below indicates these types, but each type needs to be coded like such:
  - `argtypes` is a list of each parameter. It defaults to an empty list
  - `restype` is a single value for what the function returns. It defaults to None
  - Combined, these look like such: `lib.Add.argtypes = [ctypes.c_int, ctypes.c_int]; lib.Add.restype = ctypes.c_int`
  - Frequently, python data will need to be _copied_ into a container type -- essentially the marshaling step. As such, depending on the action, you may need to update the old type or return a new data structure. likewise, this means the memory impact of a single data structure can be felt 2 or 3 times within the python side -- the foreign side may also have its own representation as well. If you want to minimize this impact, you may need to deal explicitly with ctypes data and containers.
- Pay attention to how Python does garbage collection -- if the type you create is garbaged collected before the result is complete, then the actual result is likely nonsense, and depending on the exact timing, this could even result in an exception or crash

### Primative (&str) Alignment

Python's integer implementation allows for integers of arbitrary size. Go doesn't support this, so be aware of how big your numbers will get so that you can choose the proper type -- also, prefer a sized integer (like int_32) over plain int. Use `int` when go requires something that's sized depending on the system.

| Python datatype | Go's Name | Python's ctypes name | Notes                                             |
| --------------- | --------- | -------------------- | ------------------------------------------------- |
| int             | int       | c_int                | size is OS dependent                              |
| int             | int8      | c_int8               | (guess)                                           |
| int             | int16     | c_int16              | (guess)                                           |
| int             | int32     | c_int32              |                                                   |
| int             | int64     | c_int64              | (guess)                                           |
| float           | float32   | c_float              | (guess)                                           |
| float           | float64   | c_double             |                                                   |
| str (encoded)   | *C.char   | ctypes.c_char_p      | (after encoding to `utf-8`);terminates after `\0` |

### Strings with null characters

You'll want to treat this as a slice instead. See the slice notes below.

### Slices / Arrays

Both sides need to have a pointer and a length to understand the size of the data. On the Go side, the quick process results in a slice that points to the same memory that python created.

Go:

```go
func Decode(head *int32, count int) {
    // for reading -- head is the first element, count is the number of total elements
    aSlice := unsafe.Slice(head, count)
}
```

Python:

```py
def encode(l: list[int]) -> Array[ctypes.c_int32]:
    c_arr_container = (ctypes.c_int32 * len(l))  # create a container for the data
    c_arr = c_arr_container(*l)  # fill the array
    return c_arr

# note that c_arr is a C array, not a Python list. To turn this back into a python list, you'll want to copy the data.
# easiest way is with `new_list = c_arr[:]`
```

- Arrays of Arrays (of a consistent size) can be thought of as one long array. Likely, providing 2 sizes (rows and columns), or more if there are more dimensions, will make this process easiest.
- It's easier to simply mutate the data given rather than to create a copy of the data. If the Go call _does_ mutate the data, then note that the C array will be the mutated item, not the c list.
- If you need to take the C Array and turn it back into a list, the easiest way is to copy it by using `c_arr[:]`
- If you want Go to generate data, then it may be easier to have python pass a pointer to the location of the result, rather than having Go return a new slice.

### Structs

Structures need to be properly represented on both the sending side and receiving side. In the Go world, you'd either want to import the header file in the preamble, or define a matching struct in the preamble. The struct definition would need to be _in c_. (If you're in VSCode, using the extension, after creating the type, you can run "regenerate cgo definitions" to clear up any syntax errors). A similar action needs to be done on the Python side, by creating an object that inherits from `ctypes.Structure`:

```go
/*
typedef struct {
    int32_t x_coord;
    int32_t y_coord;
} Point;
*/
import "C"

func DoThing(myPoint *C.Point) {
    // myPoint is now basically a regular go structure, but still with a C representation
}
```

```py
import ctypes

class Point(ctypes.Structure):
    _fields_ = [
        ("x_coord", ctypes.c_int32),
        ("y_coord", ctypes.c_int32),
    ]

lib = ctypes.CDLL("lib.so")
lib.DoThing.argtypes = [ctypes.POINTER(Point)]

#... when ready to use....
x = 1
y = 2
c_point = Point(x, y)
lib.DoThing(c_point)
```

- Arrays of structs are still represented with a single pointer.

## Python: Creating good interfaces to the Go code

One of the obnoxious parts of dealing with FFI calls is the marshaling of data into and out of a C format. In addition, Python returns the values as Anys, which can be misleading to use. As such, it may be desirable to solve both of these issues with a wrapping function. This provides a possible way to do this:

```py
class FFI:  # Define a container -- here we opt to contain all of the functionality.
    def __init__(self, lib: ctypes.CLL):
        self.lib = lib
    
    def caps(self, s: str) -> str:  # function call is annotated with types to keep the typing sane for callers
        # add some documentation so callers know what this is doing
        """caps takes a string, and converts the string to all UPPERCASE"""
        # Once inside, we do all of the normal marshaling / encoding + decoding
        result: bytes = self.lib.caps(s.encode('utf-8'))
        return result.decode('utf-8')


def build_ffi(path_to_so) -> FFI
    lib = ctypes.CDLL(path_to_so)
    lib.caps.argtypes = [ctypes.c_char_p]
    lib.caps.restype = ctypes.c_char_p

    return FFI(lib)

ffi = build_ffi("...")
ffi.caps("Hello, World!") == "HELLO, WORLD!"  # Now, usage of caps is more like what you'd expect from a traditional python function
```