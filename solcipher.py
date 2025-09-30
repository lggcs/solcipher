#!/usr/bin/env python3
import argparse
import re
import sys
from typing import Generator, List, Union

# Default standard deck order (space-separated tokens)
default_line = (
    'A♣ 2♣ 3♣ 4♣ 5♣ 6♣ 7♣ 8♣ 9♣ '
    'T♣ J♣ Q♣ K♣ '
    'A♦ 2♦ 3♦ 4♦ 5♦ 6♦ 7♦ 8♦ 9♦ '
    'T♦ J♦ Q♦ K♦ '
    'A♥ 2♥ 3♥ 4♥ 5♥ 6♥ 7♥ 8♥ 9♥ '
    'T♥ J♥ Q♥ K♥ '
    'A♠ 2♠ 3♠ 4♠ 5♠ 6♠ 7♠ 8♠ 9♠ '
    'T♠ J♠ Q♠ K♠ A B'
)

# Attempt to import readline for prefill support; fallback if unavailable
try:
    import readline  # type: ignore

    def input_with_prefill(prompt: str, prefill: str) -> str:
        """
        Show `prompt` with `prefill` already typed in. Works on Unix-like terminals.
        """
        def startup_hook() -> None:
            readline.insert_text(prefill)
            readline.redisplay()
        readline.set_startup_hook(startup_hook)
        try:
            return input(prompt)
        finally:
            readline.set_startup_hook(None)
except ImportError:
    def input_with_prefill(prompt: str, prefill: str) -> str:
        return input(prompt)


# Core mappings
JOKERS = {53: 'A', 54: 'B'}
SUITS = 'cdhs'
VALUES = 'A23456789TJQK'
SUITS_UNI = '\u2663\u2666\u2665\u2660'  # ♣♦♥♠


def _flip(iterable: Union[str, List[str]]) -> dict:
    return {ch: i for i, ch in enumerate(iterable)}


REV_JOKERS = {v: k for k, v in JOKERS.items()}
REV_SUITS = _flip(SUITS) | _flip(SUITS_UNI)
REV_VALUES = _flip(VALUES)


def read_card(token: str) -> int:
    """Parse a single card token into its numeric code 1–54."""
    if token in REV_JOKERS:
        return REV_JOKERS[token]
    m_r = re.search(r'[A23456789TJQK]', token)
    m_s = re.search(r'[cdhsCDHS\u2663\u2666\u2665\u2660]', token)
    if m_r and m_s:
        rank = m_r.group(0).upper()
        suit = m_s.group(0).lower()
        return 13 * REV_SUITS[suit] + REV_VALUES[rank] + 1
    raise ValueError(f"Invalid card token: {token}")


