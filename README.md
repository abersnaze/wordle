# WORDLE SOLVER

This wordle solver is meant to be run once for each guess. The program tells you what to guess in turn you feed it the clues and it will tell you what to guess next.

## INPUT

if you guess `WEARY` and the `W` is in the right spot put a `+` (plus) the response as

> `+W_E_A_R_Y`

if you guess `PILLS` and the letter `I` is in the word but in the wrong spot encode it with `-` (minus) like

> `_P-I_L_L_S`

for all the letters that aren't in the word you prefix with an `_` (underscore)

## RUNNING

### DAILY MODE

once the `input.txt` is saved run the program to get the next guess.

`./wordle.py`

for the first guess it might take up to 20 seconds to go through the possibilities.

after you've found a solution add it to the `history.txt`. it won't be included in computations or guesses after that.

Running the program with an empty `input.txt` takes a long time. I've precomputed the output in `first.txt`

### HISTORY MODE

if you run the script with one (five letter word) argument.

`./wordle.py first`

it will evaluate that as a starting guess for all possible mystery words.

## RANKING GUESSES

Probably wonder what that number is after the guess. The way the program ranks guess is very slow but luckly the number of words is usually small (in the 100s) so it only takes a few seconds.

The program imagines a universe where every word is the correct answer and you guess all words and you get a clue. Add up how many, of all words, that clue eliminates. for the geeks out there it’s O(n^3)

## TO DO

* easy mode solver: when to switch to choosing a word that you know isn't going to be the answer?
  * always on the second guess.
  * if your in danger of losing. for example you know `__+a__+e+r`. that only leaves you two letters to eleminate 29 possibilities in three or four guesses.