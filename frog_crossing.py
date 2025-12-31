import sys
import random
from dataclasses import dataclass
from pathlib import Path
import math
import asyncio
import traceback

import pygame


WIDTH, HEIGHT = 900, 640
FPS = 60
HUD_H = 44

# Touch controls (shown on web/mobile)
TOUCH_UI = True

# Grid-ish hop size (frog moves in steps)
STEP_X = 50
STEP_Y = 52
WALK_SPEED = 3.2

# If you are using pixel-art sprites, nearest-neighbor scaling looks better
# and avoids white halos when keying out flat backgrounds.
PIXEL_ART_SPRITES = True

# Sprite-only scale factors
# Croc: wider and taller than its hitbox for a more dramatic sprite.
CROC_SPRITE_SCALE_X = 3
CROC_SPRITE_SCALE_Y = 6  # 3x bigger, then 2x taller

# Frog: make sprite larger without changing hitbox.
FROG_SPRITE_SCALE_X = 2
FROG_SPRITE_SCALE_Y = 2

# Fly: make sprite larger without changing hitbox.
FLY_SPRITE_SCALE_X = 4
FLY_SPRITE_SCALE_Y = 4

# Colors
WATER = (50, 110, 180)
BANK = (30, 160, 70)
LOG = (139, 84, 48)
LILYPAD = (60, 170, 90)
CROC = (25, 120, 55)
WHITE = (245, 245, 245)
BLACK = (15, 15, 15)
FLY = (20, 20, 20)
TEXT = (10, 10, 10)


