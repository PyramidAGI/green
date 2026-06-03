import pygame
import sys
import os
import csv

pygame.init()

WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dot Cycler")

BG = (30, 30, 30)
PANEL_DIV = (80, 80, 80)
BTN_COLOR = (70, 70, 90)
BTN_ACTIVE = (60, 120, 200)
BTN_HOVER = (90, 90, 110)
BTN_TEXT = (220, 220, 220)
GREEN_DIM = (30, 130, 30)
GREEN_LIT = (50, 255, 80)
WHITE = (255, 255, 255)
RED_TEXT = (220, 80, 80)

font = pygame.font.SysFont(None, 30)
small_font = pygame.font.SysFont("couriernew", 12)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class Button:
    def __init__(self, x, y, w, h, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.active = False

    def draw(self, surface):
        mx, my = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mx, my)
        color = BTN_HOVER if hovered else BTN_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, PANEL_DIV, self.rect, 2, border_radius=8)
        txt = font.render(self.label, True, BTN_TEXT)
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def hit(self, pos):
        return self.rect.collidepoint(pos)


# Layout
btn_w, btn_h = 130, 44
left_cx = 90
buttons = [
    Button(left_cx - btn_w // 2, 120, btn_w, btn_h, "Button 1"),
    Button(left_cx - btn_w // 2, 185, btn_w, btn_h, "Button 2"),
    Button(left_cx - btn_w // 2, 250, btn_w, btn_h, "Button 3"),
]

# 3x3 dot grid
DOT_R = 16
SPACING = 80
grid_ox = 220 + (380 - SPACING * 2) // 2
grid_oy = (HEIGHT - SPACING * 2) // 2
grid_cx = grid_ox + SPACING
grid_bottom = grid_oy + 2 * SPACING
dots = [(grid_ox + c * SPACING, grid_oy + r * SPACING) for r in range(3) for c in range(3)]

ORCHESTRATOR_DOT = 0
CAUSAL_DOT = 1
TRIANGLE_DOT = 2

dot_labels = {0: "orchestrator", 1: "causal diagram", 2: "twin triangle", 3: "bus", 4: "log"}
triangle_node_labels = {6: "sensor", 8: "actuator"}
_node_indices = [i for i in range(9) if i not in triangle_node_labels]
triangle_node_numbers = {dot: n + 1 for n, dot in enumerate(_node_indices)}

current = 0
orchestrator_mode = False
current_orchestrator = 1
factor_mode = False
current_factor = 1
triangle_mode = False

csv_lines = []
csv_error = None
pinned_word = None


def get_bottom_word():
    if orchestrator_mode:
        return f"orchestrator {current_orchestrator}"
    if factor_mode:
        return f"factor {current_factor}"
    if triangle_mode:
        return triangle_node_labels[current] if current in triangle_node_labels else f"node {triangle_node_numbers[current]}"
    return None


def load_csv(word):
    global csv_lines, csv_error, pinned_word
    filename = word.replace(" ", "") + ".csv"
    path = os.path.join(SCRIPT_DIR, filename)
    pinned_word = filename
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        csv_lines = [", ".join(row) for row in rows]
        csv_error = None
    except FileNotFoundError:
        csv_lines = []
        csv_error = f"not found: {filename}"


clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Button 3: read CSV if a bottom word is showing
            if buttons[2].hit(event.pos):
                word = get_bottom_word()
                if word:
                    load_csv(word)
                elif orchestrator_mode:
                    current = (current - 1) % 9
                    current_orchestrator = ((current_orchestrator - 2) % 9) + 1
                elif triangle_mode:
                    current = (current - 1) % 9
                elif factor_mode:
                    current = (current - 1) % 9
                    current_factor = ((current_factor - 2) % 9) + 1
                continue

            if buttons[0].hit(event.pos) and orchestrator_mode:
                pinned_word = get_bottom_word()
                orchestrator_mode = False
                buttons[1].active = False
                csv_lines, csv_error = [], None
            elif buttons[0].hit(event.pos) and factor_mode:
                pinned_word = get_bottom_word()
                factor_mode = False
                buttons[1].active = False
                csv_lines, csv_error = [], None
            elif buttons[0].hit(event.pos) and triangle_mode:
                pinned_word = get_bottom_word()
                triangle_mode = False
                buttons[1].active = False
                csv_lines, csv_error = [], None
            elif buttons[0].hit(event.pos):
                current = (current + 1) % 9
            elif orchestrator_mode:
                if buttons[1].hit(event.pos):
                    current = (current + 1) % 9
                    current_orchestrator = (current_orchestrator % 9) + 1
            elif factor_mode:
                if buttons[1].hit(event.pos):
                    current = (current + 1) % 9
                    current_factor = (current_factor % 9) + 1
            elif triangle_mode:
                if buttons[1].hit(event.pos):
                    current = (current + 1) % 9
            else:
                if buttons[1].hit(event.pos) and current == ORCHESTRATOR_DOT:
                    orchestrator_mode = True
                    current = 0
                    current_orchestrator = 1
                    buttons[1].active = True
                elif buttons[1].hit(event.pos) and current == CAUSAL_DOT:
                    factor_mode = True
                    current = 0
                    current_factor = 1
                    buttons[1].active = True
                elif buttons[1].hit(event.pos) and current == TRIANGLE_DOT:
                    triangle_mode = True
                    current = 0
                    buttons[1].active = True

    screen.fill(BG)
    pygame.draw.line(screen, PANEL_DIV, (210, 20), (210, HEIGHT - 20), 2)

    for btn in buttons:
        btn.draw(screen)

    for i, (x, y) in enumerate(dots):
        lit = i == current
        color = GREEN_LIT if lit else GREEN_DIM
        r = DOT_R + 4 if lit else DOT_R
        pygame.draw.circle(screen, color, (x, y), r)
        if lit:
            pygame.draw.circle(screen, (150, 255, 150), (x, y), r + 4, 2)

    # Pinned word in red, always shown below the current bottom word
    if pinned_word:
        pinned_surf = font.render(pinned_word, True, RED_TEXT)
        screen.blit(pinned_surf, pinned_surf.get_rect(centerx=grid_cx, top=grid_bottom + 54))

    # Top label (above grid)
    if not orchestrator_mode and not factor_mode and not triangle_mode and current in dot_labels:
        label = font.render(dot_labels[current], True, GREEN_LIT)
        screen.blit(label, label.get_rect(centerx=grid_cx, bottom=grid_oy - 36))

    if orchestrator_mode:
        label = font.render(dot_labels[ORCHESTRATOR_DOT], True, GREEN_LIT)
        screen.blit(label, label.get_rect(centerx=grid_cx, bottom=grid_oy - 36))
        orch_label = font.render(f"orchestrator {current_orchestrator}", True, BTN_TEXT)
        screen.blit(orch_label, orch_label.get_rect(centerx=grid_cx, top=grid_bottom + 24))

    if factor_mode:
        label = font.render(dot_labels[CAUSAL_DOT], True, GREEN_LIT)
        screen.blit(label, label.get_rect(centerx=grid_cx, bottom=grid_oy - 36))
        factor_label = font.render(f"factor {current_factor}", True, BTN_TEXT)
        screen.blit(factor_label, factor_label.get_rect(centerx=grid_cx, top=grid_bottom + 24))

    if triangle_mode:
        label = font.render(dot_labels[TRIANGLE_DOT], True, GREEN_LIT)
        screen.blit(label, label.get_rect(centerx=grid_cx, bottom=grid_oy - 36))
        node_text = triangle_node_labels[current] if current in triangle_node_labels else f"node {triangle_node_numbers[current]}"
        node_label = font.render(node_text, True, BTN_TEXT)
        screen.blit(node_label, node_label.get_rect(centerx=grid_cx, top=grid_bottom + 24))

    # CSV content in left panel below buttons
    if csv_error:
        err_surf = small_font.render(csv_error, True, RED_TEXT)
        screen.blit(err_surf, (10, 310))
    elif csv_lines:
        y_pos = 310
        for line in csv_lines:
            if y_pos > HEIGHT - 16:
                break
            line_surf = small_font.render(line, True, BTN_TEXT)
            screen.blit(line_surf, (10, y_pos))
            y_pos += 20

    pygame.display.flip()
    clock.tick(60)
