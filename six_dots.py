import pygame
import pygame_gui
import sys
import os
import csv
import array
import math

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

WIDTH, HEIGHT = 1000, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Six Dots")

BG = (240, 240, 240)
font = pygame.font.SysFont("couriernew", 14)
small_font = pygame.font.SysFont("couriernew", 11)

DOT_R = 18
DOT_Y = 80
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIXD_DIR = os.path.join(SCRIPT_DIR, "sixd")

labels = ["orchestrator", "causal diagram", "double triangle", "bus", "log", "do"]
colors = [
    (0, 0, 255),
    (80, 210, 120),
    (230, 90, 90),
    (230, 190, 60),
    (180, 100, 220),
    (60, 200, 200),
]

n = len(labels)
spacing = WIDTH // (n + 1)
dot_positions = [(spacing * (i + 1), DOT_Y) for i in range(n)]

KP_MAP = {
    pygame.K_KP1: '1', pygame.K_KP2: '2', pygame.K_KP3: '3',
    pygame.K_KP4: '4', pygame.K_KP5: '5', pygame.K_KP6: '6',
    pygame.K_KP7: '7', pygame.K_KP8: '8', pygame.K_KP9: '9',
}

manager = pygame_gui.UIManager((WIDTH, HEIGHT))

form_panel = None
form_entry = None
form_result = None
clear_entry_next_frame = False


def open_form():
    global form_panel, form_entry
    pw, ph = 660, 140
    form_panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect((WIDTH - pw) // 2, (HEIGHT - ph) // 2, pw, ph),
        manager=manager)
    pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect(10, 8, pw - 20, 36),
        text="Give the problem tree file you want converted to causal diagram and double triangle",
        manager=manager, container=form_panel)
    form_entry = pygame_gui.elements.UITextEntryLine(
        relative_rect=pygame.Rect(10, 52, pw - 110, 40),
        manager=manager, container=form_panel)
    pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(pw - 90, 52, 70, 40),
        text="OK", manager=manager, container=form_panel)
    form_entry.focus()
    form_entry.set_text("")


def close_form():
    global form_panel, form_entry
    if form_panel:
        form_panel.kill()
        form_panel = None
        form_entry = None


active = 0
show_popup = False
combo_text = None
combo_number = 0
csv_lines = []
csv_error = None

dot_explain = {}
try:
    with open(os.path.join(SIXD_DIR, "dotexplain.csv"), encoding="utf-8-sig") as _f:
        for line in _f:
            parts = line.strip().split(";", 1)
            if len(parts) == 2:
                dot_explain[int(parts[0]) - 1] = parts[1].strip()
except FileNotFoundError:
    pass


def load_csv(name):
    global csv_lines, csv_error
    path = os.path.join(SIXD_DIR, name + ".csv")
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        csv_lines = [", ".join(row) for row in rows]
        csv_error = None
    except FileNotFoundError:
        csv_lines = []
        csv_error = f"not found: {path}"


def make_beep():
    rate = 44100
    n = int(rate * 0.12)
    buf = array.array('h', [0] * n)
    for i in range(n):
        t = i / rate
        decay = math.exp(-20 * t)
        buf[i] = int(32767 * decay * math.sin(2 * math.pi * 300 * t))
    return pygame.mixer.Sound(buffer=buf)

beep_sound = make_beep()

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame_gui.UI_BUTTON_PRESSED and form_panel:
            form_result = form_entry.get_text().strip()
            close_form()
            if form_result:
                for search_dir in [SCRIPT_DIR, SIXD_DIR]:
                    for name in [form_result, form_result + ".csv", form_result + ".txt"]:
                        path = os.path.join(search_dir, name)
                        if os.path.isfile(path):
                            with open(path, encoding="utf-8") as _f:
                                csv_lines = [l.rstrip() for l in _f.readlines()]
                            csv_error = None
                            break
                    else:
                        continue
                    break
                else:
                    csv_lines = []
                    csv_error = f"not found: {form_result}"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
            if form_panel:
                close_form()
            else:
                open_form()
                clear_entry_next_frame = True
            continue  # skip manager.process_events so 'q' keydown doesn't reach text entry

        manager.process_events(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                pass
            elif event.key == pygame.K_ESCAPE:
                close_form()
            elif event.key == pygame.K_RIGHT:
                active = (active + 1) % n
                combo_number = 0
                combo_text = None
                csv_lines, csv_error = [], None
                beep_sound.play()
            elif event.key == pygame.K_LEFT:
                active = (active - 1) % n
                combo_number = 0
                combo_text = None
                csv_lines, csv_error = [], None
                beep_sound.play()
            elif event.key == pygame.K_DOWN:
                combo_number = (combo_number % 9) + 1
                combo_text = labels[active].replace(" ", "") + str(combo_number)
                csv_lines, csv_error = [], None
            elif event.key == pygame.K_UP:
                combo_number = ((combo_number - 2) % 9) + 1
                combo_text = labels[active].replace(" ", "") + str(combo_number)
                csv_lines, csv_error = [], None
            elif pygame.K_1 <= event.key <= pygame.K_9:
                combo_text = labels[active].replace(" ", "") + chr(event.key)
                csv_lines, csv_error = [], None
            elif event.key in KP_MAP:
                combo_text = labels[active].replace(" ", "") + KP_MAP[event.key]
                csv_lines, csv_error = [], None
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if combo_text:
                    load_csv(combo_text)

    if clear_entry_next_frame and form_entry:
        form_entry.set_text("")
        clear_entry_next_frame = False

    screen.fill(BG)

    FG = (30, 30, 30)
    FG_BRIGHT = (0, 0, 0)
    RING = (0, 0, 0)

    title = font.render("THIS APP IS FULLY SELF-ORGANIZING", True, FG_BRIGHT)
    screen.blit(title, title.get_rect(centerx=WIDTH // 2, bottom=DOT_Y - 32))

    for i, (x, y) in enumerate(dot_positions):
        r = DOT_R + 4 if i == active else DOT_R
        pygame.draw.circle(screen, colors[i], (x, y), r)
        if i == active:
            pygame.draw.circle(screen, RING, (x, y), r + 4, 2)
        label_surf = font.render(labels[i], True, FG_BRIGHT if i == active else FG)
        screen.blit(label_surf, label_surf.get_rect(centerx=x, top=y + DOT_R + 14))

    content_top = DOT_Y + DOT_R + 44
    if combo_text:
        combo_surf = font.render(combo_text, True, FG)
        screen.blit(combo_surf, combo_surf.get_rect(centerx=WIDTH // 2, top=content_top))
        content_top += 28

    if csv_error:
        err_surf = small_font.render(csv_error, True, (220, 80, 80))
        screen.blit(err_surf, (20, content_top))
    else:
        y_pos = content_top
        for line in csv_lines:
            if y_pos > HEIGHT - 16:
                break
            screen.blit(small_font.render(line, True, FG), (20, y_pos))
            y_pos += 16

    if active in dot_explain:
        explain_surf = small_font.render(dot_explain[active], True, FG)
        screen.blit(explain_surf, explain_surf.get_rect(centerx=WIDTH // 2, bottom=HEIGHT - 28))

    tagline = small_font.render("make it so: turn problem tree into causal diagrams and double triangles", True, FG)
    screen.blit(tagline, tagline.get_rect(centerx=WIDTH // 2, bottom=HEIGHT - 10))

    time_delta = clock.tick(60) / 1000.0
    manager.update(time_delta)
    manager.draw_ui(screen)

    pygame.display.flip()