class SpriteBank:
    def __init__(self, assets_dir: Path):
        self.assets_dir = assets_dir
        self._base: dict[str, pygame.Surface] = {}
        self._scaled: dict[tuple[str, int, int], pygame.Surface] = {}
        self._rotated: dict[tuple[str, int, int, int], pygame.Surface] = {}

    def _load_png(self, name: str) -> pygame.Surface | None:
        path = self.assets_dir / f"{name}.png"
        if not path.exists():
            return None
        try:
            img = pygame.image.load(str(path)).convert_alpha()

            # If the sprite was saved without transparency (common "white box"),
            # try to auto-key out a flat background color.
            # Heuristic: if all 4 corners match and alpha is fully opaque, use that as colorkey.
            w, h = img.get_width(), img.get_height()
            if w >= 2 and h >= 2:
                c1 = img.get_at((0, 0))
                c2 = img.get_at((w - 1, 0))
                c3 = img.get_at((0, h - 1))
                c4 = img.get_at((w - 1, h - 1))
                if c1 == c2 == c3 == c4:
                    r, g, b, a = c1
                    if a == 255:
                        img.set_colorkey((r, g, b))

            return img
        except pygame.error:
            return None

    def _make_placeholder(self, name: str) -> pygame.Surface:
        # Small base sprites; scaled + cached per needed size.
        if name == "frog":
            surf = pygame.Surface((48, 40), pygame.SRCALPHA)
            body = pygame.Rect(6, 10, 36, 24)
            pygame.draw.ellipse(surf, (40, 200, 90), body)
            pygame.draw.ellipse(surf, (20, 120, 60), body, 2)
            pygame.draw.circle(surf, WHITE, (16, 16), 5)
            pygame.draw.circle(surf, WHITE, (32, 16), 5)
            pygame.draw.circle(surf, BLACK, (16, 16), 2)
            pygame.draw.circle(surf, BLACK, (32, 16), 2)
            pygame.draw.arc(surf, (20, 120, 60), (16, 20, 16, 10), 0.2, 2.9, 2)
            return surf

        if name == "croc":
            surf = pygame.Surface((64, 28), pygame.SRCALPHA)
            dark = (18, 90, 42)
            light = (40, 155, 75)
            body = pygame.Rect(8, 8, 40, 14)
            head = pygame.Rect(40, 6, 22, 18)
            snout = pygame.Rect(50, 9, 14, 12)
            tail_pts = [(2, 14), (10, 5), (16, 14), (10, 23)]
            pygame.draw.polygon(surf, dark, tail_pts)
            pygame.draw.rect(surf, CROC, body, border_radius=8)
            pygame.draw.rect(surf, dark, body, 2, border_radius=8)
            pygame.draw.ellipse(surf, CROC, head)
            pygame.draw.ellipse(surf, dark, head, 2)
            pygame.draw.ellipse(surf, light, snout)
            pygame.draw.ellipse(surf, dark, snout, 2)
            pygame.draw.line(surf, dark, (52, 16), (62, 16), 2)
            for tx in range(52, 62, 4):
                pygame.draw.polygon(surf, WHITE, [(tx, 16), (tx + 2, 16), (tx + 1, 19)])
            pygame.draw.circle(surf, WHITE, (44, 10), 3)
            pygame.draw.circle(surf, BLACK, (44, 10), 1)
            pygame.draw.circle(surf, dark, (61, 11), 2)
            return surf

        if name == "fly":
            surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(surf, (30, 30, 30), (12, 12), 6)
            pygame.draw.ellipse(surf, (200, 200, 200, 180), (10, 4, 10, 8))
            pygame.draw.ellipse(surf, (200, 200, 200, 180), (4, 6, 10, 8))
            pygame.draw.circle(surf, (220, 220, 220), (15, 10), 2)
            return surf

        if name == "lilypad":
            surf = pygame.Surface((64, 48), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, LILYPAD, (4, 6, 56, 38))
            pygame.draw.ellipse(surf, (40, 140, 70), (4, 6, 56, 38), 3)
            # notch
            pygame.draw.polygon(surf, (0, 0, 0, 0), [(36, 24), (64, 10), (64, 38)])
            pygame.draw.arc(surf, (40, 140, 70), (10, 12, 44, 30), 0.0, 5.9, 2)
            return surf

        if name == "log":
            surf = pygame.Surface((96, 32), pygame.SRCALPHA)
            base = (139, 84, 48)
            dark = (110, 65, 36)
            pygame.draw.rect(surf, base, (0, 4, 96, 24), border_radius=10)
            pygame.draw.rect(surf, dark, (0, 4, 96, 24), 3, border_radius=10)
            for x in range(10, 92, 14):
                pygame.draw.line(surf, dark, (x, 10), (x + 8, 22), 2)
            pygame.draw.circle(surf, dark, (10, 16), 5)
            pygame.draw.circle(surf, base, (10, 16), 2)
            return surf

        # Fallback generic
        surf = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.rect(surf, (220, 80, 80), surf.get_rect(), border_radius=10)
        return surf

    def base(self, name: str) -> pygame.Surface:
        if name not in self._base:
            img = self._load_png(name)
            self._base[name] = img if img is not None else self._make_placeholder(name)
        return self._base[name]

    def get(self, name: str, size: tuple[int, int]) -> pygame.Surface:
        w, h = size
        w = max(1, int(w))
        h = max(1, int(h))
        key = (name, w, h)
        if key in self._scaled:
            return self._scaled[key]
        img = self.base(name)
        if PIXEL_ART_SPRITES:
            scaled = pygame.transform.scale(img, (w, h))
        else:
            scaled = pygame.transform.smoothscale(img, (w, h))
        self._scaled[key] = scaled
        return scaled

    def get_rotated(self, name: str, size: tuple[int, int], angle_degrees: float, angle_step: int = 5) -> pygame.Surface:
        # Cache rotated + scaled sprites. Bucket angles to keep cache bounded.
        w, h = size
        w = max(1, int(w))
        h = max(1, int(h))
        bucket = int(round(angle_degrees / angle_step)) * angle_step
        bucket %= 360
        key = (name, w, h, bucket)
        if key in self._rotated:
            return self._rotated[key]

        base = self.get(name, (w, h))
        rotated = pygame.transform.rotate(base, bucket)
        self._rotated[key] = rotated
        return rotated


@dataclass
class LevelTuning:
    lane_count: int
    base_speed: float
    platform_count_per_lane: int
    croc_chance: float
    fly_count: int


