import py
from wordle import Constraint
import pytest


alphabet = frozenset(map(chr, range(97, 123)))
parse_parameters = [
    (
        "+s_a-s_s_y",
        frozenset([("s", 2)]),
        [
            frozenset({"s"}),
            alphabet - {"a", "y"},
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
        ],
    ),
    (
        "+s_a_s-s_y",
        frozenset([("s", 2)]),
        [
            frozenset({"s"}),
            alphabet - {"a", "y"},
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
        ],
    ),
    (
        "-s_a+s_s_y",
        frozenset([("s", 2)]),
        [
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
            frozenset({"s"}),
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
        ],
    ),
    (
        "-s_a_s+s_y",
        frozenset([("s", 2)]),
        [
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
            alphabet - {"a", "s", "y"},
            frozenset({"s"}),
            alphabet - {"a", "y"},
        ],
    ),
    (
        "_s_a+s-s_y",
        frozenset([("s", 2)]),
        [
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
            frozenset({"s"}),
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
        ],
    ),
    (
        "_s_a-s+s_y",
        frozenset([("s", 2)]),
        [
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
            alphabet - {"a", "s", "y"},
            frozenset({"s"}),
            alphabet - {"a", "y"},
        ],
    ),
]


@pytest.mark.parametrize(
    "input,at_least,allows",
    parse_parameters,
)
def test_parse_constraints(input, at_least, allows):
    c = Constraint.parse(input)
    assert c.at_least == at_least
    assert c.allows[0] == allows[0]
    assert c.allows[1] == allows[1]
    assert c.allows[2] == allows[2]
    assert c.allows[3] == allows[3]
    assert c.allows[4] == allows[4]


diff_parameters = [
    (
        "shire",
        "cross",
        frozenset([("s", 1), ("r", 1)]),
        [
            alphabet - {"o", "c"},
            alphabet - {"o", "c", "r"},
            alphabet - {"o", "c"},
            alphabet - {"o", "c", "s"},
            alphabet - {"o", "c", "s"},
        ],
    ),
    (
        "adage",
        "adiue",
        frozenset([("a", 1), ("d", 1), ("e", 1)]),
        [
            frozenset({"a"}),
            frozenset({"d"}),
            alphabet - {"i", "u"},
            alphabet - {"i", "u"},
            frozenset({"e"}),
        ],
    ),
]


@pytest.mark.parametrize(
    "input_a,input_b,at_least,allows",
    diff_parameters,
)
def test_gen_constraints(input_a, input_b, at_least, allows):
    c = Constraint.diff(input_a, input_b)
    assert c.at_least == at_least
    assert c.allows[0] == allows[0]
    assert c.allows[1] == allows[1]
    assert c.allows[2] == allows[2]
    assert c.allows[3] == allows[3]
    assert c.allows[4] == allows[4]


and_parameters = [
    (
        "-r-a_i_s_e",
        "_a_l+a-r-m",
        frozenset([("a", 1), ("r", 1), ("m", 1)]),
        [
            alphabet - {"a", "e", "i", "l", "s", "r"},
            alphabet - {"a", "e", "i", "l", "s"},
            frozenset({"a"}),
            alphabet - {"a", "e", "i", "l", "s", "r"},
            alphabet - {"a", "e", "i", "l", "m", "s"},
        ],
    )
]


@pytest.mark.parametrize("cons_a,cons_b,at_least,allows", and_parameters)
def test_and_constraints(cons_a, cons_b, at_least, allows):
    c = Constraint.parse(cons_a) & Constraint.parse(cons_b)
    assert c.at_least == at_least
    assert c.allows[0] == allows[0]
    assert c.allows[1] == allows[1]
    assert c.allows[2] == allows[2]
    assert c.allows[3] == allows[3]
    assert c.allows[4] == allows[4]
