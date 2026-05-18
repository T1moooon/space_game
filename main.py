import asyncio
import curses
import random
import time

from curses_tools import draw_frame, get_frame_size, read_controls
from obstacles import Obstacle
from physics import update_speed


TIC_TIMEOUT = 0.1
ROCKET_SPEED = 1
STARS_COUNT = 100
BORDER_PADDING = 1
coroutines = []
obstacles = []
obstacles_in_last_collisions = []


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def fill_orbit_with_garbage(canvas, garbage_frames):
    """Continuously spawn falling garbage at random columns."""
    rows, columns = canvas.getmaxyx()

    while True:
        frame = random.choice(garbage_frames)
        column = random.randint(BORDER_PADDING, columns - BORDER_PADDING - 1)
        coroutines.append(fly_garbage(canvas, column, frame))

        await sleep(20)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(garbage_frame)

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0
    obstacle = Obstacle(row, column, frame_rows, frame_columns)
    obstacles.append(obstacle)

    try:
        while row < rows_number:
            obstacle.row = row
            draw_frame(canvas, row, column, garbage_frame)
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, garbage_frame, negative=True)

            if obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(obstacle)
                return

            row += speed
    finally:
        obstacles.remove(obstacle)


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

        for obstacle in obstacles:
            if obstacle.has_collision(round(row), round(column)):
                obstacles_in_last_collisions.append(obstacle)
                return

        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol="*"):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


async def animate_rocket(canvas, row, column, frame_1, frame_2):
    height, width = canvas.getmaxyx()
    frame_rows, frame_cols = get_frame_size(frame_1)

    rows_speed, columns_speed = 0, 0

    while True:
        for frame in (frame_1, frame_2):
            for _ in range(2):
                rows_dir, cols_dir, space_pressed = read_controls(canvas)

                if space_pressed:
                    coroutines.append(fire(canvas, row, column + frame_cols // 2))

                rows_speed, columns_speed = update_speed(
                    rows_speed,
                    columns_speed,
                    rows_dir,
                    cols_dir,
                    row_speed_limit=ROCKET_SPEED,
                    column_speed_limit=ROCKET_SPEED,
                )
                row = max(1, min(row + rows_speed, height - frame_rows - 1))
                column = max(1, min(column + columns_speed, width - frame_cols - 1))

                draw_frame(canvas, row, column, frame)
                await asyncio.sleep(0)
                draw_frame(canvas, row, column, frame, negative=True)


def draw(canvas):
    curses.curs_set(0)
    canvas.border()
    canvas.nodelay(True)

    with open("animation/rocket_frame_1.txt") as f:
        rocket_frame_1 = f.read()
    with open("animation/rocket_frame_2.txt") as f:
        rocket_frame_2 = f.read()
    with open("animation/trash_small.txt") as f:
        trash_small = f.read()
    with open("animation/trash_large.txt") as f:
        trash_large = f.read()
    with open("animation/trash_xl.txt") as f:
        trash_xl = f.read()

    garbage_frames = [trash_small, trash_large, trash_xl]
    height, width = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(rocket_frame_1)
    row = height // 2 - frame_rows // 2
    col = width // 2 - frame_columns // 2

    coords = [
        (
            random.randint(BORDER_PADDING, height - BORDER_PADDING - 1),
            random.randint(BORDER_PADDING, width - BORDER_PADDING - 1),
        )
        for _ in range(STARS_COUNT)
    ]

    for star_row, star_col in coords:
        coroutines.append(blink(canvas, star_row, star_col, random.choice("+*.:")))

    for coro in coroutines:
        for _ in range(random.randint(0, 30)):
            coro.send(None)

    coroutines.append(animate_rocket(canvas, row, col, rocket_frame_1, rocket_frame_2))
    coroutines.append(fill_orbit_with_garbage(canvas, garbage_frames))

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
