import asyncio
import curses
import random
import time

from curses_tools import draw_frame, get_frame_size, read_controls
from explosion import explode
from obstacles import Obstacle
from physics import update_speed


TIC_TIMEOUT = 0.1
ROCKET_SPEED = 1
STARS_COUNT = 100
BORDER_PADDING = 1
TICS_PER_YEAR = 15
PLASMA_GUN_YEAR = 2020
coroutines = []
obstacles = []
obstacles_in_last_collisions = []
rocket_row = 0
rocket_column = 0
year = 1957

PHRASES = {
    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1981: "Flight of the Shuttle Columbia",
    1998: "ISS start building",
    2011: "Messenger launch to Mercury",
    2020: "Take the plasma gun! Shoot the garbage!",
}


def get_garbage_delay_tics(year):
    if year < 1961:
        return None
    elif year < 1969:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < 2020:
        return 6
    else:
        return 2


async def count_years():
    global year
    while True:
        await sleep(TICS_PER_YEAR)
        year += 1


async def show_year(canvas):
    rows, columns = canvas.getmaxyx()
    row = rows - 2
    phrase = ""
    while True:
        phrase = PHRASES.get(year, phrase)
        message = f"Year: {year}  {phrase}"
        draw_frame(canvas, row, 1, message)
        await asyncio.sleep(0)
        draw_frame(canvas, row, 1, message, negative=True)


async def show_gameover(canvas, message):
    rows, columns = canvas.getmaxyx()
    frame_rows, frame_cols = get_frame_size(message)
    row = rows // 2 - frame_rows // 2
    column = columns // 2 - frame_cols // 2

    while True:
        draw_frame(canvas, row, column, message)
        await asyncio.sleep(0)


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def fill_orbit_with_garbage(canvas, garbage_frames):
    """Continuously spawn falling garbage at random columns."""
    rows, columns = canvas.getmaxyx()

    while True:
        delay = get_garbage_delay_tics(year)
        if delay is None:
            await asyncio.sleep(0)
            continue

        frame = random.choice(garbage_frames)
        column = random.randint(BORDER_PADDING, columns - BORDER_PADDING - 1)
        coroutines.append(fly_garbage(canvas, column, frame))

        await sleep(delay)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(garbage_frame)

    column = max(column, 0)
    column = min(column, columns_number - frame_columns - 1)

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
                center_row = obstacle.row + obstacle.rows_size // 2
                center_column = obstacle.column + obstacle.columns_size // 2
                coroutines.append(explode(canvas, center_row, center_column))
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


async def run_spaceship(canvas, frame):
    global rocket_row, rocket_column

    height, width = canvas.getmaxyx()
    frame_rows, frame_cols = get_frame_size(frame)

    rows_speed, columns_speed = 0, 0

    while True:
        rows_dir, cols_dir, space_pressed = read_controls(canvas)

        if space_pressed and year >= PLASMA_GUN_YEAR:
            coroutines.append(fire(canvas, rocket_row, rocket_column + frame_cols // 2))

        rows_speed, columns_speed = update_speed(
            rows_speed,
            columns_speed,
            rows_dir,
            cols_dir,
            row_speed_limit=ROCKET_SPEED,
            column_speed_limit=ROCKET_SPEED,
        )
        rocket_row = max(1, min(rocket_row + rows_speed, height - frame_rows - 1))
        rocket_column = max(
            1, min(rocket_column + columns_speed, width - frame_cols - 1)
        )

        await asyncio.sleep(0)


async def animate_rocket(canvas, frame_1, frame_2, gameover_frame):
    frame_rows, frame_cols = get_frame_size(frame_1)

    while True:
        for frame in (frame_1, frame_2):
            for _ in range(2):
                row, column = rocket_row, rocket_column
                draw_frame(canvas, row, column, frame)
                await asyncio.sleep(0)
                draw_frame(canvas, row, column, frame, negative=True)

                for obstacle in obstacles:
                    if obstacle.has_collision(row, column, frame_rows, frame_cols):
                        coroutines.append(show_gameover(canvas, gameover_frame))
                        return


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
    with open("animation/gameover.txt") as f:
        gameover_frame = f.read()

    global rocket_row, rocket_column

    garbage_frames = [trash_small, trash_large, trash_xl]
    height, width = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(rocket_frame_1)
    rocket_row = height // 2 - frame_rows // 2
    rocket_column = width // 2 - frame_columns // 2

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

    coroutines.append(run_spaceship(canvas, rocket_frame_1))
    coroutines.append(
        animate_rocket(canvas, rocket_frame_1, rocket_frame_2, gameover_frame)
    )
    coroutines.append(fill_orbit_with_garbage(canvas, garbage_frames))

    coroutines.append(count_years())
    coroutines.append(show_year(canvas))

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
