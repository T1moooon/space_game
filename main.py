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

    coroutine = blink(canvas, 5, 20)

    coroutine.send(None)
    canvas.refresh()
    time.sleep(2)

    coroutine.send(None)
    canvas.refresh()
    time.sleep(0.3)

    coroutine.send(None)
    canvas.refresh()
    time.sleep(0.5)

    coroutine.send(None)
    canvas.refresh()
    time.sleep(0.3)
    time.sleep(3)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
