import asyncio
import curses
import time


async def blink(canvas, row, column, symbol="*"):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)


def draw(canvas):
    curses.curs_set(0)
    canvas.border()

    coords = [(5, 10), (5, 15), (5, 20), (5, 25), (5, 30)]
    coroutines = [blink(canvas, row, col) for row, col in coords]

    while True:
        for corotine in coroutines:
            corotine.send(None)
        canvas.refresh()
        time.sleep(0.5)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
