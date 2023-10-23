import sys
import argparse
import re
from abc import abstractmethod
from typing import Callable, Dict, Union
from io import StringIO

from pushable import Pushable


class ParseException(Exception):
    def __init__(self, message):
        super().__init__(message)


class StrictCheckException(Exception):
    def __init__(self, message):
        super().__init__(message)


class Token:
    pass


class EndOfLine(Token):

    def __str__(self):
        return '<EOL>'

    def __repr__(self):
        return str(self)


class Number(Token):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f'<{self.value}>'

    def __repr__(self):
        return str(self)


class Symbol(Token):

    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name

    def __str__(self):
        return f'<{self._name}>'

    def __repr__(self):
        return str(self)


class String(Token):

    def __init__(self, token):
        self._token = token
        self._value = ''.join(String.stringify(token))

    def value(self):
        return self._value

    def __str__(self):
        return f'<{self._token}>'

    def __repr__(self):
        return str(self)
    
    @staticmethod
    def stringify(s):
        # Strip quotes and process escapes.
        n = 1
        L = len(s) - 1
        while n < L:
            ch = s[n]
            if ch == '\\':
                n += 1
                if n < L:
                    ch = s[n]
                    print( 'ESC' , ch)
                    if ch == 'n':
                        yield '\n'
                    elif ch == 'r':
                        yield '\r'
                    elif ch == 't':
                        yield '\t'
                    elif ch == '"':
                        yield '"'
                    elif ch == '\\':
                        yield '\\'
                    elif ch == 's':
                        yield ' '
                    else:
                        raise ParseException(f'Unknown escape sequence: {ch}')
                else:
                    raise ParseException(f'Unexpected end of string')
            else:
                yield ch
            n += 1


class StopLoopLang(Exception):
    pass


class Codelet:

    def __repr__(self):
        return str(self)

    def strictCheck(self):
        pass


class Expression(Codelet):
    @abstractmethod
    def evaluate(self, state):
        ...


class Statement(Codelet):
    @abstractmethod
    def execute(self, state):
        ...


class Constant(Expression):

    def __init__(self, value):
        self._value = value

    def evaluate(self, state):
        return self._value

    def __str__(self):
        return f'{self._value}'
    
    def value(self):
        return self._value


class Register(Expression):
    def __init__(self, name):
        self._name = name

    def evaluate(self, state):
        if self._name not in state:
            return 0
        return state[self._name]

    def __str__(self):
        return f'[{self._name}]'

    def __repr__(self):
        return str(self)
    
    def name(self):
        return self._name


class Error(Statement):

    def __init__(self, message=None) -> None:
        self._message = message

    def execute(self, state):
        if self._message:
            print( self._message, file=sys.stderr )
        raise StopLoopLang()

    def __str__(self):
        return 'ERROR'

    def strictCheck(self):
        pass


class Set(Statement):

    def __init__(self, x: str, y: Expression):
        self._name = x
        self._expr = y

    def execute(self, state):
        state[self._name] = self._expr.evaluate(state)

    def __str__(self):
        return f'SET {self._name} {self._expr}'

    def strictCheck(self):
        if isinstance(self._expr, Constant) and self._expr.value() == 0:
            return
        if isinstance(self._expr, Register):
            return
        if isinstance(self._expr, Add):
            self._expr.strictCheckArithOp(self._name)
            return
        raise StrictCheckException(f'Cannot set {self._name} to {self._expr}')


class ArithOp(Expression):

    def __init__(self, x, y):
        self._lhs = x
        self._rhs = y

    @abstractmethod
    def name(self):
        ...

    def __str__(self):
        return f'{self.name()} {self._lhs} {self._rhs}'

    def strictCheckArithOp(self, name):
        if isinstance(self._lhs, Register) and self._lhs.name() == name:
            if isinstance(self._rhs, Constant) and self._rhs.value() == 1:
                return
        raise StrictCheckException(f'Cannot {self.name()} {self._lhs} to {self._rhs}')


class Add(ArithOp):

    def name(self):
        return 'ADD'

    def evaluate(self, state):
        lhs = self._lhs.evaluate(state)
        rhs = self._rhs.evaluate(state)
        return lhs + rhs