def card_writer(code: int, suits: str = SUITS) -> str:
    """Convert numeric code back to a single-character token."""
    if code in JOKERS:
        return JOKERS[code]
    rank = VALUES[(code - 1) % 13]
    suit = suits[(code - 1) // 13]
    return f"{rank}{suit}"


def combine_letters(a: str, b: str, sign: int = 1) -> str:
    """
    Combine plaintext letter `a` with keystream letter `b`.
    `sign=1` for encryption, `sign=-1` for decryption.
    """
    is_upper = a.isupper()
    base = 65 if is_upper else 97
    p0 = ord(a) - base
    k1 = ord(b) - 64
    c0 = (p0 + sign * k1) % 26
    return chr(base + c0)


def combine_text(text: str, key_gen: Generator[str, None, None], sign: int = 1) -> str:
    """
    Transform only A–Z/a–z in `text` via keystream `key_gen`.
    Non-letters are dropped before processing.
    """
    out: List[str] = []
    for ch in text:
        if 'A' <= ch <= 'Z' or 'a' <= ch <= 'z':
            k = next(key_gen)
            out.append(combine_letters(ch, k, sign))
    return ''.join(out)


class Deck:
    def __init__(self, cards: List[int], verbose: bool = False) -> None:
        if len(cards) != 54:
            raise ValueError("Deck must have 54 cards.")
        self.deck = list(cards)
        self.verbose = verbose

    @classmethod
    def create(cls, verbose: bool = False) -> "Deck":
        return cls(list(range(1, 55)), verbose)

    @classmethod
    def from_input(cls, inp: str, verbose: bool = False) -> "Deck":
        tokens = re.sub(
            r'[^AB2-9TJQKcdhsCDHS\u2663\u2666\u2665\u2660\s]',
            '', inp
        ).strip().split()
        if len(tokens) != 54:
            raise ValueError(f"Found {len(tokens)} cards, expected 54.")
        vals = [read_card(t) for t in tokens]
        if len(set(vals)) != 54:
            raise ValueError("Duplicate card detected.")
        return cls(vals, verbose)

    def add_password_letter(self, letter: str) -> "Deck":
        """Apply one passphrase letter to key-schedule."""
        self.shift_cut()
        cnt = ord(letter.upper()) - 64
        self.count_cut(cnt)
        return self

    @classmethod
    def from_password(cls, pw: str, verbose: bool = False) -> "Deck":
        deck = cls.create(verbose)
        for ch in pw:
            deck.add_password_letter(ch)
        return deck

    def search(self, code: int) -> int:
        return self.deck.index(code)

    def get_card(self, idx: int) -> int:
        return min(self.deck[idx], 53)

    def cycle_shift(self) -> None:
        self.deck.insert(0, self.deck.pop())

    def swap_down(self, code: int) -> "Deck":
        if self.deck[-1] == code:
            self.cycle_shift()
        i = self.search(code)
        j = (i + 1) % 54
        self.deck[i], self.deck[j] = self.deck[j], self.deck[i]
        return self

    def count_cut(self, count: int) -> "Deck":
        x = self.deck[:count]
        y = self.deck[count:-1]
        z = [self.deck[-1]]
        self.deck = y + x + z
        if self.verbose:
            print(f"Count cut ({count}):", end=' ')
            self.print_state()
        return self

    def shift_cut(self) -> "Deck":
        if self.verbose:
            print("=== ShiftCut Start ===")
            print("Before:", end=' ')
            self.print_state()

        # Joker A down one
        self.swap_down(REV_JOKERS['A'])
        if self.verbose:
            print("After A swap:", end=' ')
            self.print_state()

        # Joker B down two
        self.swap_down(REV_JOKERS['B']).swap_down(REV_JOKERS['B'])
        if self.verbose:
            print("After B swaps:", end=' ')
            self.print_state()

        # Triple cut
        i1, i2 = sorted([self.search(53), self.search(54)])
        top, mid, bot = (
            self.deck[:i1],
            self.deck[i1 : i2 + 1],
            self.deck[i2 + 1 :]
        )
        self.deck = bot + mid + top
        if self.verbose:
            print("After triple cut:", end=' ')
            self.print_state()

        # Count cut using bottom card
        bottom = self.deck[-1]
        cnt = bottom if bottom < 53 else 53
        self.count_cut(cnt)
        return self

    def next_key_letter(self) -> str:
        card = 54
        while card > 52:
            self.shift_cut()
            top = self.get_card(0)
            card = self.get_card(top)
        letter = chr((card - 1) % 26 + 65)
        if self.verbose:
            print("Next key letter:", letter)
        return letter

    def get_key_stream(self, length: int = 0) -> Generator[str, None, None]:
        i = 0
        while length <= 0 or i < length:
            yield self.next_key_letter()
            i += 1

    def encrypt(self, plaintext: str) -> str:
        return combine_text(plaintext, self.get_key_stream(), sign=1)

    def decrypt(self, ciphertext: str) -> str:
        return combine_text(ciphertext, self.get_key_stream(), sign=-1)

    def print_state(self, unicode: bool = True, color: bool = False) -> None:
        """Print the current deck state if verbose is enabled."""
        if not self.verbose:
            return
        suits = list(SUITS_UNI if unicode else SUITS)
        if color:
            suits = [
                suits[0],
                f"\x1b[31m{suits[1]}\x1b[0m",
                f"\x1b[31m{suits[2]}\x1b[0m",
                suits[3]
            ]
        line = ' '.join(card_writer(c, suits) for c in self.deck)
        print(line)


def group_text(text: str, size: int) -> str:
    if size <= 0:
        return text
    return ' '.join(text[i : i + size] for i in range(0, len(text), size))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Solitaire (Pontifex) Cipher – CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "-e", "--encrypt", metavar="PLAINTEXT",
        help="Text to encrypt."
    )
    mode_group.add_argument(
        "-d", "--decrypt", metavar="CIPHERTEXT",
        help="Text to decrypt."
    )
    parser.add_argument(
        "-p", "--passphrase", metavar="PASS",
        help="Optional shared passphrase."
    )
    parser.add_argument(
        "--deck", metavar="TOKENS", default=default_line,
        help="Optional 54-card deck (space-separated tokens)."
    )
    parser.add_argument(
        "-g", "--group-size", type=int, default=5,
        help="Group output into fixed-length blocks."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show internal deck transformations."
    )
    args = parser.parse_args()

    # Build initial deck
    if args.deck:
        deck = Deck.from_input(args.deck, verbose=args.verbose)
    else:
        deck = Deck.create(verbose=args.verbose)

    # Apply passphrase key-schedule
    if args.passphrase:
        for ch in args.passphrase:
            deck.add_password_letter(ch)

    # Prepare and clean text
    if args.encrypt:
        cleaned = re.sub(r'[^A-Za-z]', '', args.encrypt).upper()
        result = deck.encrypt(cleaned)
    else:
        cleaned = re.sub(r'[^A-Za-z]', '', args.decrypt).upper()  # type: ignore
        result = deck.decrypt(cleaned)

    # Group and output
    print(group_text(result, args.group_size))


if __name__ == "__main__":
    main()
