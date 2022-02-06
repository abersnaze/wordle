#!python3

import fileinput
import sys
from collections import Counter
from enum import Enum
from multiprocessing import Pool
from typing import Dict, List, Set


class Mode(Enum):
    absent = "_"
    present = "-"
    correct = "+"


class Constraint:
    # how many of each letter must there be
    at_least: Dict[str, int]
    # what letters are allowed in each of the 5 positions
    allows: List[Set[str]]
    # what words were used so far
    used: Set[str]

    def __init__(
        self,
        at_least=None,
        allows=None,
        used=None,
    ) -> None:
        self.at_least = at_least if at_least else {}
        # allow a to z in any possion
        self.allows = (
            allows
            if allows
            else [
                set(map(chr, range(97, 123))),
                set(map(chr, range(97, 123))),
                set(map(chr, range(97, 123))),
                set(map(chr, range(97, 123))),
                set(map(chr, range(97, 123))),
            ]
        )
        self.used = used if used else set()

    @staticmethod
    def parse(line: str) -> None:
        """
        parse the result of a guess for a five letter word.
        each letter prefixed with:
        _ == absent letter
        - == present but in the wrong place
        + == correct letter in the right place.
        """
        out = Constraint()
        out.used.add("".join(map(line.__getitem__, range(1, 10, 2))))

        # parse the 10 characters into 5 tuples.
        clues = []
        for pos in range(0, 10, 2):
            mode = Mode(line[pos])
            ltr = line[pos + 1]
            clues.append((pos // 2, mode, ltr))

        # discard the absent letters
        for pos, mode, ltr in filter(lambda x: x[1] == Mode.absent, clues):
            for allow in out.allows:
                allow.discard(ltr)
        # add back the present letters
        for pos, mode, ltr in filter(lambda x: x[1] == Mode.present, clues):
            for allow in out.allows:
                allow.add(ltr)
            out.allows[pos].discard(ltr)
            out.at_least[ltr] = out.at_least.get(ltr, 0) + 1
        # discard the present letters from where they were wrong
        for pos, mode, ltr in filter(lambda x: x[1] == Mode.absent, clues):
            out.allows[pos].discard(ltr)
        # set the correct positions to one letter allowed
        for pos, mode, ltr in filter(lambda x: x[1] == Mode.correct, clues):
            out.allows[pos] = {ltr}
            out.at_least[ltr] = out.at_least.get(ltr, 0) + 1

        return out

    @staticmethod
    def diff(mystry: str, guess: str):
        """
        for a given mystry word what would the constraints be if we you made this guess
        """
        mguess = guess
        mapping = [-1, -1, -1, -1, -1]
        for pos in range(5):
            if mystry[pos] == mguess[pos]:
                mapping[pos] = pos
                mguess = mguess[:pos] + "_" + mguess[pos + 1 :]
        for pos in range(5):
            if mapping[pos] != -1:
                continue
            ltr = mystry[pos]
            to_pos = mapping[pos] = mguess.find(ltr)
            if to_pos != -1:
                mguess = mguess[:to_pos] + "_" + mguess[to_pos + 1 :]

        rmapping = {
            v: Mode.correct if k == v else Mode.present
            for k, v in enumerate(mapping)
            if v != -1
        }

        clues = "".join(
            [rmapping.get(pos, Mode.absent).value + guess[pos] for pos in range(5)]
        )

        return Constraint.parse(clues)

    def __and__(self, othr):
        """
        override the & operator to combine two constraints into one.
        """
        return Constraint(
            {
                k: max(othr.at_least.get(k, 0), self.at_least.get(k, 0))
                for k in self.at_least | othr.at_least
            },
            list(map(lambda a: a[0].intersection(a[1]), zip(self.allows, othr.allows))),
            self.used.union(othr.used),
        )

    def __repr__(self) -> str:
        """
        for the humans
        """
        pass
        out = f"words used: [{', '.join(self.used)}], "
        out += f"at least: [{', '.join([f'{c}:{ltr}' for ltr, c in self.at_least.items()])}], "
        # out += f"allowed: [{', '.join(map(str, map(len, self.allows)))}]"
        def func(ltrs):
            return "".join(sorted(list(ltrs)))

        out += f"allowed: [{', '.join(map(str, map(func, self.allows)))}]"
        return out

    def match(self, word: str) -> bool:
        """
        does the word fit these constraints
        """
        fail = False
        if word in self.used:
            fail = True
        word_has = Counter(word)
        for ltr, count in self.at_least.items():
            if word_has[ltr] < count:
                fail = True
        for pos, ltr in enumerate(word):
            if ltr not in self.allows[pos]:
                fail = True
        return not fail

    def score(self):
        """
        depricated: i don't like how this is a guess at how good the filter is.

        how specific the constraints are. inverse how many letters are
        allowed in each posision. if all 26 letters are allowed then
        the score is 1/26. if only one letter is allowed then the score
        is 1/1.
        """
        return sum(map(lambda allow: 1 / len(allow), self.allows))


def do_score(args):
    guess, candidates = args
    # total_matched = 0
    # total_candidate = 0
    total = 0
    for mystry in candidates:
        if guess == mystry:
            continue
        cons = Constraint.diff(mystry, guess)
        # changed
        # - from: cons.score()
        # - to: use the filter and see how good it is for reals.
        #
        # O(n^3) for small values of n is fine. right?
        total += sum(
            1 for _ in filter(lambda candidate: not cons.match(candidate), candidates)
        )
    return guess, total


def make_guess(candidates, constraints):
    candidates = list(filter(constraints.match, candidates))

    # compute the scores in parallel
    with Pool() as p:
        scores = list(
            p.imap_unordered(
                do_score, map(lambda guess: (guess, candidates), candidates)
            )
        )

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def solve(mystry, starting):
    """
    auto guess the top pick and fold the constraints in until you run out of candidates
    """
    candidates = set(map(lambda x: x.strip().lower(), open("words.txt", "r")))
    constraints = Constraint.diff(mystry, starting)
    rounds = 1
    print(mystry)
    print(f"\t{starting}")
    while True:
        guesses = make_guess(candidates, constraints)
        if len(guesses) == 0:
            print("\t-1")
            return
        rounds += 1
        print(f"\t{guesses[0][0]} {len(guesses)}")
        if guesses[0][0] == mystry:
            break
        constraints &= Constraint.diff(mystry, guesses[0][0])
    print(f"\t{rounds}")


def daily():
    """
    parse the constraints from 'input.txt' and produce the next guess
    """
    constraints = Constraint()
    for line in map(lambda x: x.strip().lower(), fileinput.input("input.txt")):
        if line.startswith("#") or not line:
            continue
        constraints &= Constraint.parse(line)

    print(constraints)

    words = set(map(lambda x: x.strip().lower(), open("words.txt", "r")))
    hist = set(map(lambda x: x.strip().lower(), open("history.txt", "r")))
    candidates = words - hist
    guesses = make_guess(candidates, constraints, words)
    print("number of candidates", len(guesses))
    for n in range(min(len(guesses), 20)):
        guess, score = guesses[n]
        print(guess, score)


def historical(starting):
    """
    see what happens for every possible mystry word.
    """
    words = set(map(lambda x: x.strip().lower(), open("words.txt", "r")))
    for mystry in words:
        solve(mystry, starting)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        historical(sys.argv[1])
    else:
        daily()
