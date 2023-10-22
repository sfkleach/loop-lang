# loop-lang

This is an implementation of the LOOP programming language, loosely based on the 
[1967 paper](https://dl.acm.org/doi/pdf/10.1145/800196.806014). LOOP is  summarised on Wikipedia [here](https://en.wikipedia.org/wiki/LOOP_(programming_language)).

This is a simple implementation to test out some ideas of what happens when  we add some features to the language. We have two sets of extensions:

- *-s --sugar*: this option allows for normal arithmetic expressions on
  the right hand side of assignments and the count for loops. These options
  are syntactic sugar in principle, although the interpreter does directly
  implement add and multiply rather than expand them into their much less
  efficient LOOP code. In other words, it is still a primitive recursive
  programming language.

- *-n --enhanced*: this option adds a single new 'instruction' called ERROR.
  When ERROR is executed, execution immediately stops and the interpreter
  reports that an error was encountered.

## How to use the interpreter

The LOOP interpreter is made available as a single file: `looplang.pyz`. This is a bunch of Python code stuff into [a zip archive that the Python interpreter understands](https://docs.python.org/3/library/zipapp.html).

```
% python3 looplang.pyz --help
usage: looplang.py [-h] [-f FILE] [-x]

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  LOOP code to be executed
  -S, --sugar           enable syntactic sugar
  -N, --enhanced        enable ERROR enhancement
```

### Example

LOOP programs consist of simple assignments to arbitarily named variables called  'registers' and the eponymous `LOOP` construct. The assignments must fit one of three exact patterns:

```
x = 0       # Assignment to zero (and only zero)
y = x       # Assignment from another register
y = y + 1   # Increment of a register (same register on both sides)
```

The only control construct is the `LOOP` which fits the following pattern n.b.  line breaks are significant, although indentation is ignored.

```
LOOP y
  x = x + 1
END
```

Putting this sequence together we might have the following simple LOOP program (see examples/simple.loop):
```
  x = 0
  y = x
  y = y + 1
  LOOP y
    x = x + 1
  END
```

To run the interpreter on a file `foo.loop`, run:
```bash
% python3 looplang.pyz -f examples/simple.loop
{'x': 1, 'y': 1}
```
When the interpreter stops it prints out the values of the registers.

## Strict mode

By default, the interpreter runs in strict mode, which means that it only uses the syntax from the original paper plus comments. The EBNF syntax (ignoring comments) is as follows:

```
program ::= statement*
statement ::= initialise | increment | assign | loop
initialise ::= register '=' '0'
increment ::= register '=' register '+' '1'
assign ::= register '=' register
loop ::= 'LOOP' register statement* 'END'
```

Register names must start with a letter and can contain letters, digits and  underscores. And they may be prefixed with any number of underscores. For  example, `x`, `_x` and `__x` are all valid register names but `1x` is not.

In this initial implementation, each instruction must be on a separate line. Any line starting with a '#' is treated as a comment and is ignored.

## Sugared mode, -S

Harmless extensions to LOOP are enabled through the `-S` flag. These are
harmless in the sense that they are syntactic sugar that could be expanded into  equivalent strict LOOP code. However the interpreter is free to implement them more efficiently.

Sugared mode allows assignment to use three arithmetic operators: `+`, `*` and  `-`. Note that if subtraction would generate a negative number then zero is returned instead. The usual operator precedence rules apply (`*` binds tighter than `+` or `-`) and ordering can be modified by parentheses.

It also allows `LOOP`s to iterate over the value of an arithmetic expression e.g.
```
LOOP x * y
  z = z + 1
END
```

The EBNF grammar looks like this:
```
program ::= statement*
statement ::= assignment | loop
assign ::= register '=' expression LINEBREAK
loop ::= 'LOOP' expression LINEBREAK statement* 'END' LINEBREAK
expression ::= integer
    | register
    | expression ( '+' | '-' | '*' ) expression
    | '(' expression ')'
```


## Enhanced mode, -N

This mode adds the ERROR instruction to LOOP. It is compatible with the `--sugar` option. When an ERROR is encountered, the interpreter will  immediately stop and report an error:

Here is the simplest enhanced mode program :) 
```
ERROR
```

And this is what happens when you try running it:
```bash
% python3 looplang.pyz -N -f examples/error.loop
++ Out of Cheese Error ++ Redo From Start ++
```
