import argparse
import re
from abc import abstractmethod

class Token:
    def __init__(self, type, *value):
        self.type = type
        self.value = value

    def __str__(self):
        if self.value:
            return f'{self.type}{self.value}'
        else:
            return f'{self.type}'

    def __repr__(self):
        return str(self)


class Instruction:
    @abstractmethod
    def execute(self, state):
        ...

class Zero(Instruction):
    def __init__(self, x):
        self.x = x

    def execute(self, state):
        state[self.x] = 0

    def __str__(self):
        return f'ZERO {self.x}'
    
class Set(Instruction):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def execute(self, state):
        state[self.x] = state[self.y]

    def __str__(self):
        return f'SET {self.x} {self.y}'
    
class Inc(Instruction):
    def __init__(self, x):
        self.x = x

    def execute(self, state):
        state[self.x] += 1

    def __str__(self):
        return f'INC {self.x}'

class Loop(Instruction):
    def __init__(self, x, body):
        self._count = x
        self._body = body

    def execute(self, state):
        for i in range(state[self._count]):
            self._body.execute(state)

    def __str__(self):
        return f'LOOP {self._count}: {self._body}'
    
class Body(Instruction):
    def __init__(self, instructions):
        self._instructions = instructions

    def execute(self, state):
        for instruction in self._instructions:
            instruction.execute(state)

    def __str__(self):
        return f'BODY: {self._instructions}'

def parseLine(line):
    m = re.match(r'''(\w+) *= *0 *$''', line)
    if m:
        x = m.group(1)
        return Token('ZERO', x)

    m = re.match(r'''(\w+) *= (\w+) *$''', line)
    if m:
        x = m.group(1)
        y = m.group(2)
        return Token('SET', x, y)
    
    m = re.match(r'''(\w+) *= (\w+) *\+ *1 *$''', line)
    if m:
        x = m.group(1)
        y = m.group(2)
        if x == y:
            return Token('INC', x)
        else:
            raise Exception(f'Invalid increment: variables differ: {x} {y}')

    m = re.match(r'''LOOP[ ]+(\w+)[ ]*$''', line)
    if m:
        x = m.group(1)
        return Token('LOOP', x)
    
    if line == 'END':
        return Token('END')

    return line

def getTokens(file):
    for line in file:
        yield parseLine(line.strip())

def readLoopProgram(tokens):
    instructions = []
    for token in tokens:
        if token.type == 'ZERO':
            instructions.append(Zero(token.value[0]))
        elif token.type == 'SET':
            instructions.append(Set(token.value[0], token.value[1]))
        elif token.type == 'INC':
            instructions.append(Inc(token.value[0]))
        elif token.type == 'LOOP':
            instructions.append(Loop(token.value[0], readLoopProgram(tokens)))
        elif token.type == 'END':
            return Body(instructions)
        else:
            raise Exception(f'Invalid token: {token}')
    return Body(instructions)

def startLoopLang():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=argparse.FileType('r'), help='LOOP code')
    args = parser.parse_args()
    program = readLoopProgram(getTokens(args.file))
    state = {}
    program.execute(state)
    print(state)


if __name__ == "__main__":
    startLoopLang()
