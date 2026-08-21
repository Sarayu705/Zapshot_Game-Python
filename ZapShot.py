import math
import random
import time
import pygame
pygame.init()

width, height = 900, 650
win = pygame.display.set_mode((width, height))
pygame.display.set_caption("ZapShot")

TARGET_EVENT = pygame.USEREVENT + 1
TARGET_INCREMENT = 600
TARGET_PADDING = 40
bg_color = (10, 10, 20)
top_bar_height = 70
bottom_bar_height = 0

# Fonts
try:
    titleFont = pygame.font.SysFont("impact", 52)
    labelFont = pygame.font.SysFont("verdana", 18)
    smallFont = pygame.font.SysFont("verdana", 14)
    btnFont = pygame.font.SysFont("impact", 22)
except:
    titleFont = pygame.font.SysFont("comicsans", 52)
    labelFont = pygame.font.SysFont("comicsans", 18)
    smallFont = pygame.font.SysFont("comicsans", 14)
    btnFont = pygame.font.SysFont("comicsans", 22)

game_duration = 60

import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

try:
    pop_sound = pygame.mixer.Sound(resource_path("pop.wav"))
except Exception:
    pop_sound = None

POWERUP_TYPES = ["extra_time", "slow_motion", "double_score", "extra_life"]
POWERUP_LABELS = {
    "extra_time": "+5s",
    "slow_motion": "SLOW",
    "double_score": "2×",
    "extra_life": "+♥"
}
POWERUP_COLORS = {
    "extra_time": (60, 200, 220),
    "slow_motion": (190, 80, 230),
    "double_score": (240, 200, 30),
    "extra_life": (60, 200, 80)
}

