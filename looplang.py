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

class Init(Instruction):
    def __init__(self, x, k):
        self.x = x
        self._constant = k

    def execute(self, state):
        state[self.x] = self._constant

    def __str__(self):
        return f'INIT {self.x} {self._constant}'
    
class Set(Instruction):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def execute(self, state):
        try:
            state[self.x] = state[self.y]
        except KeyError:
            state[self.y] = 0
            state[self.x] = 0

    def __str__(self):
        return f'SET {self.x} {self.y}'
    
class Inc(Instruction):
    def __init__(self, x):
        self.x = x

    def execute(self, state):
        try:
            state[self.x] += 1
        except KeyError:
            state[self.x] = 1

    def __str__(self):
        return f'INC {self.x}'

class Loop(Instruction):
    def __init__(self, x, body):
        self._count = x
        self._body = body

    def execute(self, state):
        if self._count not in state:
            state[self._count] = 0
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

def parseLine(line, *, extended, plus):
    m = re.match(r'''(_*[a-zA-Z][_\w]*) *= *([\d]+)$''', line)
    if m:
        try:
            x = m.group(1)
            k = int(m.group(2))
            if not extended and k:
                raise Exception(f'Extended syntax only (hint: did you mean -x?): {line}')
            return Token('INIT', x, k)
        except ValueError:
            raise Exception(f'Invalid initialisation: {line}')

    m = re.match(r'''(_*[a-zA-Z][_\w]*) *= (_*[a-zA-Z][_\w]*)$''', line)
    if m:
        x = m.group(1)
        y = m.group(2)
        return Token('SET', x, y)
    
    m = re.match(r'''(_*[a-zA-Z][_\w]*) *= (_*[a-zA-Z][_\w]*) *\+ *1$''', line)
    if m:
        x = m.group(1)
        y = m.group(2)
        if x == y:
            return Token('INC', x)
        else:
            raise Exception(f'Invalid increment: variables differ: {x} {y}')

    m = re.match(r'''LOOP[ ]+(_*[a-zA-Z][_\w]*)$''', line)
    if m:
        x = m.group(1)
        return Token('LOOP', x)
    
    if line == 'END':
        return Token('END')

    raise Exception(f'Invalid line: {line}')

def getTokens(file, extended, plus):
    for line in file:
        line = line.strip()
        if line and line[0] == '#':
            continue
        yield parseLine(line, extended=extended, plus=plus)

def readLoopProgram(tokens):
    instructions = []
    for token in tokens:
        if token.type == 'INIT':
            instructions.append(Init(token.value[0], token.value[1]))
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
    parser.add_argument('-f', '--file', type=argparse.FileType('r'), help='LOOP code')
    parser.add_argument('-x', '--extended', action='store_true', help='enable syntactic sugar')
    parser.add_argument('-p', '--plus', action='store_true', help='enable LOOP+ extensions')
    args = parser.parse_args()
    program = readLoopProgram(getTokens(args.file, args.extended, args.plus))
    state = {}
    program.execute(state)
    print(state)


if __name__ == "__main__":
    startLoopLang()
