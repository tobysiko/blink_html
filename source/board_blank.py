# -*- coding: utf-8 -*-
"""Blink player board - blank, print-exact A4 landscape (mm units).

THE SAME BOARD AS board_a4.py, by construction.

This file used to draw a board of its own - the v0.17 one, with a FOOD
column, a "3 per terrain" scoring line and a victory row hanging off the
sheet - and build_pdfs.sh went on printing it as Blink-player-board-blank.pdf
long after every rule on it had left the game. board_a4.py has produced a
blank board (no demo units, no highlighted band) since v0.20, so the blank
sheet is now simply that board, written under this name. One drawing, one set
of rules: a fix to the board cannot miss the blank copy again.

    python3 board_blank.py   ->  board_blank.svg
"""
import pathlib

import board_a4


if __name__ == "__main__":
    out = pathlib.Path(__file__).resolve().parent / "board_blank.svg"
    out.write_text(board_a4.build())
    print("wrote board_blank.svg")
