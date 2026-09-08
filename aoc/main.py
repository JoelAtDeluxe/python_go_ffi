from time import time
import ctypes


INC_REG = 1
DEC_REG = 2
CPY_REG = 3
CPY_VAL = 4
JNZ_REG = 5
JNZ_VAL = 6
NULL_PARAM = 0

PROG_INST = tuple[int, int, int]

class ProgramInstruction(ctypes.Structure):
    _fields_ = [
        ('command', ctypes.c_int32),
        ('param1', ctypes.c_int32),
        ('param2', ctypes.c_int32),
    ]


def load_file(path: str) -> list[str]:
    lines = []
    with open(path, 'r') as fh:
        for line in fh:
            lines.append(line.strip())
    return lines


def load_lib(path: str) -> ctypes.CDLL:
    lib = ctypes.CDLL(path)

    lib.Evaluate.argtypes = [
        ctypes.POINTER(ctypes.c_int32), ctypes.c_int,  # memory
        ctypes.POINTER(ProgramInstruction), ctypes.c_int  # program
    ]
    lib.Evaluate.restype = None

    return lib


def main():
    instructions = load_file('input/input_part2.txt')
    lib = load_lib("./dist/lib.so")

    start = time()
    compiled_instructions, mem_map, memory = compile_program(instructions)
    duration = time() - start
    print(f"Compilation: {duration}!")


    start = time()
    cmem = (ctypes.c_int32 * len(memory))(*memory)
    prog = (ProgramInstruction * len(compiled_instructions))(*[ProgramInstruction(c, p1, p2) for c, p1, p2 in compiled_instructions])
    lib.Evaluate(cmem, len(cmem), prog, len(prog))

    duration = time() - start
    print(f"Value in register a: {cmem[mem_map.get('a')]}")
    print(f"Finished in: {duration}!")


def compile_program(program: list[str]) -> tuple[list[PROG_INST], dict[str, int], list[int]]:
    registers: list[int] = []
    reg_map: dict[str, int] = {}
    parse_instructions: list[PROG_INST] = []

    def get_reg_index(reg_name: str) -> int:
        val = reg_map.get(reg_name)
        if val is None:
            val = len(registers)
            reg_map[reg_name] = val
            registers.append(0)  # initialize registers
        return val

    for line in program:
        instruction = line.split(' ')
        action = instruction[0]
        if action == 'inc':
            register = get_reg_index(instruction[1])
            parse_instructions.append((INC_REG, register, NULL_PARAM))
        elif action == 'dec':
            register = get_reg_index(instruction[1])
            parse_instructions.append((DEC_REG, register, NULL_PARAM))
        elif action == 'cpy':
            frm = instruction[1]
            to_idx = get_reg_index(instruction[2])
            if is_num(frm):
                parse_instructions.append((CPY_VAL, int(frm), to_idx))
            else:
                parse_instructions.append((CPY_REG, get_reg_index(frm), to_idx))
        elif action == 'jnz':
            val = instruction[1]
            direction = int(instruction[2])
            if is_num(val):
                parse_instructions.append((JNZ_VAL, int(val), direction))
            else:
                parse_instructions.append((JNZ_REG, get_reg_index(val), direction))

    return parse_instructions, reg_map, registers


def is_num(val: str) -> bool:
    for c in val:
        if c not in '0123456789-':
            return False
    return True


if __name__ == "__main__":
    main()
