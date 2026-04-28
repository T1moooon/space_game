import asyncio
import curses
import random
import time

from cursed_tools import draw_frame, get_frame_size


TIC_TIMEOUT = 0.1


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), "*")
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), "O")
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), " ")

    row += rows_speed
    column += columns_speed

    symbol = "-" if columns_speed else "|"

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), " ")
        row += rows_speed
        column += columns_speed


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


async def animate_rocket(canvas, row, column, frame_1, frame_2):
    while True:
        draw_frame(canvas, row, column, frame_1)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame_1, negative=True)

        draw_frame(canvas, row, column, frame_2)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame_2, negative=True)


def draw(canvas):
    curses.curs_set(0)
    canvas.border()

    with open("animation/rocket_frame_1.txt") as f:
        rocket_frame_1 = f.read()
    with open("animation/rocket_frame_2.txt") as f:
        rocket_frame_2 = f.read()

    height, width = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(rocket_frame_1)
    row = height // 2 - frame_rows // 2
    col = width // 2 - frame_columns // 2

    coords = [
        (random.randint(1, height - 2), random.randint(1, width - 2))
        for _ in range(100)
    ]

    coroutines = [blink(canvas, row, col, random.choice("+*.:")) for row, col in coords]
    coroutines.append(fire(canvas, height - 2, width // 2))
    coroutines.append(animate_rocket(canvas, row, col, rocket_frame_1, rocket_frame_2))

    for coro in coroutines:
        for _ in range(random.randint(0, 30)):
            coro.send(None)

    while True:
        for coroutine in coroutines[:]:
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