def tuning_for_level(level: int) -> LevelTuning:
    # Harder each level: faster lanes, more crocs, slightly fewer platforms, more flies.
    lane_count = 8 + min(4, level // 2)  # 8..12 lanes
    base_speed = 1.8 + 0.25 * (level - 1)
    platform_count = max(3, 6 - level // 3)
    croc_chance = min(0.45, 0.10 + 0.04 * (level - 1))
    fly_count = min(6, 2 + level // 2)
    return LevelTuning(
        lane_count=lane_count,
        base_speed=base_speed,
        platform_count_per_lane=platform_count,
        croc_chance=croc_chance,
        fly_count=fly_count,
    )


class Frog:
    def __init__(self, start_pos: pygame.Vector2):
        self.w, self.h = 34, 28
        self.rect = pygame.Rect(0, 0, self.w, self.h)
        self.pos = pygame.Vector2(start_pos)
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self._move_cooldown = 0

    def reset(self, start_pos: pygame.Vector2) -> None:
        self.pos.update(start_pos.x, start_pos.y)
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self._move_cooldown = 10

    def update(self) -> None:
        if self._move_cooldown > 0:
            self._move_cooldown -= 1

    def can_move(self) -> bool:
        return self._move_cooldown <= 0

    def hop(self, dx: int, dy: int) -> None:
        self.pos.x += dx
        self.pos.y += dy
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self._move_cooldown = 6

    def draw(self, surf: pygame.Surface, sprites: SpriteBank) -> None:
        sw = self.rect.width * FROG_SPRITE_SCALE_X
        sh = self.rect.height * FROG_SPRITE_SCALE_Y
        img = sprites.get("frog", (sw, sh))
        dst = img.get_rect(center=self.rect.center)
        surf.blit(img, dst)


class Platform:
    def __init__(self, lane_id: int, lane_y: int, x: float, w: int, h: int, speed: float, kind: str):
        self.kind = kind  # 'log' or 'lilypad'
        self.lane_id = lane_id
        self.rect = pygame.Rect(int(x), int(lane_y - h // 2), w, h)
        self.speed = speed
        self.dx_last = 0

    def update(self) -> None:
        # Keep movement pixel-consistent so riders don't slowly drift due to rounding.
        self.dx_last = int(self.speed)
        self.rect.x += self.dx_last

    def needs_wrap(self) -> bool:
        if self.speed > 0:
            return self.rect.left > WIDTH + 60
        return self.rect.right < -60

    def draw(self, surf: pygame.Surface, sprites: SpriteBank) -> None:
        if self.kind == "log":
            img = sprites.get("log", (self.rect.width, self.rect.height))
            surf.blit(img, self.rect)
        else:
            img = sprites.get("lilypad", (self.rect.width, self.rect.height))
            surf.blit(img, self.rect)


class Crocodile:
    def __init__(self, platform: Platform):
        # Croc rides on a platform, offset a bit
        self.platform = platform
        self.w, self.h = 46, 18
        self.offset_x = 0
        self.rect = pygame.Rect(0, 0, self.w, self.h)
        self._sync()

    def _sync(self) -> None:
        # Center the croc on the log so it reads clearly as "on top".
        self.rect.center = (
            self.platform.rect.centerx + self.offset_x,
            self.platform.rect.centery,
        )

    def update(self) -> None:
        self._sync()

    def draw(self, surf: pygame.Surface, sprites: SpriteBank) -> None:
        sw = self.rect.width * CROC_SPRITE_SCALE_X
        sh = self.rect.height * CROC_SPRITE_SCALE_Y
        img = sprites.get("croc", (sw, sh))
        dst = img.get_rect(center=self.rect.center)
        surf.blit(img, dst)


class Fly:
    def __init__(self, area: pygame.Rect, speed: float):
        self.area = area
        self.pos = pygame.Vector2(
            random.uniform(area.left + 10, area.right - 10),
            random.uniform(area.top + 10, area.bottom - 10),
        )
        angle = random.uniform(0, 6.283)
        self.vel = pygame.Vector2(speed, 0).rotate_rad(angle)
        self.r = 6
        # Sprite faces up by default (eyes at top). Keep last angle if velocity is tiny.
        self.facing_deg = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.pos.x - self.r), int(self.pos.y - self.r), self.r * 2, self.r * 2)

    def update(self) -> None:
        self.pos += self.vel
        # bounce in area
        if self.pos.x < self.area.left + self.r or self.pos.x > self.area.right - self.r:
            self.vel.x *= -1
        if self.pos.y < self.area.top + self.r or self.pos.y > self.area.bottom - self.r:
            self.vel.y *= -1

        if self.vel.length_squared() > 1e-6:
            # Angle from "up" (0,-1) to current velocity.
            self.facing_deg = pygame.Vector2(0, -1).angle_to(self.vel)

    def draw(self, surf: pygame.Surface, sprites: SpriteBank) -> None:
        r = self.r
        sw = r * 2 * FLY_SPRITE_SCALE_X
        sh = r * 2 * FLY_SPRITE_SCALE_Y
        img = sprites.get_rotated("fly", (sw, sh), self.facing_deg, angle_step=10)
        dst = img.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        surf.blit(img, dst)


class FrogCrossingGame:
    def __init__(self) -> None:
        pygame.init()
        flags = pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        pygame.display.set_caption("Frog Crossing")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)

        self.sprites = SpriteBank(Path(__file__).parent / "assets")

        self.is_web = sys.platform == "emscripten"
        self.touch = TouchControls(enabled=TOUCH_UI and self.is_web)

        self.score = 0
        self.level = 1
        self.max_lives = 3
        self.lives = self.max_lives

        self.safe_top = pygame.Rect(0, HUD_H, WIDTH, STEP_Y)
        self.safe_bottom = pygame.Rect(0, HEIGHT - STEP_Y, WIDTH, STEP_Y)
        self.water_area = pygame.Rect(0, HUD_H + STEP_Y, WIDTH, HEIGHT - (HUD_H + 2 * STEP_Y))

        self.start_pos = pygame.Vector2(WIDTH // 2, self.safe_bottom.centery)
        self.frog = Frog(self.start_pos)

        self.platforms: list[Platform] = []
        self.lanes: dict[int, list[Platform]] = {}
        self.crocs: list[Crocodile] = []
        self.flies: list[Fly] = []

        self.last_horizontal_dir = 1

        self._build_level(self.level)

    def _handle_touch_events(self, event: pygame.event.Event) -> None:
        if not self.touch.enabled:
            return

        def to_screen_pos(px: int, py: int) -> tuple[int, int]:
            return px, py

        def to_screen_pos_norm(nx: float, ny: float) -> tuple[int, int]:
            return int(nx * WIDTH), int(ny * HEIGHT)

        if event.type == pygame.FINGERDOWN:
            x, y = to_screen_pos_norm(event.x, event.y)
            self.touch.on_down(x, y)
        elif event.type == pygame.FINGERMOTION:
            x, y = to_screen_pos_norm(event.x, event.y)
            self.touch.on_move(x, y)
        elif event.type == pygame.FINGERUP:
            x, y = to_screen_pos_norm(event.x, event.y)
            self.touch.on_up(x, y)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = to_screen_pos(event.pos[0], event.pos[1])
            self.touch.on_down(x, y)
        elif event.type == pygame.MOUSEMOTION:
            x, y = to_screen_pos(event.pos[0], event.pos[1])
            self.touch.on_move(x, y)
        elif event.type == pygame.MOUSEBUTTONUP:
            x, y = to_screen_pos(event.pos[0], event.pos[1])
            self.touch.on_up(x, y)

    def _lane_centers(self, lane_count: int) -> list[int]:
        # Lanes stacked in water area.
        lane_h = self.water_area.height / lane_count
        centers: list[int] = []
        for i in range(lane_count):
            y = int(self.water_area.top + lane_h * (i + 0.5))
            centers.append(y)
        return centers

    def _build_level(self, level: int) -> None:
        tune = tuning_for_level(level)
        self.platforms.clear()
        self.lanes.clear()
        self.crocs.clear()
        self.flies.clear()

        # Reset lives for the stage
        self.lives = self.max_lives

        lane_centers = self._lane_centers(tune.lane_count)
        lane_h = int(self.water_area.height / tune.lane_count)
        plat_h = max(26, min(34, lane_h - 10))

        # Minimum horizontal gap between platforms in the same lane.
        self.lane_gap = 32

        for i, lane_y in enumerate(lane_centers):
            direction = 1 if i % 2 == 0 else -1
            speed = direction * (tune.base_speed + 0.15 * (i % 3))

            # Mix of logs and lily pads
            count = tune.platform_count_per_lane
            spacing = WIDTH / count
            min_gap = self.lane_gap
            self.lanes[i] = []
            # Build enough platforms so the lane looks populated immediately.
            # If total platform length is shorter than the screen width, you'll otherwise
            # get big empty regions until wrap cycles.
            platforms_in_lane: list[Platform] = []
            def make_platform() -> Platform:
                kind = "log" if random.random() < 0.6 else "lilypad"
                max_w = int(spacing - min_gap)
                if kind == "log":
                    lo = max(80, int(max_w * 0.50))
                    hi = max(80, max_w)
                    w = random.randint(lo, hi)
                else:
                    lo = max(60, int(max_w * 0.35))
                    hi = max(60, int(max_w * 0.75))
                    if hi < lo:
                        hi = lo
                    w = random.randint(lo, hi)
                return Platform(i, lane_y, 0, w, plat_h, speed, kind)

            for _ in range(count):
                platforms_in_lane.append(make_platform())

            def lane_total_len(plats: list[Platform]) -> int:
                if not plats:
                    return 0
                return sum(p.rect.width for p in plats) + self.lane_gap * (len(plats) - 1)

            # Add extras until we cover the screen (plus a little buffer)
            # so multiple platforms are visible immediately.
            target = WIDTH + 240
            extra_limit = 6
            while lane_total_len(platforms_in_lane) < target and extra_limit > 0:
                platforms_in_lane.append(make_platform())
                extra_limit -= 1

            for plat in platforms_in_lane:
                self.platforms.append(plat)
                self.lanes[i].append(plat)
                # Crocs ride on logs only
                if plat.kind == "log" and random.random() < tune.croc_chance:
                    self.crocs.append(Crocodile(plat))

            # Arrange lane so platforms start entering from the movement side.
            lane_plats = self.lanes[i]
            random.shuffle(lane_plats)
            jitter_gap = 18
            total_len = sum(p.rect.width for p in lane_plats) + self.lane_gap * (len(lane_plats) - 1)
            if speed > 0:
                # Moving right: place a whole chain with a random phase so the lane
                # looks populated immediately.
                slack = max(0, total_len - WIDTH)
                x_left = -random.randint(0, slack) - 40
                for p in lane_plats:
                    p.rect.left = x_left
                    x_left = p.rect.right + self.lane_gap + random.randint(0, jitter_gap)
            else:
                # Moving left: same idea but laid out right-to-left.
                slack = max(0, total_len - WIDTH)
                x_right = WIDTH + random.randint(0, slack) + 40
                for p in lane_plats:
                    p.rect.right = x_right
                    x_right = p.rect.left - self.lane_gap - random.randint(0, jitter_gap)

            # Final pass: resolve any accidental overlaps within the lane.
            ordered = sorted(lane_plats, key=lambda p: p.rect.left)
            for k in range(1, len(ordered)):
                prev = ordered[k - 1]
                cur = ordered[k]
                min_left = prev.rect.right + self.lane_gap
                if cur.rect.left < min_left:
                    cur.rect.left = min_left

        # Flies roam around the whole water area (so you can eat them while platforming)
        fly_speed = 1.0 + 0.25 * (level - 1)
        for _ in range(tune.fly_count):
            self.flies.append(Fly(self.water_area.inflate(-20, -20), fly_speed))

        self.frog.reset(self.start_pos)

    def _draw_background(self) -> None:
        self.screen.fill(WATER)
        pygame.draw.rect(self.screen, BANK, self.safe_top)
        pygame.draw.rect(self.screen, BANK, self.safe_bottom)
        # HUD bar
        pygame.draw.rect(self.screen, (235, 235, 235), (0, 0, WIDTH, HUD_H))
        pygame.draw.line(self.screen, (190, 190, 190), (0, HUD_H - 1), (WIDTH, HUD_H - 1), 2)

    def _draw_hud(self) -> None:
        txt = self.font.render(
            f"Score: {self.score}    Level: {self.level}    Lives: {self.lives}",
            True,
            TEXT,
        )
        self.screen.blit(txt, (12, 12))

    def _clamp_frog(self) -> None:
        half_w = self.frog.w / 2
        half_h = self.frog.h / 2

        self.frog.pos.x = max(half_w, min(WIDTH - half_w, self.frog.pos.x))
        self.frog.pos.y = max(HUD_H + half_h, min(HEIGHT - half_h, self.frog.pos.y))
        self.frog.rect.center = (int(self.frog.pos.x), int(self.frog.pos.y))

    def _clamp_frog_y_only(self) -> None:
        half_h = self.frog.h / 2
        self.frog.pos.y = max(HUD_H + half_h, min(HEIGHT - half_h, self.frog.pos.y))
        self.frog.rect.center = (int(self.frog.pos.x), int(self.frog.pos.y))

    def _frog_on_platform(self) -> Platform | None:
        # Frog must be supported when in water.
        # If overlapping multiple platforms, choose the one with the biggest overlap.
        frog_rect = self.frog.rect
        best: Platform | None = None
        best_area = 0
        for p in self.platforms:
            if not frog_rect.colliderect(p.rect):
                continue
            inter = frog_rect.clip(p.rect)
            area = inter.width * inter.height
            if area > best_area:
                best_area = area
                best = p
        return best

    def _current_support(self) -> Platform | None:
        if not self.water_area.collidepoint(self.frog.rect.center):
            return None
        return self._frog_on_platform()

    def _handle_death_reset(self) -> None:
        self.lives -= 1
        if self.lives <= 0:
            # Restart the stage (same level) when out of lives.
            self._build_level(self.level)
            return

        self.frog.reset(self.start_pos)

    def _handle_level_complete(self) -> None:
        # Advance difficulty and rebuild
        self.level += 1
        self._build_level(self.level)

    def _attempt_hop(self, dx: int, dy: int) -> None:
        if not self.frog.can_move():
            return

        prev_y = self.frog.pos.y
        self.frog.hop(dx, dy)
        self._clamp_frog()

        if dx != 0:
            self.last_horizontal_dir = 1 if dx > 0 else -1

        # If the hop ends in water on a platform, snap to the platform center.
        if self.water_area.collidepoint(self.frog.rect.center):
            support = self._frog_on_platform()
            if support is not None:
                self.frog.pos.x = support.rect.centerx
                self.frog.pos.y = support.rect.centery
                self.frog.rect.center = (int(self.frog.pos.x), int(self.frog.pos.y))
                self._clamp_frog()

        # Score for upward progress
        if self.frog.pos.y < prev_y:
            self.score += 5

    def _walk_if_on_platform(self, support: Platform | None) -> None:
        if support is None:
            return

        keys = pygame.key.get_pressed()
        dx = 0.0
        left = keys[pygame.K_LEFT] or keys[pygame.K_a] or (self.touch.enabled and self.touch.left_held)
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d] or (self.touch.enabled and self.touch.right_held)
        if left:
            dx -= WALK_SPEED
            self.last_horizontal_dir = -1
        if right:
            dx += WALK_SPEED
            self.last_horizontal_dir = 1

        if dx == 0.0:
            return

        self.frog.pos.x += dx
        self.frog.rect.center = (int(self.frog.pos.x), int(self.frog.pos.y))

        # Lose a life if you walk off-screen while riding.
        if self.frog.rect.right < 0 or self.frog.rect.left > WIDTH:
            self._handle_death_reset()
            return

        # Keep vertical bounds safe.
        self._clamp_frog_y_only()

    def run(self) -> None:
        running = True
        while running:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self._attempt_hop(0, -STEP_Y)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self._attempt_hop(0, STEP_Y)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        # On a platform in water: walking is handled per-frame; on land: hop.
                        if self._current_support() is None:
                            self._attempt_hop(-STEP_X, 0)
                        else:
                            self.last_horizontal_dir = -1
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        if self._current_support() is None:
                            self._attempt_hop(STEP_X, 0)
                        else:
                            self.last_horizontal_dir = 1
                    elif event.key == pygame.K_SPACE:
                        # Side jump to nearby platform (same lane feel): space + last direction
                        self._attempt_hop(self.last_horizontal_dir * STEP_X, 0)

                # Touch + mouse
                self._handle_touch_events(event)

                if self.touch.enabled and event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
                    action = self.touch.consume_tap_action()
                    if action == "up":
                        self._attempt_hop(0, -STEP_Y)
                    elif action == "down":
                        self._attempt_hop(0, STEP_Y)
                    elif action == "left":
                        if self._current_support() is None:
                            self._attempt_hop(-STEP_X, 0)
                        else:
                            self.last_horizontal_dir = -1
                    elif action == "right":
                        if self._current_support() is None:
                            self._attempt_hop(STEP_X, 0)
                        else:
                            self.last_horizontal_dir = 1
                    elif action == "jump":
                        self._attempt_hop(self.last_horizontal_dir * STEP_X, 0)

            self.frog.update()

            # Update platforms lane-by-lane so wrap re-entry can't overlap.
            for lane_id, plats in self.lanes.items():
                for p in plats:
                    p.update()

                # Lane-aware wrapping: reinsert behind the last platform in that lane.
                for p in plats:
                    if not p.needs_wrap():
                        continue

                    if p.speed > 0:
                        # Moving right: re-enter on the left behind the current leftmost.
                        leftmost = min(plats, key=lambda q: q.rect.left)
                        p.rect.right = leftmost.rect.left - self.lane_gap
                    else:
                        # Moving left: re-enter on the right beyond the current rightmost.
                        rightmost = max(plats, key=lambda q: q.rect.right)
                        p.rect.left = rightmost.rect.right + self.lane_gap

                # Safety: resolve any overlaps caused by multiple wraps in one frame.
                ordered = sorted(plats, key=lambda q: q.rect.left)
                for i in range(1, len(ordered)):
                    prev = ordered[i - 1]
                    cur = ordered[i]
                    min_left = prev.rect.right + self.lane_gap
                    if cur.rect.left < min_left:
                        cur.rect.left = min_left

            for c in self.crocs:
                c.update()

            for f in self.flies:
                f.update()

            # If frog is in water, it must be on a moving log/lilypad and gets carried by it
            in_water = self.water_area.collidepoint(self.frog.rect.center)
            if in_water:
                support = self._frog_on_platform()
                if support is None:
                    self._handle_death_reset()
                else:
                    # carry by platform speed
                    self.frog.pos.x += support.dx_last
                    self.frog.rect.center = (int(self.frog.pos.x), int(self.frog.pos.y))

                    # Lose a life if carried completely off-screen by a log/lilypad.
                    if self.frog.rect.right < 0 or self.frog.rect.left > WIDTH:
                        self._handle_death_reset()
                    else:
                        # Allow sideways movement while riding.
                        self._walk_if_on_platform(support)
                        # Keep vertical bounds safe while allowing off-screen loss logic.
                        self._clamp_frog_y_only()

            # Crocodile hazard
            for c in self.crocs:
                if self.frog.rect.colliderect(c.rect):
                    self._handle_death_reset()
                    break

            # Eat flies
            for i in range(len(self.flies) - 1, -1, -1):
                if self.frog.rect.colliderect(self.flies[i].rect):
                    self.score += 100
                    # respawn fly somewhere else
                    self.flies[i] = Fly(self.water_area.inflate(-20, -20), 1.0 + 0.25 * (self.level - 1))

            # Win condition: reach the other side (top safe bank)
            if self.frog.rect.colliderect(self.safe_top):
                self._handle_level_complete()

            # Draw
            self._draw_background()
            for p in self.platforms:
                p.draw(self.screen, self.sprites)
            for c in self.crocs:
                c.draw(self.screen, self.sprites)
            for f in self.flies:
                f.draw(self.screen, self.sprites)
            self.frog.draw(self.screen, self.sprites)
            if self.touch.enabled:
                self.touch.draw(self.screen)
            self._draw_hud()

            pygame.display.flip()

        pygame.quit()
        return

    async def run_async(self) -> None:
        # Web builds (pygbag/emscripten) need an async loop that yields.
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self._attempt_hop(0, -STEP_Y)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self._attempt_hop(0, STEP_Y)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        if self._current_support() is None:
                            self._attempt_hop(-STEP_X, 0)
                        else:
                            self.last_horizontal_dir = -1
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        if self._current_support() is None:
                            self._attempt_hop(STEP_X, 0)
                        else:
                            self.last_horizontal_dir = 1
                    elif event.key == pygame.K_SPACE:
                        self._attempt_hop(self.last_horizontal_dir * STEP_X, 0)

                self._handle_touch_events(event)
                if self.touch.enabled and event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
                    action = self.touch.consume_tap_action()
                    if action == "up":
                        self._attempt_hop(0, -STEP_Y)
                    elif action == "down":
                        self._attempt_hop(0, STEP_Y)
                    elif action == "left":
                        if self._current_support() is None:
                            self._attempt_hop(-STEP_X, 0)
                        else:
                            self.last_horizontal_dir = -1
                    elif action == "right":
                        if self._current_support() is None:
                            self._attempt_hop(STEP_X, 0)
                        else:
                            self.last_horizontal_dir = 1
                    elif action == "jump":
                        self._attempt_hop(self.last_horizontal_dir * STEP_X, 0)

            self.frog.update()

            for lane_id, plats in self.lanes.items():
                for p in plats:
                    p.update()
                for p in plats:
                    if not p.needs_wrap():
                        continue
                    if p.speed > 0:
                        leftmost = min(plats, key=lambda q: q.rect.left)
                        p.rect.right = leftmost.rect.left - self.lane_gap
                    else:
                        rightmost = max(plats, key=lambda q: q.rect.right)
                        p.rect.left = rightmost.rect.right + self.lane_gap
                ordered = sorted(plats, key=lambda q: q.rect.left)
                for i in range(1, len(ordered)):
                    prev = ordered[i - 1]
                    cur = ordered[i]
                    min_left = prev.rect.right + self.lane_gap
                    if cur.rect.left < min_left:
                        cur.rect.left = min_left

            for c in self.crocs:
                c.update()
            for f in self.flies:
                f.update()

            in_water = self.water_area.collidepoint(self.frog.rect.center)
            if in_water:
                support = self._frog_on_platform()
                if support is None:
                    self._handle_death_reset()
                else:
                    self.frog.pos.x += support.dx_last
                    self.frog.rect.center = (int(self.frog.pos.x), int(self.frog.pos.y))
                    if self.frog.rect.right < 0 or self.frog.rect.left > WIDTH:
                        self._handle_death_reset()
                    else:
                        self._walk_if_on_platform(support)
                        self._clamp_frog_y_only()

            for c in self.crocs:
                if self.frog.rect.colliderect(c.rect):
                    self._handle_death_reset()
                    break

            for i in range(len(self.flies) - 1, -1, -1):
                if self.frog.rect.colliderect(self.flies[i].rect):
                    self.score += 100
                    self.flies[i] = Fly(self.water_area.inflate(-20, -20), 1.0 + 0.25 * (self.level - 1))

            if self.frog.rect.colliderect(self.safe_top):
                self._handle_level_complete()

            self._draw_background()
            for p in self.platforms:
                p.draw(self.screen, self.sprites)
            for c in self.crocs:
                c.draw(self.screen, self.sprites)
            for f in self.flies:
                f.draw(self.screen, self.sprites)
            self.frog.draw(self.screen, self.sprites)
            if self.touch.enabled:
                self.touch.draw(self.screen)
            self._draw_hud()
            pygame.display.flip()

            await asyncio.sleep(0)

        pygame.quit()
        return


class TouchControls:
    def __init__(self, enabled: bool):
        self.enabled = enabled
        self.left_held = False
        self.right_held = False
        self._tap_action: str | None = None
        self._active = False

    def _layout(self) -> dict[str, pygame.Rect]:
        pad = 14
        size = 74
        # D-pad left side
        base_x = pad
        base_y = HEIGHT - (size * 2 + pad)
        up = pygame.Rect(base_x + size, base_y, size, size)
        left = pygame.Rect(base_x, base_y + size, size, size)
        right = pygame.Rect(base_x + size * 2, base_y + size, size, size)
        down = pygame.Rect(base_x + size, base_y + size, size, size)

        # Jump button right side
        jump = pygame.Rect(WIDTH - (size + pad), HEIGHT - (size + pad), size, size)
        return {"up": up, "down": down, "left": left, "right": right, "jump": jump}

    def on_down(self, x: int, y: int) -> None:
        if not self.enabled:
            return
        self._active = True
        self._update_state(x, y, is_tap=True)

    def on_move(self, x: int, y: int) -> None:
        if not self.enabled or not self._active:
            return
        self._update_state(x, y, is_tap=False)

    def on_up(self, x: int, y: int) -> None:
        if not self.enabled:
            return
        self._active = False
        self.left_held = False
        self.right_held = False

    def _update_state(self, x: int, y: int, is_tap: bool) -> None:
        rects = self._layout()
        # Hold left/right for walking; tap any button triggers an action.
        self.left_held = rects["left"].collidepoint(x, y)
        self.right_held = rects["right"].collidepoint(x, y)

        if not is_tap:
            return
        for name, r in rects.items():
            if r.collidepoint(x, y):
                self._tap_action = name
                return

    def consume_tap_action(self) -> str | None:
        action = self._tap_action
        self._tap_action = None
        return action

    def draw(self, surf: pygame.Surface) -> None:
        rects = self._layout()
        # Minimal UI: translucent buttons
        for name, r in rects.items():
            fill = (255, 255, 255, 110)
            if name == "jump":
                fill = (255, 255, 255, 140)
            box = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            pygame.draw.rect(box, fill, box.get_rect(), border_radius=12)
            pygame.draw.rect(box, (0, 0, 0, 140), box.get_rect(), 2, border_radius=12)
            surf.blit(box, r.topleft)

        # labels
        label_map = {"up": "↑", "down": "↓", "left": "←", "right": "→", "jump": "J"}
        font = pygame.font.SysFont(None, 36)
        for name, r in rects.items():
            txt = font.render(label_map[name], True, (0, 0, 0))
            surf.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))


