import curses

def select_source(sources):
    def print_menu(stdscr, selected_row_idx):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        for idx, source in enumerate(sources):
            x = w//2 - len(source)//2
            y = h//2 - len(sources)//2 + idx
            if idx == selected_row_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, source)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, source)
        stdscr.refresh()

    def main(stdscr):
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

        current_row = 0
        print_menu(stdscr, current_row)

        while True:
            key = stdscr.getch()
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(sources) - 1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                return current_row

            print_menu(stdscr, current_row)

    return curses.wrapper(main)

def choose_source(sources):
    sources = ["All Sources"] + sources
    selected = select_source(sources)
    return sources[selected] if selected > 0 else None