class Mul(ArithOp):

    def name(self):
        return 'MUL'

    def evaluate(self, state):
        lhs = self._lhs.evaluate(state)
        rhs = self._rhs.evaluate(state)
        return lhs * rhs


class Sub(ArithOp):

    def name(self):
        return 'SUB'

    def evaluate(self, state):
        lhs = self._lhs.evaluate(state)
        rhs = self._rhs.evaluate(state)
        n = lhs - rhs
        return n if n >= 0 else 0


class Loop(Statement):

    def __init__(self, x: Expression, body: Statement):
        self._count = x
        self._body = body

    def execute(self, state):
        count = self._count.evaluate(state)
        for _ in range(0, count):
            self._body.execute(state)

    def __str__(self):
        return f'LOOP {self._count}: {self._body}'

    def strictCheck(self):
        if isinstance(self._count, Register):
            return
        self._body.strictCheck()


class Body(Statement):

    def __init__(self, instructions):
        self._instructions = instructions

    def execute(self, state):
        for instruction in self._instructions:
            instruction.execute(state)

    def __str__(self):
        return f'BODY: {self._instructions}'

    def strictCheck(self):
        for instruction in self._instructions:
            instruction.strictCheck()


class PostfixOptions:

    def __init__(self, prec, parse, constructor):
        self._prec = prec
        self._parse = parse
        self._constructor = constructor

    @property
    def prec(self):
        return self._prec

    @property
    def parse(self):
        return self._parse

    @property
    def constructor(self):
        return self._constructor


PrefixParsers: Dict[str, Union[Callable, None]] = {}
PostfixParsers: Dict[str, PostfixOptions] = {}


class Parser:

    def __init__(self, tokens, *, extended, plus):
        self._tokens: Pushable = Pushable( tokens )
        self._prefix_parsers = PrefixParsers.copy()
        self._postfix_parsers = PostfixParsers.copy()
        if plus:
            self._prefix_parsers['ERROR'] = errorPrefixParser
        if extended:
            self._prefix_parsers['('] = parenthesisPrefixParser
            self._prefix_parsers[')'] = None
            self._postfix_parsers['*'] = PostfixOptions(2, infixParser, Mul)
            self._postfix_parsers['-'] = PostfixOptions(1, infixParser, Sub)

    def checkComplete(self):
        if bool(self._tokens):
            raise ParseException(f'Unexpected tokens: {self._tokens.peek()}')
        
    def tryReadString(self):
        if self._tokens:
            token = self._tokens.peek()
            if isinstance(token, String):
                self._tokens.pop()
                return token.value()
            else:
                return None

    def mustReadToken(self, expected):
        # print('mustReadToken', expected)
        if self._tokens:
            token = self._tokens.pop()
            # print('mustReadToken', expected, token)
            if isinstance(token, Symbol) and token.name() == expected:
                return
        raise ParseException(f'Expected {expected} but got {token}')

    def mustReadEndOfLine(self):
        token = self._tokens.pop()
        if not isinstance(token, EndOfLine):
            raise ParseException(f'Expected end of line but got {token}')

    def readPrimaryExpression(self) -> Expression:
        # read constant or register.
        token = self._tokens.pop()
        # print('token', token)
        if isinstance(token, Number):
            return Constant(token.value)
        elif isinstance(token, Symbol):
            name = token.name()
            if name in self._prefix_parsers:
                mini_parser = self._prefix_parsers[name]
                if not mini_parser:
                    raise ParseException(f'Unexpected token at start of expression: {token}')
                return mini_parser(self, name)
            else:
                return Register(name)
        else:
            raise ParseException(f'Unexpected token at start of expression: {token}')

    def readExpression(self, prec) -> Expression:
        lhs = self.readPrimaryExpression()
        while True:
            token = self._tokens.peek()
            if not isinstance(token, Symbol):
                break
            name = token.name()
            if name not in self._postfix_parsers:
                break
            postfix_parser = self._postfix_parsers[name]
            if postfix_parser.prec < prec:
                break
            self._tokens.pop()
            lhs = (postfix_parser.parse)(self, postfix_parser.prec + 1, lhs, postfix_parser.constructor)
        return lhs

    def tryReadStatement(self) -> Union[Statement, None]:
        if not self._tokens:
            return None
        token = self._tokens.peek()
        if isinstance(token, Number):
            raise ParseException(f'Unexpected token at start of statement: {token}')
        if isinstance(token, Symbol):
            name = token.name()
            if name in self._prefix_parsers:
                mini_parser = self._prefix_parsers[name]
                if not mini_parser:
                    return None
                self._tokens.pop()
                return mini_parser(self, name)
            else:
                self._tokens.pop()
                self.mustReadToken('=')
                expr = self.readExpression(0)
                self.mustReadEndOfLine()
                return Set(name, expr)
        elif isinstance(token, EndOfLine):
            self._tokens.pop()
            return None
        else:
            raise ParseException(f'Unexpected token at start of statement: {token}')

    def readStatements(self) -> Statement:
        statements = []
        while True:
            statement = self.tryReadStatement()
            if statement is None:
                break
            statements.append(statement)
        return Body(statements)


