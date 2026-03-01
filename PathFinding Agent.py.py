import pygame
import math
import random
import time
from queue import PriorityQueue

pygame.init()
pygame.font.init()

# ─── Layout ───────────────────────────────────────────────────────────────────
GRID_WIDTH  = 620
PANEL_WIDTH = 280
WIN_WIDTH   = GRID_WIDTH + PANEL_WIDTH
WIN_HEIGHT  = 700
WIN         = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Dynamic Pathfinding Agent  ·  AI Assignment 2")

# ─── Color Palette ────────────────────────────────────────────────────────────
# Grid area — warm cream/ivory
GRID_BG       = (255, 252, 235)   # Warm cream background
GRID_LINE     = (220, 210, 175)   # Soft tan grid lines

# Panel — deep warm brown/dark golden
PANEL_BG      = (42,  32,  10)    # Very dark brown
PANEL_BORDER  = (160, 120,  30)   # Golden border line
SECTION_LINE  = (80,  62,  18)    # Subtle dark gold divider

# Button colors — dark golden tones
BTN_IDLE      = (72,  54,  14)    # Dark golden brown
BTN_HOVER     = (95,  72,  18)    # Slightly lighter gold
BTN_ACTIVE    = (180, 140,  30)   # Bright gold when active
BTN_BORDER    = (130, 100,  22)   # Gold border
BTN_TEXT      = (20,  15,   5)    # Near-black text on buttons
BTN_TEXT_MUTED= (140, 110,  40)   # Muted gold for inactive

# Node state colors — vivid and clear
C_EMPTY       = (248, 244, 220)   # Warm cream cell
C_WALL        = (55,  40,  20)    # Dark chocolate brown wall
C_START       = (220,  60,  40)   # Vivid red-orange start
C_END         = (30,  160,  80)   # Rich emerald green goal
C_OPEN        = (60,  140, 220)   # Clear sky blue frontier
C_CLOSED      = (180, 140, 200)   # Soft lavender visited
C_PATH        = (255, 195,   0)   # Bright golden yellow path

# Panel text
TEXT_HEADING  = (255, 220,  80)   # Bright warm gold headings
TEXT_BODY     = (20,   15,   5)   # Near-black for instructions/buttons
TEXT_MUTED    = (160, 130,  55)   # Muted gold for labels/hints
TEXT_WHITE    = (255, 248, 220)   # Cream white for title

# Status colors
STATUS_OK     = (80,  200, 100)
STATUS_ERR    = (220,  70,  60)
STATUS_INFO   = (255, 195,  50)

# ─── Fonts ────────────────────────────────────────────────────────────────────
try:
    F_TITLE   = pygame.font.SysFont("georgia",    20, bold=True)
    F_SUB     = pygame.font.SysFont("georgia",    11)
    F_HEADING = pygame.font.SysFont("segoeui",    13, bold=True)
    F_LABEL   = pygame.font.SysFont("segoeui",    13)
    F_SMALL   = pygame.font.SysFont("segoeui",    12)
    F_MONO    = pygame.font.SysFont("consolas",   13, bold=True)
    F_METRIC  = pygame.font.SysFont("consolas",   14, bold=True)
except:
    F_TITLE   = pygame.font.SysFont("serif",      20, bold=True)
    F_SUB     = pygame.font.SysFont("serif",      11)
    F_HEADING = pygame.font.SysFont("sans",       13, bold=True)
    F_LABEL   = pygame.font.SysFont("sans",       13)
    F_SMALL   = pygame.font.SysFont("sans",       12)
    F_MONO    = pygame.font.SysFont("monospace",  13, bold=True)
    F_METRIC  = pygame.font.SysFont("monospace",  14, bold=True)


# ─── Button Class ─────────────────────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, label, value=None, accent=None):
        self.rect    = pygame.Rect(x, y, w, h)
        self.label   = label
        self.value   = value
        self.accent  = accent  # optional override color when active
        self.active  = False
        self.hovered = False

    def draw(self, win):
        if self.active:
            bg  = self.accent if self.accent else BTN_ACTIVE
            bc  = (220, 180, 50)
            lc  = BTN_TEXT
            bw  = 2
        elif self.hovered:
            bg  = BTN_HOVER
            bc  = BTN_BORDER
            lc  = TEXT_WHITE
            bw  = 1
        else:
            bg  = BTN_IDLE
            bc  = BTN_BORDER
            lc  = BTN_TEXT_MUTED
            bw  = 1

        pygame.draw.rect(win, bg,  self.rect, border_radius=7)
        pygame.draw.rect(win, bc,  self.rect, bw, border_radius=7)

        txt = F_LABEL.render(self.label, True, lc)
        win.blit(txt, txt.get_rect(center=self.rect.center))

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(pos))


