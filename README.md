# loop-lang

This is an implementation of the LOOP programming language, loosely based on the 
[1967 paper](https://dl.acm.org/doi/pdf/10.1145/800196.806014). LOOP is 
summarised on Wikipedia [here](https://en.wikipedia.org/wiki/LOOP_(programming_language)).

This is not a serious implementation but a quick hack to test out some ideas
of what happens when we add some features to the language. 

## Command-line options

```
% python3 looplang.py --help
usage: looplang.py [-h] [-f FILE] [-x]

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  LOOP code to be executed
  -x, --extended        enable eXtended LOOP syntax
  -p, --plus            enable LOOP+ extensions
```

### Example

To run the interpreter on a file `foo.loop`, run:
```bash
python3 looplang.py foo.loop
```
When the interpreter stops it prints out the values of the registers.

## Strict mode

By default, the interpreter runs in strict mode, which means that it only uses
the syntax from the original paper plus comments. The full EBNF syntax is as 
follows:

```
program ::= statement*
statement ::= initialise | increment | assign | loop
initialise ::= register '=' '0'
increment ::= register '=' register '+' '1'
assign ::= register '=' register
loop ::= 'LOOP' register statement* 'END'
```

Register names must start with a letter and can contain letters, digits and 
underscores. And they may be prefixed with any number of underscores. For 
example, `x`, `_x` and `__x` are all valid register names but `1x` is not.

In this initial implementation, each instruction must be on a separate line.
Any line starting with a '#' is treated as a comment and is ignored.

## Extended syntax mode, -x

Not implemented yet.

Harmless extensions to LOOP are enabled through the `-x` flag. These are
harmless in the sense that they are syntactic sugar that could be expanded into 
equivalent strict LOOP code. However the interpreter is free to implement them
more efficiently.


## LOOP+ mode, -p

Not implemented yet.

This mode adds extensions to LOOP that change the semantics of the language.
