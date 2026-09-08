import ctypes


# Passing Structs: You need to model this on both sides for easiest consumption
# on the Python-side, inheriting from ctypes.Structure will make it a C-compatible structure
# on the Go side, you can place the C definition of the type in the preamble, and then reference it directly
# but, the actual mechanism for passing it needs to be a pointer
#
## Note: if passing arrays of Tri, you only need a single pointer. *Tri can be either 1 Tri or many Tris.
class Tri(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int32),
        ("y", ctypes.c_int32),
        ("z", ctypes.c_int32),
    ]


# CTypes functions _always_ return Any type; explictly annotate or wrap to get proper type checking around it;
# wrapping is a good idea if the values need to be encoded/decoded anyway.

def setup_lib(path: str) -> ctypes.CDLL:
    lib = ctypes.CDLL(path)
    lib.Double.argtypes = [ctypes.c_int32]  # could just use int, which is system dependent
    lib.Double.restype = ctypes.c_int32

    # c_char_p -> C's char* (not specifically unicode, null terminated)
    # c_wchar_p -> "wide" char*; unicode (seems each one is multi-byte?)
    # Looks like you typically want to use c_char_p and do python string encode ("".encode('utf-8'))

    lib.StrLen.argtypes = [ctypes.c_char_p]
    lib.StrLen.restype = ctypes.c_int

    lib.TrimString.argtypes = [ctypes.c_char_p]
    lib.TrimString.restype = ctypes.c_char_p  # Since we get back a char*, we need to free it -- does python do this for us?

    lib.Sum.argtypes = [ctypes.POINTER(ctypes.c_int32), ctypes.c_int]
    lib.Sum.restype = ctypes.c_int32

    lib.DoubleAllMutate.argtypes = [ctypes.POINTER(ctypes.c_int32), ctypes.c_int]  # mutates in place

    lib.TriProduct.argtypes = [ctypes.POINTER(Tri)]
    lib.TriProduct.restype = ctypes.c_int32

    lib.TriDistance.argtypes = [ctypes.POINTER(Tri), ctypes.c_int] # [ctypes.POINTER(ctypes.POINTER(Tri)), ctypes.c_int]
    lib.TriDistance.restype = ctypes.c_double

    return lib

# might not handle interrupts while in dll land

def test_double(lib: ctypes.CDLL):
    v = 10
    expected = v * 2
    actual = lib.Double(10)
    assert expected == actual
    print("Double: OK")


def test_strlen(lib: ctypes.CDLL):
    s = "A testing String"
    amt = lib.StrLen(s.encode('utf-8'))
    assert amt == len(s)
    print("StrLen: OK")


def test_trim(lib: ctypes.CDLL):
    s = "  abc  "
    expected = s.strip()
    rtn: bytes = lib.TrimString(s.encode('utf-8'))
    actual = rtn.decode('utf-8')
    assert expected == actual
    print("TrimString: OK")


def test_sum(lib: ctypes.CDLL):
    nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    c_nums = (ctypes.c_int * len(nums))(*nums)

    actual = lib.Sum(c_nums, len(c_nums))

    expected = sum(nums)
    assert expected == actual
    print("Sum: OK")


def test_double_mutate(lib: ctypes.CDLL):
    nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    expected = [2*v for v in nums]
    c_nums = (ctypes.c_int * len(nums))(*nums)

    lib.DoubleAllMutate(c_nums, len(c_nums))
    actual = c_nums[:]

    assert len(actual) == len(expected)
    for i in range(len(actual)):
        assert expected[i] == actual[i], f"didn't match(E:{expected[i]} ;; A:{actual[i]})"
    print("DoubleAllMutate: OK")


def test_tri_product(lib: ctypes.CDLL):
    tri = Tri(3, 4, 5)
    expected = tri.x * tri.y * tri.z
    actual = lib.TriProduct(tri)

    assert expected == actual
    print("TriProduct: OK")


def test_tri_distance(lib: ctypes.CDLL):
    import math
    tri1 = Tri(3, 4, 5)
    tri2 = Tri(13, 14, 15)
    tri_arr = (Tri * 2)(tri1, tri2)

    actual = lib.TriDistance(tri_arr, len(tri_arr))

    x = tri1.x - tri2.x
    y = tri1.y - tri2.y
    z = tri1.z - tri2.z
    expected = math.sqrt(x*x + y*y + z*z)

    assert expected == actual
    print("TriProduct: OK")


def main():
    lib = setup_lib("./dist/lib.so")

    test_double(lib)
    test_strlen(lib)
    test_trim(lib)
    test_sum(lib)
    test_double_mutate(lib)
    test_tri_product(lib)
    test_tri_distance(lib)


if __name__ == '__main__':
    main()