# ─── Node Class ───────────────────────────────────────────────────────────────
class Node:
    def __init__(self, row, col, width, total_rows):
        self.row = row; self.col = col
        self.x = col * width; self.y = row * width
        self.color = C_EMPTY; self.width = width
        self.total_rows = total_rows; self.neighbors = []

    def __lt__(self, other): return False
    def get_pos(self):    return self.row, self.col
    def is_closed(self):  return self.color == C_CLOSED
    def is_open(self):    return self.color == C_OPEN
    def is_barrier(self): return self.color == C_WALL
    def is_start(self):   return self.color == C_START
    def is_end(self):     return self.color == C_END
    def reset(self):        self.color = C_EMPTY
    def make_start(self):   self.color = C_START
    def make_closed(self):  self.color = C_CLOSED
    def make_open(self):    self.color = C_OPEN
    def make_barrier(self): self.color = C_WALL
    def make_end(self):     self.color = C_END
    def make_path(self):    self.color = C_PATH

    def draw(self, win):
        pygame.draw.rect(win, self.color, (self.x, self.y, self.width, self.width))

    def update_neighbors(self, grid):
        self.neighbors = []
        if self.row < self.total_rows-1 and not grid[self.row+1][self.col].is_barrier():
            self.neighbors.append(grid[self.row+1][self.col])
        if self.row > 0 and not grid[self.row-1][self.col].is_barrier():
            self.neighbors.append(grid[self.row-1][self.col])
        if self.col < self.total_rows-1 and not grid[self.row][self.col+1].is_barrier():
            self.neighbors.append(grid[self.row][self.col+1])
        if self.col > 0 and not grid[self.row][self.col-1].is_barrier():
            self.neighbors.append(grid[self.row][self.col-1])


# ─── Heuristics ───────────────────────────────────────────────────────────────
def h_manhattan(p1, p2):
    r1,c1=p1; r2,c2=p2
    return abs(r1-r2)+abs(c1-c2)

def h_euclidean(p1, p2):
    r1,c1=p1; r2,c2=p2
    return math.sqrt((r1-r2)**2+(c1-c2)**2)

def reconstruct_path(came_from, current, draw):
    path = []
    while current in came_from:
        path.append(current)
        current = came_from[current]
        current.make_path()
        draw()
    return path

def algorithm(draw, grid, start, end, algo_type, heuristic_type):
    start_time = time.time()
    count = 0
    open_set = PriorityQueue()
    open_set.put((0, count, start))
    came_from = {}
    g_score = {node: float("inf") for row in grid for node in row}
    g_score[start] = 0
    f_score = {node: float("inf") for row in grid for node in row}
    hfn = h_manhattan if heuristic_type == 'manhattan' else h_euclidean
    f_score[start] = hfn(start.get_pos(), end.get_pos())
    open_set_hash = {start}
    nodes_expanded = 0
    MOVEMENT_COST = 1  # VIVA: change this to add weighted movement

    while not open_set.empty():
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit()
        current = open_set.get()[2]
        open_set_hash.remove(current)
        nodes_expanded += 1
        if current == end:
            path = reconstruct_path(came_from, end, draw)
            end.make_end(); start.make_start()
            return True, nodes_expanded, g_score[end], (time.time()-start_time)*1000, path
        for neighbor in current.neighbors:
            temp_g = g_score[current] + MOVEMENT_COST
            if temp_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = temp_g
                h_val = hfn(neighbor.get_pos(), end.get_pos())
                f_score[neighbor] = h_val if algo_type=='gbfs' else temp_g+h_val
                if neighbor not in open_set_hash:
                    count += 1
                    open_set.put((f_score[neighbor], count, neighbor))
                    open_set_hash.add(neighbor)
                    neighbor.make_open()
        draw()
        if current != start: current.make_closed()
    return False, nodes_expanded, 0, (time.time()-start_time)*1000, []


# ─── Grid Helpers ─────────────────────────────────────────────────────────────
def make_grid(rows, width):
    gap = width // rows
    return [[Node(i,j,gap,rows) for j in range(rows)] for i in range(rows)]

