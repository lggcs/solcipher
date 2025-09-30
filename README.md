### SolCipher

### Overview

A compact, readable Python CLI implementing the Solitaire Pontifex cipher by Bruce Schneier. Use a 54-card deck (two jokers) to generate a keystream, supports an optional passphrase key schedule, accepts a custom deck, and can encrypt or decrypt A–Z text while grouping output into blocks.

### Features

- Full Solitaire cipher implementation with A and B jokers, joker moves, triple cut, and count cut.

- Optional passphrase key schedule.

- Accepts Unicode suit tokens and an optional custom 54-card deck.

- Verbose mode to show internal deck transformations.
 
- Outputs grouped blocks (configurable size).

- No third-party packages required.

### Dependencies

- Python 3.7 or newer.

- Optional: readline for input prefill on Unix-like terminals (falls back to builtin input if unavailable).

### Installation and Quick Start

- Clone or download this repository.

- Ensure Python 3.7+ is installed.

- python solcipher.py --help

### Usage

#### Encrypt text:

`python solcipher.py -e "Hello World"`

#### Decrypt text with passphrase:

`python solcipher.py -d "ASVQX TIXJB" -p "SECRET"`

#### Use a custom deck (54 tokens, space-separated):

`python solcipher.py -e "TEST" --deck "A♣ 2♣ 3♣ ... A B"`

#### Show verbose deck transformations:

`python solcipher.py -e "CRYPTONOMICON" -v`

### CLI options summary:

```
-e, --encrypt PLAINTEXT

-d, --decrypt CIPHERTEXT

-p, --passphrase PASS

--deck TOKENS (default is standard Unicode-suit deck)

-g, --group-size N (default 5)

-v, --verbose
```

### Notes:

- Input is cleaned to A–Z letters only and converted to uppercase before processing.

- Custom deck must contain exactly 54 distinct tokens; use A and B to represent the jokers.

### References
- [Bruce Schneier Solitaire Pontifex cipher original description and related cryptography resources.](https://www.schneier.com/academic/solitaire/)
