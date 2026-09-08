package main

/*
#include <stdlib.h>

typedef struct {
    int32_t x;
	int32_t y;
	int32_t z;
} Tri;

*/
import "C"

import (
	"math"
	"strings"
	"unsafe"
)

func main() {

}

// all exports must be explicitly "//export"
// doing frees requires including <stdlib.h> as part of your "preamble"; see above

// Double makes an integer twice as large
//
//export Double
func Double(i int32) int32 {
	return i * 2
}

//export StrLen
func StrLen(cstr *C.char) int {
	s := C.GoString(cstr)
	// fmt.Println("Input: ", s, "Calc_len:", len(s))
	return len(s)
}

//export TrimString
func TrimString(cstr *C.char) *C.char {
	s := C.GoString(cstr)
	trimmed := strings.TrimSpace(s)
	var result *C.char = C.CString(trimmed)
	return result
}

//export Sum
func Sum(cints *int32, itemCount int) int32 {
	ints := unsafe.Slice(cints, itemCount)
	var rtn int32 = 0
	for _, v := range ints {
		rtn += int32(v)
	}
	return rtn
}

//export DoubleAllMutate
func DoubleAllMutate(cints *int32, itemCount int) {
	ints := unsafe.Slice(cints, itemCount)

	for i := range ints {
		ints[i] = ints[i] * 2
	}
}

//export TriProduct
func TriProduct(tri *C.Tri) int32 {
	rtn := tri.x * tri.y * tri.z
	return int32(rtn)
}

//export TriDistance
func TriDistance(tris *C.Tri, itemCount int) float64 {
	triSlice := unsafe.Slice(tris, itemCount)
	if len(triSlice) != 2 { // This is silly -- you'd probably just pass two Tri's, but I wanted to vet out []struct
		return 0
	}
	t1, t2 := triSlice[0], triSlice[1]

	x := (t1.x - t2.x)
	y := (t1.y - t2.y)
	z := (t1.z - t2.z)
	distance := math.Sqrt(float64(x*x) + float64(y*y) + float64(z*z))

	return distance
}

// This needs some work -- we have three options:
// 1: Mutate the array -- that's DoubleAllMutate
// 2: Mutate a copy -- ask for more pointers, and fill up the pointed-to memory; not super sure how to best do this
// 3: Return a copy -- Go will need to create the memory via unsafe calls. (& maybe return a struct?)
// func DoubleAllCopy(cints *int32, itemCount int)  {
// 	ints := unsafe.Slice(cints, itemCount)
// 	rtn := make([]int32, itemCount)

// 	for i := range ints {
// 		rtn[i] = ints[i] * 2
// 	}
// 	C.malloc()
// 	return rtn
// }
