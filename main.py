import curses
import time


def draw(canvas):
    row, column = (5, 20)
    canvas.addstr(row, column, "Hello, World!")
    canvas.refresh()
    time.sleep(5)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
