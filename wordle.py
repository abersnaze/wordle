#! /usr/bin/python3

import datetime
import fileinput
import sys
import argparse
from collections import Counter
from enum import Enum
from multiprocessing import Pool
from typing import Dict, FrozenSet, List, Set, Tuple

class Mode(Enum):
    absent = "_"
    present = "-"
    correct = "+"


class Constraint:
    # how many of each letter must there be
    at_least: FrozenSet[Tuple[str, int]]
    # what letters are allowed in each of the 5 positions
    allows: Tuple[
        FrozenSet[str], FrozenSet[str], FrozenSet[str], FrozenSet[str], FrozenSet[str]
    ]

    def __init__(
        self,
        at_least=None,
        allows=None,
    ) -> None:
        self.at_least = at_least if at_least else frozenset()
        # allow a to z in any possion
        self.allows = (
            allows
            if allows
            else [
                frozenset(map(chr, range(97, 123))),
                frozenset(map(chr, range(97, 123))),
                frozenset(map(chr, range(97, 123))),
                frozenset(map(chr, range(97, 123))),
                frozenset(map(chr, range(97, 123))),
            ]
        )

    @staticmethod
    def parse(line: str) -> None:
        """
        parse the result of a guess for a five letter word.
        each letter prefixed with:
        _ == absent letter
        - == present but in the wrong place
        + == correct letter in the right place.
        """

        at_least = dict()
        # allow a to z in any possion
        allows = [
            set(map(chr, range(97, 123))),
            set(map(chr, range(97, 123))),
            set(map(chr, range(97, 123))),
            set(map(chr, range(97, 123))),
            set(map(chr, range(97, 123))),
        ]

        # parse the 10 characters into 5 tuples.
        clues = []
        for pos in range(0, 10, 2):
            mode = Mode(line[pos])
            ltr = line[pos + 1]
            clues.append((pos // 2, mode, ltr))

        # discard the absent letters
        for pos, mode, ltr in filter(lambda x: x[1] == Mode.absent, clues):
            for allow in allows:
                allow.discard(ltr)
        # add back the present letters
        for pos, mode, ltr in filter(lambda x: x[1] == Mode.present, clues):
            for allow in allows:
                allow.add(ltr)
            allows[pos].discard(ltr)
            at_least[ltr] = at_least.get(ltr, 0) + 1
        # discard the present letters from where they were wrong
        for pos, mode, ltr in filter(lambda x: x[1] == Mode.absent, clues):
            allows[pos].discard(ltr)
        # set the correct positions to one letter allowed
        for pos, mode, ltr in filter(lambda x: x[1] == Mode.correct, clues):
            allows[pos] = {ltr}
            at_least[ltr] = at_least.get(ltr, 0) + 1

        # freeze the constraints
        at_least = frozenset([(k, v) for k, v in at_least.items()])
        allow = tuple(frozenset for i in allows)
        out = Constraint(at_least, allows)
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
        self_at_least = {k: v for k, v in self.at_least}
        othr_at_least = {k: v for k, v in othr.at_least}

        return Constraint(
            frozenset(
                {
                    (k, max(self_at_least.get(k, 0), othr_at_least.get(k, 0)))
                    for k in self_at_least | othr_at_least
                }
            ),
            tuple(map(lambda a: a[0].intersection(a[1]), zip(self.allows, othr.allows))),
        )

    def __repr__(self) -> str:
        """
        for the humans
        """
        out = f"at least: [{', '.join([f'{c}:{ltr}' for ltr, c in self.at_least])}], "
        # out += f"allowed: [{', '.join(map(str, map(len, self.allows)))}]"
        def func(ltrs):
            return "".join(sorted(list(ltrs)))

        out += f"allowed: [{', '.join(map(str, map(func, self.allows)))}]"
        return out

    def not_match(self, word: str) -> bool:
        return not self.match(word)

    def match(self, word: str) -> bool:
        """
        does the word fit these constraints
        """
        fail = False
        word_has = Counter(word)
        for ltr, count in self.at_least:
            if word_has[ltr] < count:
                fail = True
        for pos, ltr in enumerate(word):
            if ltr not in self.allows[pos]:
                fail = True
        return not fail

score_cache = {}

def do_score(constraints, candidates):
    cache_key = (constraints, candidates)
    if cache_key in score_cache:
        return score_cache[cache_key]
    score = sum(
        1
        for _ in filter(lambda candidate: not constraints.match(candidate), candidates)
    )
    score_cache[cache_key] = score
    return score


def do_scores(args):
    guess, candidates = args
    # total_matched = 0
    # total_candidate = 0
    total = 0
    for mystry in candidates:
        if guess == mystry:
            continue
        constraints = Constraint.diff(mystry, guess)
        # changed
        # - from: cons.score()
        # - to: use the filter and see how good it is for reals.
        #
        # O(n^3) for small values of n is fine. right?
        total += do_score(constraints, candidates)
    return guess, total


def make_guess(candidates, guessable):
    # compute the scores in parallel
    with Pool() as p:
        scores = list(
            p.imap_unordered(
                do_scores, map(lambda guess: (guess, candidates), guessable)
            )
        )

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def solve(mystry, starting):
    """
    auto guess the top pick and fold the constraints in until you run out of candidates
    """
    candidates = frozenset(map(lambda x: x.strip().lower(), open("words.txt", "r")))
    constraints = Constraint.diff(mystry, starting)
    rounds = 1
    print(mystry)
    print(f"\t{starting}")
    while True:
        candidates = frozenset(filter(constraints.match, candidates))
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


def rot13(x: str) -> str:
    return "".join(
        map(lambda ltr: chr(ord("a") + (ord(ltr.lower()) + 13 - ord("a")) % 26), x)
    )


def daily(easy, candidate_words, allowed_words):
    """
    parse the constraints from 'input.txt' and produce the next guess
    """
    constraints = Constraint()
    for line in map(lambda x: x.strip().lower(), fileinput.input("input.txt")):
        if line.startswith("#") or not line:
            continue
        constraints &= Constraint.parse(line)

    print(constraints)

    start = datetime.date(2021, 6, 19)
    end = datetime.date.today()
    day = (end - start).days
    print(f"day #{day}")

    candidates = candidate_words
    candidates = frozenset(filter(constraints.match, candidates))
    print("number of candidates", len(candidates))

    if easy:
        guesses = make_guess(candidates, allowed_words)
    else:
        guesses = make_guess(candidates, candidates)  # hard mode

    for n in range(min(len(guesses), 20)):
        guess, score = guesses[n]
        print(guess, score)


def historical(starting, easy, candidate_words, allowed_words):
    """
    see what happens for every possible mystry word.
    """
    for mystry in candidate_words:
        solve(mystry, starting)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="wordle solver")
    parser.add_argument("--first", type=str, help="try this word as the first guess")
    parser.add_argument(
        "--easy",
        action="store_true",
        default=False,
        help="allow the guesses to not use all the clues",
    )
    parser.add_argument("--all", action="store_true", default=False)
    args = parser.parse_args()
    candidate_words = set(map(lambda x: x.strip().lower(), open("words.txt", "r")))
    allowed_words = set(map(lambda x: x.strip().lower(), open("allowed.txt", "r")))
    if args.all:
        print("using all words", len(candidate_words), len(allowed_words))
        candidate_words = allowed_words

    if args.first is not None:
        historical(args.first, args.easy, candidate_words, allowed_words)
    else:
        daily(args.easy, candidate_words, allowed_words)