# ── Button ──────────────────────────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, color, hover_color, text_color=(255,255,255)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False

    def draw(self, win):
        col = self.hover_color if self.hovered else self.color
        pygame.draw.rect(win, col, self.rect, border_radius=10)
        pygame.draw.rect(win, (255,255,255,80), self.rect, width=2, border_radius=10)
        label = btnFont.render(self.text, True, self.text_color)
        win.blit(label, (self.rect.centerx - label.get_width()//2,
                         self.rect.centery - label.get_height()//2))

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ── Target ───────────────────────────────────────────────────────────────────
class Target:
    def __init__(self, x, y, color="red", secondColor="white", maxSize=40,
                 growthRate=0.2, target_type=None, is_powerup=False):
        self.x = x
        self.y = y
        self.color = color
        self.secondColor = secondColor
        self.maxSize = maxSize
        self.growthRate = growthRate
        self.size = 0
        self.grow = True
        self.is_blue = False
        self.is_powerup = is_powerup
        self.target_type = target_type
        self.label = POWERUP_LABELS.get(target_type, "") if is_powerup else ""

    def update(self, speed_multiplier=1):
        step = self.growthRate * speed_multiplier
        if self.size + step >= self.maxSize:
            self.grow = False
        if self.grow:
            self.size += step
        else:
            self.size -= step

    def draw(self, win):
        r = int(self.size)
        pygame.draw.circle(win, self.color,       (self.x, self.y), r)
        pygame.draw.circle(win, self.secondColor, (self.x, self.y), int(r * 0.78))
        pygame.draw.circle(win, self.color,       (self.x, self.y), int(r * 0.58))
        pygame.draw.circle(win, self.secondColor, (self.x, self.y), int(r * 0.38))
        if self.is_powerup and self.label:
            lbl = smallFont.render(self.label, True, self.secondColor)
            win.blit(lbl, (self.x - lbl.get_width()//2, self.y - r - 18))

    def collide(self, x, y):
        return math.hypot(x - self.x, y - self.y) <= self.size


# ── Drawing helpers ──────────────────────────────────────────────────────────
def draw_background(win):
    win.fill(bg_color)
    grid_color = (22, 22, 38)
    for x in range(0, width, 50):
        pygame.draw.line(win, grid_color, (x, top_bar_height), (x, height), 1)
    for y in range(top_bar_height, height, 50):
        pygame.draw.line(win, grid_color, (0, y), (width, y), 1)


def format_time(secs):
    milli = math.floor(int(secs * 1000 % 1000) / 100)
    seconds = int(round(secs % 60, 1))
    minutes = int(secs // 60)
    return f"{minutes:02d}:{seconds:02d}.{milli}"


def draw_top_bar(win, remaining_time, score, hits, clicks, lives, slow_end, double_end):
    # Background
    pygame.draw.rect(win, (15, 15, 30), (0, 0, width, top_bar_height))
    pygame.draw.line(win, (255, 80, 80), (0, top_bar_height), (width, top_bar_height), 2)

    now = time.time()
    # --- Segments: Time | Score | Hits | Acc | Lives | Effects ---
    # Divide bar into 6 equal cells
    cells = 6
    cw = width // cells
    cy = top_bar_height // 2

    def stat_block(index, label_text, value_text, val_color=(255,255,255)):
        cx = index * cw + cw // 2
        lbl = smallFont.render(label_text, True, (140, 140, 180))
        val = labelFont.render(value_text, True, val_color)
        win.blit(lbl, (cx - lbl.get_width()//2, cy - 24))
        win.blit(val, (cx - val.get_width()//2, cy - 2))

    acc = round(hits / clicks * 100, 1) if clicks > 0 else 0.0
    time_color = (255, 80, 80) if remaining_time < 10 else (255, 255, 255)

    stat_block(0, "TIME",     format_time(remaining_time), time_color)
    stat_block(1, "SCORE",    str(score),   (255, 220, 80))
    stat_block(2, "HITS",     str(hits),    (100, 220, 255))
    stat_block(3, "ACCURACY", f"{acc}%",    (180, 255, 180))
    stat_block(4, "LIVES",    "♥ " * max(0, lives) if lives <= 6 else f"♥ ×{lives}", (255, 80, 120))

    # Effects cell
    effects = []
    if now < slow_end:   effects.append("SLOW")
    if now < double_end: effects.append("2×")
    eff_text = " | ".join(effects) if effects else "—"
    eff_color = (130, 255, 130) if effects else (80, 80, 100)
    stat_block(5, "EFFECTS", eff_text, eff_color)

    # Dividers
    for i in range(1, cells):
        pygame.draw.line(win, (40, 40, 60), (i*cw, 6), (i*cw, top_bar_height-6), 1)


def draw_menu(win, buttons):
    draw_background(win)

    # Title glow effect
    glow = titleFont.render("ZAPSHOT", True, (255, 40, 40))
    title = titleFont.render("ZAPSHOT", True, (255, 255, 255))
    win.blit(glow,  (width//2 - glow.get_width()//2 + 2, 82))
    win.blit(title, (width//2 - title.get_width()//2, 80))

    sub = labelFont.render("Click targets. Beat the clock. Don't miss.", True, (160, 160, 200))
    win.blit(sub, (width//2 - sub.get_width()//2, 148))

    # Instructions box
    box = pygame.Rect(width//2 - 280, 190, 560, 160)
    pygame.draw.rect(win, (20, 20, 40), box, border_radius=12)
    pygame.draw.rect(win, (50, 50, 100), box, width=1, border_radius=12)
    tips = [
        "🔴  Red targets  →  +1 point",
        "🔵  Blue targets  →  +10 points",
        "🟡  Power-ups  →  +5s / Slow / 2× / Extra Life",
        "💀  Miss a target  →  lose a life (5 to start)",
    ]
    for i, tip in enumerate(tips):
        t = smallFont.render(tip, True, (200, 200, 230))
        win.blit(t, (box.x + 20, box.y + 18 + i * 32))

    for btn in buttons:
        btn.draw(win)

    pygame.display.update()


def draw_pause_screen(win, buttons, slow_end, double_end):
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    win.blit(overlay, (0, 0))

    title = titleFont.render("PAUSED", True, (255, 220, 80))
    win.blit(title, (width//2 - title.get_width()//2, 180))

    now = time.time()
    effects = []
    if now < slow_end:   effects.append("Slow Motion")
    if now < double_end: effects.append("Double Score")
    if effects:
        eff = labelFont.render("Active: " + " + ".join(effects), True, (130, 255, 130))
        win.blit(eff, (width//2 - eff.get_width()//2, 260))

    for btn in buttons:
        btn.draw(win)

    pygame.display.update()


def draw_game(win, targets, combo_text, combo_display_time, remaining_time, score, hits, clicks, lives, slow_end, double_end, pause_btn):
    draw_background(win)
    for target in targets:
        target.draw(win)

    now = time.time()
    if combo_text and now - combo_display_time < 1.2:
        alpha = max(0, int(255 * (1.2 - (now - combo_display_time)) / 1.2))
        surf = labelFont.render(combo_text, True, (255, 220, 80))
        surf.set_alpha(alpha)
        win.blit(surf, (width//2 - surf.get_width()//2, top_bar_height + 18))

    draw_top_bar(win, remaining_time, score, hits, clicks, lives, slow_end, double_end)
    pause_btn.draw(win)
    pygame.display.update()


def draw_end_screen(win, elapsed, hits, clicks, score, lives, buttons):
    draw_background(win)

    title = titleFont.render("GAME OVER", True, (255, 60, 60))
    win.blit(title, (width//2 - title.get_width()//2, 80))

    acc = round(hits / clicks * 100, 1) if clicks > 0 else 0
    stats = [
        ("Time Survived", format_time(elapsed)),
        ("Final Score",   str(score)),
        ("Targets Hit",   str(hits)),
        ("Accuracy",      f"{acc}%"),
        ("Lives Left",    str(max(0, lives))),
    ]

    box = pygame.Rect(width//2 - 220, 160, 440, 220)
    pygame.draw.rect(win, (18, 18, 35), box, border_radius=14)
    pygame.draw.rect(win, (80, 40, 40), box, width=2, border_radius=14)

    for i, (k, v) in enumerate(stats):
        ky = labelFont.render(k, True, (150, 150, 190))
        vy = labelFont.render(v, True, (255, 255, 255))
        y = box.y + 22 + i * 38
        win.blit(ky, (box.x + 30, y))
        win.blit(vy, (box.right - vy.get_width() - 30, y))

    for btn in buttons:
        btn.draw(win)

    pygame.display.update()


def get_middle(surface):
    return width // 2 - surface.get_width() // 2


def spawn_target():
    x = random.randint(TARGET_PADDING, width - TARGET_PADDING)
    y = random.randint(TARGET_PADDING + top_bar_height, height - TARGET_PADDING)
    if random.random() < 0.18:
        powerup_type = random.choice(POWERUP_TYPES)
        color = POWERUP_COLORS[powerup_type]
        return Target(x, y, color=color, secondColor="white", maxSize=28, growthRate=0.35,
                      target_type=powerup_type, is_powerup=True)
    if random.random() < 0.25:
        t = Target(x, y, color=(30, 120, 255), secondColor="white", maxSize=25, growthRate=0.4)
        t.is_blue = True
        return t
    return Target(x, y)


def reset_state():
    return dict(
        targets=[], zapshots=0, clicks=0, score=0,
        current_combo=0, combo_text="", combo_display_time=0,
        start_time=time.time(), bonus_time=0, lives=5,
        slow_motion_end=0, double_score_end=0
    )


def main():
    run = True
    state = "menu"
    clock = pygame.time.Clock()
    gs = reset_state()
    gs["start_time"] = 0  # not started yet

    pygame.time.set_timer(TARGET_EVENT, TARGET_INCREMENT)

    # ── Build buttons ────────────────────────────────────────────────────────
    BW, BH = 180, 48
    cx = width // 2

    menu_start_btn = Button(cx - BW//2, 380, BW, BH, "▶  START", (200, 40, 40), (255, 80, 80))
    menu_quit_btn  = Button(cx - BW//2, 445, BW, BH, "✕  QUIT",  (40, 40, 70),  (80, 80, 120))
    menu_buttons   = [menu_start_btn, menu_quit_btn]

    pause_resume_btn = Button(cx - BW//2, 310, BW, BH, "▶  RESUME", (50, 160, 80), (80, 200, 110))
    pause_quit_btn   = Button(cx - BW//2, 375, BW, BH, "✕  QUIT",   (140, 30, 30), (200, 60, 60))
    pause_buttons    = [pause_resume_btn, pause_quit_btn]

    # Pause button shown in-game (top-right area, after top bar)
    ingame_pause_btn = Button(width - 100, 12, 86, 46, "⏸ PAUSE", (40, 40, 80), (80, 80, 140))

    end_restart_btn = Button(cx - BW//2, 408, BW, BH, "↺  PLAY AGAIN", (200, 40, 40), (255, 80, 80))
    end_quit_btn    = Button(cx - BW//2, 472, BW, BH, "✕  QUIT",       (40, 40, 70),  (80, 80, 120))
    end_buttons     = [end_restart_btn, end_quit_btn]

    remaining_time = game_duration
    elapsed_for_end = 0

    while run:
        clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()
        click = False
        now = time.time()

        # Update hover
        if state == "menu":
            for b in menu_buttons: b.check_hover(mouse_pos)
        elif state == "pause":
            for b in pause_buttons: b.check_hover(mouse_pos)
        elif state == "play":
            ingame_pause_btn.check_hover(mouse_pos)
        elif state == "end":
            for b in end_buttons: b.check_hover(mouse_pos)

        if state == "play":
            elapsed_time = now - gs["start_time"]
            remaining_time = max(0, game_duration + gs["bonus_time"] - elapsed_time)
        else:
            remaining_time = game_duration

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                if state == "menu":
                    if menu_start_btn.is_clicked(pos):
                        gs = reset_state()
                        state = "play"
                    elif menu_quit_btn.is_clicked(pos):
                        run = False

                elif state == "pause":
                    if pause_resume_btn.is_clicked(pos):
                        state = "play"
                    elif pause_quit_btn.is_clicked(pos):
                        run = False

                elif state == "end":
                    if end_restart_btn.is_clicked(pos):
                        gs = reset_state()
                        state = "play"
                    elif end_quit_btn.is_clicked(pos):
                        run = False

                elif state == "play":
                    if ingame_pause_btn.is_clicked(pos):
                        state = "pause"
                    else:
                        click = True
                        gs["clicks"] += 1

            if state == "play":
                if event.type == TARGET_EVENT:
                    gs["targets"].append(spawn_target())
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    state = "pause"

            elif state == "pause":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    state = "play"

        if not run:
            break

        if state == "menu":
            draw_menu(win, menu_buttons)
            continue

        if state == "pause":
            draw_game(win, gs["targets"], gs["combo_text"], gs["combo_display_time"],
                      remaining_time, gs["score"], gs["zapshots"], gs["clicks"],
                      gs["lives"], gs["slow_motion_end"], gs["double_score_end"], ingame_pause_btn)
            draw_pause_screen(win, pause_buttons, gs["slow_motion_end"], gs["double_score_end"])
            continue

        if state == "end":
            draw_end_screen(win, elapsed_for_end, gs["zapshots"], gs["clicks"],
                            gs["score"], gs["lives"], end_buttons)
            continue

        # ── Play state ─────────────────────────────────────────────────────
        speed_multiplier = 0.55 if now < gs["slow_motion_end"] else 1.0

        for target in gs["targets"][:]:
            target.update(speed_multiplier)

            if target.size <= 0:
                gs["targets"].remove(target)
                gs["current_combo"] = 0
                if not target.is_powerup:
                    gs["lives"] -= 1
                    gs["combo_text"] = "Missed! −1 Life"
                    gs["combo_display_time"] = now
                continue

            if click and target.collide(*mouse_pos):
                if pop_sound: pop_sound.play()
                gs["targets"].remove(target)
                gs["zapshots"] += 1
                gs["current_combo"] += 1
                click = False

                if target.is_powerup:
                    if target.target_type == "extra_time":
                        gs["bonus_time"] += 5
                        gs["combo_text"] = "+5 seconds! ⏱"
                    elif target.target_type == "slow_motion":
                        gs["slow_motion_end"] = now + 5
                        gs["combo_text"] = "Slow Motion! 🐢"
                    elif target.target_type == "double_score":
                        gs["double_score_end"] = now + 8
                        gs["combo_text"] = "Double Score! 2×"
                    elif target.target_type == "extra_life":
                        gs["lives"] += 1
                        gs["combo_text"] = "+1 Life! ♥"
                    gs["combo_display_time"] = now
                    gs["current_combo"] = 0
                    continue

                base = 10 if target.is_blue else 1
                mult = 2 if now < gs["double_score_end"] else 1
                gs["score"] += base * mult

                if gs["current_combo"] == 5:
                    gs["score"] += 5
                    gs["combo_text"] = "Combo ×5! +5 bonus"
                    gs["combo_display_time"] = now
                elif gs["current_combo"] == 10:
                    gs["score"] += 10
                    gs["combo_text"] = "Combo ×10! +10 bonus"
                    gs["combo_display_time"] = now

        if gs["lives"] <= 0 or remaining_time <= 0:
            elapsed_for_end = now - gs["start_time"]
            state = "end"
            continue

        draw_game(win, gs["targets"], gs["combo_text"], gs["combo_display_time"],
                  remaining_time, gs["score"], gs["zapshots"], gs["clicks"],
                  gs["lives"], gs["slow_motion_end"], gs["double_score_end"], ingame_pause_btn)

    pygame.quit()


main()