def draw_grid_lines(win, rows, width):
    gap = width // rows
    for i in range(rows):
        pygame.draw.line(win, GRID_LINE, (0,i*gap),(width,i*gap))
    for j in range(rows):
        pygame.draw.line(win, GRID_LINE, (j*gap,0),(j*gap,WIN_HEIGHT))

def get_clicked_pos(pos, rows, width):
    gap = width // rows
    x, y = pos
    return min(y//gap, rows-1), min(x//gap, rows-1)

def generate_random_map(grid, rows, density=0.3):
    for row in grid:
        for node in row:
            if not node.is_start() and not node.is_end():
                node.reset()
                if random.random() < density: node.make_barrier()


# ─── Panel Drawing ────────────────────────────────────────────────────────────
def section_header(win, title, x, y, w):
    pygame.draw.line(win, SECTION_LINE, (x, y), (x+w, y), 1)
    lbl = F_HEADING.render(title, True, TEXT_HEADING)
    win.blit(lbl, (x, y+6))
    return y + 24

def legend_dot(win, x, y, color, label):
    # Colored square swatch
    pygame.draw.rect(win, color, (x, y+1, 11, 11), border_radius=2)
    pygame.draw.rect(win, (0,0,0,60), (x, y+1, 11, 11), 1, border_radius=2)
    win.blit(F_SMALL.render(label, True, TEXT_MUTED), (x+15, y))

def draw_panel(win, buttons, nodes, cost, ex_time, algo, heuri, rows, status_msg):
    px = GRID_WIDTH + 1
    pw = PANEL_WIDTH - 2

    # Panel background
    pygame.draw.rect(win, PANEL_BG, pygame.Rect(px, 0, pw+1, WIN_HEIGHT))
    # Left border gold line
    pygame.draw.line(win, PANEL_BORDER, (px, 0), (px, WIN_HEIGHT), 2)

    cx = px + 14
    cy = 16

    # ── Title ─────────────────────────────────────────────────────────────────
    title1 = F_TITLE.render("PATHFINDER", True, TEXT_HEADING)
    win.blit(title1, (cx, cy)); cy += title1.get_height() + 2
    sub = F_SUB.render("Dynamic AI Navigation Agent", True, TEXT_MUTED)
    win.blit(sub, (cx, cy)); cy += sub.get_height() + 14

    # ── Algorithm ─────────────────────────────────────────────────────────────
    cy = section_header(win, "ALGORITHM", cx, cy, pw-28)
    bw = (pw - 28 - 8) // 2
    for btn in buttons["algo"]: btn.draw(win)
    cy = buttons["algo"][0].rect.bottom + 12

    # ── Heuristic ─────────────────────────────────────────────────────────────
    cy = section_header(win, "HEURISTIC", cx, cy, pw-28)
    for btn in buttons["heuri"]: btn.draw(win)
    cy = buttons["heuri"][0].rect.bottom + 12

    # ── Grid Size ─────────────────────────────────────────────────────────────
    cy = section_header(win, "GRID SIZE", cx, cy, pw-28)
    for btn in buttons["grid"]: btn.draw(win)
    g_lbl = F_MONO.render(f"{rows} × {rows}", True, TEXT_HEADING)
    cx_mid = px + PANEL_WIDTH//2 - g_lbl.get_width()//2 - 7
    win.blit(g_lbl, (cx_mid, buttons["grid"][0].rect.y + 7))
    cy = buttons["grid"][0].rect.bottom + 12

    # ── Controls ──────────────────────────────────────────────────────────────
    cy = section_header(win, "CONTROLS", cx, cy, pw-28)
    for btn in buttons["action"]: btn.draw(win)
    cy = buttons["action"][-1].rect.bottom + 14

    # ── Metrics ───────────────────────────────────────────────────────────────
    cy = section_header(win, "METRICS", cx, cy, pw-28)

    metric_pairs = [
        ("Nodes Expanded", str(nodes)),
        ("Path Cost",      str(cost)),
        ("Exec Time",      f"{ex_time:.1f} ms"),
    ]
    for label, value in metric_pairs:
        lbl_s = F_SMALL.render(label, True, TEXT_MUTED)
        val_s = F_METRIC.render(value, True, TEXT_HEADING)
        win.blit(lbl_s, (cx, cy))
        win.blit(val_s, (cx + pw - val_s.get_width() - 28, cy))
        cy += 18
    cy += 6

    # ── Status ────────────────────────────────────────────────────────────────
    cy = section_header(win, "STATUS", cx, cy, pw-28)
    if status_msg:
        col = STATUS_OK  if ("Found" in status_msg or "placed" in status_msg.lower() or "complete" in status_msg.lower()) else \
              STATUS_ERR if "No path" in status_msg else STATUS_INFO
        # Word wrap
        words = status_msg.split()
        line = ""; lines = []
        for w in words:
            test = line + (" " if line else "") + w
            if F_SMALL.size(test)[0] > pw - 32: lines.append(line); line = w
            else: line = test
        if line: lines.append(line)
        for ln in lines:
            win.blit(F_SMALL.render(ln, True, col), (cx, cy)); cy += 15
    cy += 6

    # ── Legend ────────────────────────────────────────────────────────────────
    cy = section_header(win, "LEGEND", cx, cy, pw-28)
    items = [
        (C_START,  "Start Node"),
        (C_END,    "Goal Node"),
        (C_OPEN,   "Frontier"),
        (C_CLOSED, "Visited"),
        (C_PATH,   "Final Path"),
        (C_WALL,   "Wall"),
    ]
    col1 = cx; col2 = cx + (pw-28)//2 + 4
    for i, (color, label) in enumerate(items):
        lx = col1 if i % 2 == 0 else col2
        legend_dot(win, lx, cy + (i//2)*18, color, label)
    cy += (len(items)//2)*18 + 14

    # ── How to Use ────────────────────────────────────────────────────────────
    cy = section_header(win, "HOW TO USE", cx, cy, pw-28)
    steps = [
        ("1", "Left-click grid → place Start"),
        ("2", "Left-click again → place Goal"),
        ("3", "Left-click to draw Walls"),
        ("4", "Select Algorithm & Heuristic"),
        ("5", "Click Run Search to solve"),
        ("6", "Click Dynamic Mode to watch"),
        ("",  "  agent re-plan around new walls"),
        ("7", "Right-click any node to erase"),
        ("8", "Random Maze fills 30% walls"),
    ]
    for num, text in steps:
        if num:
            num_s  = F_SMALL.render(f"{num}.", True, TEXT_HEADING)
            txt_s  = F_SMALL.render(text, True, TEXT_MUTED)
            win.blit(num_s, (cx, cy))
            win.blit(txt_s, (cx+18, cy))
        else:
            txt_s = F_SMALL.render(text, True, TEXT_MUTED)
            win.blit(txt_s, (cx, cy))
        cy += 14

    # ── Keyboard shortcuts ────────────────────────────────────────────────────
    cy += 4
    pygame.draw.line(win, SECTION_LINE, (cx, cy), (cx+pw-28, cy), 1)
    cy += 6
    for text in ["[Space] Run   [D] Dynamic Mode",
                 "[R] Random Maze   [C] Clear",
                 "[↑] Bigger Grid   [↓] Smaller"]:
        win.blit(F_SMALL.render(text, True, TEXT_MUTED), (cx, cy)); cy += 14


# ─── Full Render ──────────────────────────────────────────────────────────────
def draw_all(win, grid, rows, buttons, nodes=0, cost=0, ex_time=0,
             algo="a*", heuri="manhattan", status_msg=""):
    win.fill(GRID_BG)
    for row in grid:
        for node in row: node.draw(win)
    draw_grid_lines(win, rows, GRID_WIDTH)
    draw_panel(win, buttons, nodes, cost, ex_time, algo, heuri, rows, status_msg)
    pygame.display.update()


# ─── Dynamic Transit ──────────────────────────────────────────────────────────
def dynamic_transit(draw_func, grid, path, start, end, rows, algo, heuri):
    if not path: return
    path.reverse()
    current_idx = 0
    agent_node  = start
    while current_idx < len(path):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit()
        if agent_node != start: agent_node.make_path()
        agent_node = path[current_idx]
        agent_node.make_start()
        if random.random() < 0.10:
            r = random.randint(0, rows-1); c = random.randint(0, rows-1)
            n = grid[r][c]
            if n not in (start, end, agent_node):
                n.make_barrier()
                if n in path[current_idx:]:
                    for row_g in grid:
                        for node in row_g:
                            node.update_neighbors(grid)
                            if node.color in [C_CLOSED,C_OPEN,C_PATH] and node not in (start,end,agent_node):
                                node.reset()
                    success,_,_,_,new_path = algorithm(draw_func,grid,agent_node,end,algo,heuri)
                    if success: return dynamic_transit(draw_func,grid,new_path,agent_node,end,rows,algo,heuri)
                    else: return
        current_idx += 1
        draw_func()
        time.sleep(0.12)


# ─── Build Buttons ────────────────────────────────────────────────────────────
def build_buttons(rows):
    px = GRID_WIDTH + 15
    pw = PANEL_WIDTH - 30
    bw = (pw - 8) // 2

    buttons = {}

    ay = 106
    buttons["algo"] = [
        Button(px,       ay, bw, 30, "A*  Search", "a*",      (200, 155, 30)),
        Button(px+bw+8,  ay, bw, 30, "GBFS",       "gbfs",    (170, 120, 20)),
    ]
    buttons["algo"][0].active = True

    hy = ay + 30 + 30
    buttons["heuri"] = [
        Button(px,       hy, bw, 30, "Manhattan",  "manhattan", (200, 155, 30)),
        Button(px+bw+8,  hy, bw, 30, "Euclidean",  "euclidean", (170, 120, 20)),
    ]
    buttons["heuri"][0].active = True

    gy = hy + 30 + 30
    sw = 38
    buttons["grid"] = [
        Button(px,          gy, sw, 30, "−", "down", (160, 60, 40)),
        Button(px+pw-sw,    gy, sw, 30, "+", "up",   (50, 150, 70)),
    ]

    by = gy + 30 + 30
    buttons["action"] = [
        Button(px, by,      pw, 34, "▶  Run Search",    "run",     (50, 150, 70)),
        Button(px, by+40,   pw, 34, "⬡  Dynamic Mode",  "dynamic", (200, 140, 20)),
        Button(px, by+80,   pw, 28, "⊞  Random Maze",   "random",  (60, 110, 180)),
        Button(px, by+114,  pw, 28, "✕  Clear Board",   "clear",   (160, 60, 40)),
    ]

    return buttons


# ─── Main ─────────────────────────────────────────────────────────────────────
def main(win):
    ROWS = 25
    grid = make_grid(ROWS, GRID_WIDTH)
    buttons = build_buttons(ROWS)

    start = None; end = None; run = True
    nodes_exp = 0; path_cost = 0; exec_time = 0.0
    current_algo = "a*"; current_heuri = "manhattan"
    current_path = []; status_msg = "Place a Start node on the grid"

    while run:
        mouse_pos = pygame.mouse.get_pos()
        for group in buttons.values():
            for btn in group: btn.check_hover(mouse_pos)

        draw_all(win, grid, ROWS, buttons, nodes_exp, path_cost, exec_time,
                 current_algo, current_heuri, status_msg)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: run = False

            # Grid painting
            if pygame.mouse.get_pressed()[0]:
                pos = pygame.mouse.get_pos()
                if pos[0] < GRID_WIDTH:
                    row, col = get_clicked_pos(pos, ROWS, GRID_WIDTH)
                    node = grid[row][col]
                    if not start and node != end:
                        start = node; start.make_start()
                        status_msg = "Start placed — now click Goal position"
                    elif not end and node != start:
                        end = node; end.make_end()
                        status_msg = "Goal placed — draw walls, then Run Search"
                    elif node != start and node != end:
                        node.make_barrier()

            elif pygame.mouse.get_pressed()[2]:
                pos = pygame.mouse.get_pos()
                if pos[0] < GRID_WIDTH:
                    row, col = get_clicked_pos(pos, ROWS, GRID_WIDTH)
                    node = grid[row][col]; node.reset()
                    if node == start:   start = None; status_msg = "Place a Start node"
                    elif node == end:   end = None;   status_msg = "Place a Goal node"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                for btn in buttons["algo"]:
                    if btn.is_clicked(pos, event):
                        for b in buttons["algo"]: b.active = False
                        btn.active = True; current_algo = btn.value

                for btn in buttons["heuri"]:
                    if btn.is_clicked(pos, event):
                        for b in buttons["heuri"]: b.active = False
                        btn.active = True; current_heuri = btn.value

                for btn in buttons["grid"]:
                    if btn.is_clicked(pos, event):
                        if btn.value == "up": ROWS += 5
                        elif btn.value == "down" and ROWS > 10: ROWS -= 5
                        grid = make_grid(ROWS, GRID_WIDTH)
                        buttons = build_buttons(ROWS)
                        for b in buttons["algo"]:  b.active = (b.value == current_algo)
                        for b in buttons["heuri"]: b.active = (b.value == current_heuri)
                        start = None; end = None; current_path = []
                        status_msg = f"Grid resized to {ROWS}×{ROWS}"

                for btn in buttons["action"]:
                    if btn.is_clicked(pos, event):
                        if btn.value == "run" and start and end:
                            for row_g in grid:
                                for node in row_g:
                                    if node.color in [C_PATH,C_CLOSED,C_OPEN] and node not in (start,end): node.reset()
                                    node.update_neighbors(grid)
                            status_msg = f"Running {current_algo.upper()} with {current_heuri.capitalize()}..."
                            draw_all(win,grid,ROWS,buttons,nodes_exp,path_cost,exec_time,current_algo,current_heuri,status_msg)
                            success, nodes_exp, path_cost, exec_time, current_path = algorithm(
                                lambda: draw_all(win,grid,ROWS,buttons,nodes_exp,path_cost,exec_time,current_algo,current_heuri,status_msg),
                                grid, start, end, current_algo, current_heuri)
                            status_msg = f"Path Found!  Cost={path_cost}  Nodes={nodes_exp}" if success else "No path found!"

                        elif btn.value == "dynamic" and start and end and current_path:
                            status_msg = "Dynamic Mode — agent navigating live!"
                            draw_all(win,grid,ROWS,buttons,nodes_exp,path_cost,exec_time,current_algo,current_heuri,status_msg)
                            dynamic_transit(
                                lambda: draw_all(win,grid,ROWS,buttons,nodes_exp,path_cost,exec_time,current_algo,current_heuri,status_msg),
                                grid, current_path, start, end, ROWS, current_algo, current_heuri)
                            status_msg = "Dynamic transit complete"

                        elif btn.value == "random":
                            generate_random_map(grid, ROWS, 0.3)
                            status_msg = "Random maze generated — place Start & Goal"

                        elif btn.value == "clear":
                            start = None; end = None; current_path = []
                            grid = make_grid(ROWS, GRID_WIDTH)
                            nodes_exp = 0; path_cost = 0; exec_time = 0.0
                            status_msg = "Board cleared — place a Start node"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and start and end:
                    for row_g in grid:
                        for node in row_g:
                            if node.color in [C_PATH,C_CLOSED,C_OPEN] and node not in (start,end): node.reset()
                            node.update_neighbors(grid)
                    success, nodes_exp, path_cost, exec_time, current_path = algorithm(
                        lambda: draw_all(win,grid,ROWS,buttons,nodes_exp,path_cost,exec_time,current_algo,current_heuri,status_msg),
                        grid, start, end, current_algo, current_heuri)
                    status_msg = f"Path Found! Cost={path_cost}" if success else "No path found!"

                if event.key == pygame.K_d and start and end and current_path:
                    status_msg = "Dynamic Mode active!"
                    dynamic_transit(
                        lambda: draw_all(win,grid,ROWS,buttons,nodes_exp,path_cost,exec_time,current_algo,current_heuri,status_msg),
                        grid, current_path, start, end, ROWS, current_algo, current_heuri)

                if event.key == pygame.K_r:
                    generate_random_map(grid, ROWS, 0.3); status_msg = "Random maze generated"

                if event.key == pygame.K_c:
                    start=None; end=None; current_path=[]; grid=make_grid(ROWS,GRID_WIDTH)
                    nodes_exp=0; path_cost=0; exec_time=0.0; status_msg="Board cleared"

                if event.key == pygame.K_UP:
                    ROWS+=5; grid=make_grid(ROWS,GRID_WIDTH); buttons=build_buttons(ROWS)
                    for b in buttons["algo"]:  b.active=(b.value==current_algo)
                    for b in buttons["heuri"]: b.active=(b.value==current_heuri)
                    start=None; end=None; current_path=[]

                if event.key == pygame.K_DOWN and ROWS>10:
                    ROWS-=5; grid=make_grid(ROWS,GRID_WIDTH); buttons=build_buttons(ROWS)
                    for b in buttons["algo"]:  b.active=(b.value==current_algo)
                    for b in buttons["heuri"]: b.active=(b.value==current_heuri)
                    start=None; end=None; current_path=[]

    pygame.quit()

if __name__ == "__main__":
    main(WIN)