def errorPrefixParser(parser: 'Parser', name: str):
    msg = parser.tryReadString()
    parser.mustReadEndOfLine()
    return Error(message=msg)

def loopPrefixParser(parser: 'Parser', name: str):
    x = parser.readExpression(0)
    parser.mustReadEndOfLine()
    body = []
    while True:
        statement = parser.tryReadStatement()
        if statement is None:
            break
        body.append(statement)
    # print('ALL', list(parser._tokens))
    parser.mustReadToken('END')
    parser.mustReadEndOfLine()
    return Loop(x, Body(body))

def parenthesisPrefixParser(parser: 'Parser', name: str):
    expr = parser.readExpression(0)
    parser.mustReadToken(')')
    return expr

def infixParser(parser, prec, lhs, constructor):
    rhs = parser.readExpression(prec)
    return constructor(lhs, rhs)

# Punctuation.
PrefixParsers['='] = None
PrefixParsers['END'] = None

# Prefix codelets.
PrefixParsers['LOOP'] = loopPrefixParser

# Postfix codelets.
PostfixParsers['+'] = PostfixOptions(1, infixParser, Add)


SCANNER = re.Scanner([
    (r"[0-9]+",             lambda scanner,token:Number(int(token))),
    (r"[a-zA-Z_][\w_]*",    lambda scanner,token:Symbol(token)),
    (r"[-=+*]+",            lambda scanner,token:Symbol(token)),
    (r"[()]",               lambda scanner,token:Symbol(token)),
    (r'''"([^"]|\")*"''',   lambda scanner,token:String(token)),
    (r';',                  lambda scanner,token:EndOfLine()),
    (r"\s+",                None),  # None == skip token.
    (r"#.*",                None),  # None == skip token.
])

def tokenise(line):
    results, remainder=SCANNER.scan(line)
    if remainder:
        raise ParseException(f'Unexpected text at the end of line: {remainder}')
    someTokens = False
    for tok in results:
        if tok:
            someTokens = True
            yield tok
    if someTokens:
        yield EndOfLine()

def getTokens(file):
    for line in file:
        yield from tokenise(line)

def execute(file, state, *, sugar=False, enhanced=False):
    initialcode = Parser(getTokens(file), extended=sugar, plus=enhanced)
    icode = initialcode.readStatements()
    initialcode.checkComplete()
    if not sugar:
        icode.strictCheck()
    icode.execute(state)

def main():
    argsp = argparse.ArgumentParser()
    argsp.add_argument('-f', '--file', type=argparse.FileType('r'), default=sys.stdin, help='LOOP code')
    argsp.add_argument('-S', '--sugar', action='store_true', help='enable syntactic sugar')
    argsp.add_argument('-N', '--enhanced', action='store_true', help='enable ERROR enhancement')
    argsp.add_argument('-e', '--execute', type=str, default=None, help='Semi-colon separated initial statements to execute')
    argsp.add_argument('-p', '--print', type=str, default=None, help='Comma-separated list of registers to print')
    args = argsp.parse_args()

    state: Dict[str, int] = {}
    try:
        if args.execute is not None:
            execute(StringIO(args.execute), state, sugar=args.sugar, enhanced=args.enhanced)
        execute(args.file, state, sugar=args.sugar, enhanced=args.enhanced)
        for a in args.print.split(',') if args.print else state.keys():
            print(a, '=', state[a])
    except StopLoopLang:
        sys.exit(1)

if __name__ == "__main__":
    main()
