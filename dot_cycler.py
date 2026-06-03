import pygame
import sys

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

font = pygame.font.SysFont(None, 30)


class Button:
    def __init__(self, x, y, w, h, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.active = False

    def draw(self, surface):
        mx, my = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mx, my)
        if self.active:
            color = BTN_ACTIVE
        elif hovered:
            color = BTN_HOVER
        else:
            color = BTN_COLOR
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

# 3x3 dot grid, centered on the right panel
DOT_R = 16
SPACING = 80
grid_ox = 220 + (380 - SPACING * 2) // 2  # right panel starts at x=220
grid_oy = (HEIGHT - SPACING * 2) // 2
grid_cx = grid_ox + SPACING
dots = [(grid_ox + c * SPACING, grid_oy + r * SPACING) for r in range(3) for c in range(3)]

CAUSAL_DOT = 1  # index of 'causal diagram' dot

dot_labels = {0: "orchestrator", 1: "causal diagram", 2: "twin triangle", 3: "bus", 4: "log"}

current = 0
factor_mode = False
current_factor = 1  # 1-9

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if buttons[0].hit(event.pos) and factor_mode:
                factor_mode = False
                buttons[1].active = False
            elif buttons[0].hit(event.pos):
                current = (current + 1) % 9
            elif factor_mode:
                if buttons[1].hit(event.pos):
                    current = (current + 1) % 9
                    current_factor = (current_factor % 9) + 1
                elif buttons[2].hit(event.pos):
                    current = (current - 1) % 9
                    current_factor = ((current_factor - 2) % 9) + 1
            else:
                if buttons[1].hit(event.pos) and current == CAUSAL_DOT:
                    factor_mode = True
                    current = 0
                    current_factor = 1
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

    if not factor_mode and current in dot_labels:
        label = font.render(dot_labels[current], True, GREEN_LIT)
        screen.blit(label, label.get_rect(centerx=grid_cx, bottom=grid_oy - 36))

    if factor_mode:
        label = font.render(dot_labels[CAUSAL_DOT], True, GREEN_LIT)
        screen.blit(label, label.get_rect(centerx=grid_cx, bottom=grid_oy - 36))
        factor_label = font.render(f"factor {current_factor}", True, BTN_TEXT)
        grid_bottom = grid_oy + 2 * SPACING
        screen.blit(factor_label, factor_label.get_rect(centerx=grid_cx, top=grid_bottom + 24))

    pygame.display.flip()
    clock.tick(60)
