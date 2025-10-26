import bu_vs_bb_drill
import pytest
import sys


def test_fresh_deck_len():
    deck = bu_vs_bb_drill.fresh_deck()
    assert len(deck) == 52


def test_deal_btn_open_and_board_returns_valid():
    hand, board = bu_vs_bb_drill.deal_btn_open_and_board(seed=42)
    assert isinstance(hand, tuple)
    assert len(hand) == 2
    assert isinstance(board, list)
    assert len(board) == 5


def test_format_card_output():
    card = "As"
    out = bu_vs_bb_drill.format_card(card)
    assert "A" in out and ("\u2660" in out or "♠" in out)


def test_format_cards_output():
    cards = ["As", "Kd", "7h"]
    out = bu_vs_bb_drill.format_cards(cards)
    # Check that each rank appears at least once
    for rank in ["A", "K", "7"]:
        assert rank in out


def test_main_runs(monkeypatch: pytest.MonkeyPatch):
    # Patch input to simulate quick ENTER presses
    monkeypatch.setattr("sys.stdin.read", lambda n=1: "\n")
    monkeypatch.setattr(sys, "argv", ["prog", "1", "--timeout", "0"])
    bu_vs_bb_drill.main()
