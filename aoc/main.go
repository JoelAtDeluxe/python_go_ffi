package main

/*
#include <stdlib.h>

typedef struct {
    int32_t command;
	int32_t param1;
	int32_t param2;
} ProgramInstruction;

*/
import "C"

import (
	"unsafe"
)

const (
	IncReg = iota + 1
	DecReg
	CpyReg
	CpyVal
	JnzReg
	JnzVal
)


func main() {}

//export Evaluate
func Evaluate(cmem *int32, memSize int, instructions *C.ProgramInstruction, numInstructions int) {
	memory := unsafe.Slice(cmem, memSize)
	program := unsafe.Slice(instructions, numInstructions)

	pc := int32(0)
	progLen := int32(numInstructions)

	for pc < progLen {
		npc := pc + 1

		step := program[pc]
		// cmd := int32(step.command)
		switch int32(step.command) {
		case IncReg:
			memory[int32(step.param1)]++
		case DecReg:
			memory[int32(step.param1)]--
		case CpyReg:
			memory[int32(step.param2)] = memory[int32(step.param1)]
		case CpyVal:
			memory[int32(step.param2)] = int32(step.param1)
		case JnzVal:
			if int32(step.param1) != 0 {
				npc = pc + int32(step.param2)
			}
		case JnzReg:
			if memory[int32(step.param1)] != 0 {
				npc = pc + int32(step.param2)
			}
		}

		pc = npc
	}
}