def _render_fatal_error(message: str) -> None:
    # On mobile web builds, exceptions can end up only in the JS console.
    # Render a readable error screen so a "black screen" becomes debuggable.
    try:
        pygame.init()
        flags = pygame.SCALED | pygame.RESIZABLE
        screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        pygame.display.set_caption("Frog Crossing (Error)")
        font = pygame.font.SysFont(None, 22)

        lines = ["Frog Crossing crashed:"]
        for raw in message.splitlines():
            # Avoid super-wide lines on small screens.
            while len(raw) > 90:
                lines.append(raw[:90])
                raw = raw[90:]
            lines.append(raw)

        # Show last ~22 lines.
        lines = lines[-22:]
        screen.fill((10, 10, 10))
        y = 12
        for line in lines:
            txt = font.render(line, True, (235, 235, 235))
            screen.blit(txt, (12, y))
            y += 22
        pygame.display.flip()

        # Keep the window alive briefly so the message is visible.
        # On web, this returns control quickly after a few frames.
        for _ in range(180):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            pygame.time.delay(16)
    except Exception:
        # Last resort: nothing else to do.
        return


async def _web_entry() -> None:
    try:
        game = FrogCrossingGame()
        await game.run_async()
    except Exception:
        _render_fatal_error(traceback.format_exc())
        raise


def main() -> None:
    if sys.platform == "emscripten":
        # pygbag may already be running an asyncio loop; asyncio.run() would crash.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_web_entry())
        else:
            loop.create_task(_web_entry())
        return

    game = FrogCrossingGame()
    game.run()


if __name__ == "__main__":
    main()
