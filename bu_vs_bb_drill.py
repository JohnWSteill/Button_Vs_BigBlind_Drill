#!/usr/bin/env python3
"""
BU vs BB Drill RNG
Reveals streets iteratively (press SPACE or ENTER to continue, Ctrl-C to stop).

Usage:
  python bu_vs_bb_drill.py 5 --seed 123
"""

import argparse
import random
import sys
import time
import threading
import io
from typing import List, Tuple

RANKS = "23456789TJQKA"
SUITS = "shdc"  # spades, hearts, diamonds, clubs
SUIT_SYMBOLS = {"s": "♠", "h": "♥", "d": "♦", "c": "♣"}

# ANSI color codes for four-color deck (bright colors for dark backgrounds)
SUIT_COLORS = {
    "s": "\033[97m",  # bright white (black suits on light background)
    "h": "\033[91m",  # bright red
    "d": "\033[94m",  # bright blue
    "c": "\033[92m",  # bright green
}
RESET_COLOR = "\033[0m"

# ------------------------ Range Logic (from user's BTN 45.25% image) --------


def rank_value(r: str) -> int:
    return RANKS.index(r)


def normalize_cards(card1: str, card2: str) -> Tuple[str, str, bool, bool]:
    """
    Return (hi_rank, lo_rank, suited, pair) given two cards like 'As','Kd'.
    """
    r1, s1 = card1[0], card1[1]
    r2, s2 = card2[0], card2[1]
    pair = r1 == r2
    suited = s1 == s2
    # sort ranks high->low by rank_value
    if rank_value(r1) > rank_value(r2):
        hi, lo = r1, r2
    else:
        hi, lo = r2, r1
    return hi, lo, suited, pair


def in_suited_rules(hi: str, lo: str) -> bool:
    """Apply suited inclusion rules from the user's BTN image."""
    lo_val = rank_value(lo)
    # Axs, Kxs, Qxs: all
    if hi in ("A", "K", "Q"):
        return True
    if hi == "J":
        return lo_val >= rank_value("4")
    if hi == "T":
        return lo_val >= rank_value("6")
    if hi == "9":
        return lo_val >= rank_value("6")
    if hi == "8":
        return lo_val >= rank_value("5")
    if hi == "7":
        return lo_val >= rank_value("5")
    if hi == "6":
        return lo_val >= rank_value("4")
    if hi == "5":
        return lo_val >= rank_value("3")
    if hi == "4":
        return lo == "3"  # exactly 43s
    return False


def in_offsuit_rules(hi: str, lo: str) -> bool:
    """Apply offsuit inclusion rules from the user's BTN image."""
    # A3o+, K8o+, Q8o+, J8o+, T8o+, plus 98o
    if hi == "A":
        return rank_value(lo) >= rank_value("3")
    if hi == "K":
        return rank_value(lo) >= rank_value("8")
    if hi == "Q":
        return rank_value(lo) >= rank_value("8")
    if hi == "J":
        return rank_value(lo) >= rank_value("8")
    if hi == "T":
        return rank_value(lo) >= rank_value("8")
    # special case: 98o
    return hi == "9" and lo == "8"


def is_btn_open_45(card1: str, card2: str) -> bool:
    """
    Return True if two cards are in the 45.25% BTN open range.
    """
    hi, lo, suited, pair = normalize_cards(card1, card2)
    if pair:
        return True  # all pairs 22+
    if suited:
        return in_suited_rules(hi, lo)
    else:
        return in_offsuit_rules(hi, lo)


# ------------------------ Dealing ------------------------


def fresh_deck() -> List[str]:
    return [r + s for r in RANKS for s in SUITS]


def deal_btn_open_and_board(
    seed: int | None = None,
) -> Tuple[Tuple[str, str], List[str]]:
    """Deal a BTN hand from the 45% range, plus a 5-card board."""
    if seed is not None:
        random.seed(seed)
    while True:
        deck = fresh_deck()
        random.shuffle(deck)
        c1, c2 = deck[0], deck[1]
        if is_btn_open_45(c1, c2):
            board = deck[2:7]
            return (c1, c2), board


# ------------------------ CLI helpers ------------------------


def wait_for_key_with_timeout(timeout_seconds: int = 600) -> bool:
    """Wait for key press with timeout and countdown display.
    Returns True if key was pressed, False if timeout occurred."""
    import termios
    import tty
    import select

    start_time = time.time()
    key_pressed = threading.Event()

    def check_keypress():
        try:
            fd = sys.stdin.fileno()
        except io.UnsupportedOperation:
            return  # In pytest or redirected stdin, just exit the thread
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while not key_pressed.is_set():
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    ch: str = sys.stdin.read(1)
                    if ch == "\x03":  # Ctrl-C
                        raise KeyboardInterrupt
                    if ch in (" ", "\r", "\n"):
                        key_pressed.set()
                        return
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    # Start keypress checking thread
    key_thread = threading.Thread(target=check_keypress, daemon=True)
    key_thread.start()

    # Countdown display
    while time.time() - start_time < timeout_seconds:
        remaining = timeout_seconds - int(time.time() - start_time)
        if key_pressed.is_set():
            # Clear countdown and return
            print(f"\r{' ' * 20}\r", end="", flush=True)
            return True

        # Display countdown with two tabs separation
        print(f"\r\t\t{remaining:2d}s", end="", flush=True)
        time.sleep(0.1)

    # Timeout reached
    print(f"\r{' ' * 20}\r", end="", flush=True)
    return False


def wait_for_key(
    prompt: str = "Press SPACE or ENTER to continue, Ctrl-C to stop...",
) -> None:
    """Cross-platform 'press space/enter to continue'."""
    if prompt:
        print(prompt, flush=True)
    wait_for_key_with_timeout()


def format_card(card: str) -> str:
    """Convert a card like 'As' to colored 'A♠'."""
    rank, suit = card[0], card[1]
    color = SUIT_COLORS[suit]
    symbol = SUIT_SYMBOLS[suit]
    return f"{color}{rank}{symbol}{RESET_COLOR}"


def format_cards(cards: List[str]) -> str:
    return " ".join(format_card(card) for card in cards)


def main():
    parser = argparse.ArgumentParser(
        description="BU vs BB Drill RNG (iterative street reveal)"
    )
    parser.add_argument("hands", type=int, help="number of hands to generate")
    parser.add_argument(
        "--seed", type=int, default=None, help="optional RNG seed"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="decision time per street in seconds (default: 600)",
    )
    args = parser.parse_args()

    seed = args.seed
    timeout = args.timeout

    for i in range(1, args.hands + 1):
        hand, board = deal_btn_open_and_board(seed=seed)
        # Increment seed to avoid identical outputs when repeatedly seeding
        if seed is not None:
            seed += 1

        print(f"\nHand {i}:")
        print(f"Preflop: {format_card(hand[0])} {format_card(hand[1])}")
        wait_for_key_with_timeout(timeout)

        flop = board[:3]
        print(f"Flop:    {format_cards(flop)}")
        wait_for_key_with_timeout(timeout)

        turn = board[3]
        print(f"Turn:    {format_card(turn)}")
        wait_for_key_with_timeout(timeout)

        river = board[4]
        print(f"River:   {format_card(river)}")
        wait_for_key_with_timeout(timeout)
    print("\nDone. Good session.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
