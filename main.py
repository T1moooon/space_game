import asyncio
import curses
import random
import time


TIC_TIMEOUT = 0.1


async def blink(canvas, row, column, symbol="*"):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


def draw(canvas):
    curses.curs_set(0)
    canvas.border()

    height, width = canvas.getmaxyx()

    coords = [
        (random.randint(1, height - 2), random.randint(1, width - 2))
        for _ in range(100)
    ]

    coroutines = [blink(canvas, row, col, random.choice("+*.:")) for row, col in coords]

    while True:
        for corotine in coroutines:
            corotine.send(None)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
