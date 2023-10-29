import looplang
import io
import pytest

def test_set_to_zero():
    program = io.StringIO("""x = 0""")
    state = {}
    looplang.execute(program, state, sugar=False, enhanced=False)
    assert state['x'] == 0

def test_set_to_99():
    program = io.StringIO("""x = 99""")
    state = {}
    looplang.execute(program, state, sugar=True, enhanced=False)
    assert 99 == state['x']

def test_example_strict():
    with open('examples/strict.loop', 'r') as program:
        state = {}
        looplang.execute(program, state, sugar=False, enhanced=False)
        assert 1 == state['x']
        assert 2 == state['y']

def test_example_strict():
    with open('examples/add1.loop', 'r') as program:
        state = {}
        looplang.execute(program, state, sugar=False, enhanced=False)
        assert 1 == state['x']

def test_example_sugared():
    with open('examples/sugared.loop', 'r') as program:
        state = {}
        looplang.execute(program, state, sugar=True, enhanced=False)
        assert 7 == state['xyz']

def test_example_sugared():
    with pytest.raises(looplang.StrictCheckException):
        with open('examples/sugared.loop', 'r') as program:
            state = {}
            looplang.execute(program, state, sugar=False, enhanced=False)
            assert 7 == state['xyz']

def test_example_simple():
    with open('examples/simple.loop', 'r') as program:
        state = {}
        looplang.execute(program, state, sugar=False, enhanced=False)
        assert 1 == state['x']
        assert 1 == state['y']

def test_example_error():
    with pytest.raises(looplang.StopLoopLang):
        with open('examples/error.loop', 'r') as program:
            state = {}
            looplang.execute(program, state, sugar=False, enhanced=True)

def test_example_error_inline_factorial():
    with open('examples/inline_factorial.loop', 'r') as program:
        state = dict(n = 5)
        looplang.execute(program, state, sugar=True, enhanced=False)
        assert 120 == state['r']

def test_example_error_factorial():
    with open('examples/factorial.loop', 'r') as program:
        state = {}
        looplang.execute(program, state, sugar=True, enhanced=False)
        assert 120 == state['f5']

def test_example_failed_recursion():
    with pytest.raises(looplang.ResolveException):
        with open('examples/failed_recursion.loop', 'r') as program:
            state = {}
            looplang.execute(program, state, sugar=True, enhanced=False)
