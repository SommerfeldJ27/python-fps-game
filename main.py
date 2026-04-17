from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import time
import random

app = Ursina()

# ---------------- WORLD ----------------
Sky()

DirectionalLight().look_at(Vec3(1, -1, -1))
AmbientLight(color=color.rgba(120, 120, 120, 0.5))

# ---------------- GROUND ----------------
ground = Entity(
    model='cube',
    scale=(100, 2, 100),
    position=(0, -1, 0),
    collider='box',
    color=color.dark_gray
)

Entity(
    model='cube',
    scale=(200, 1, 200),
    position=(0, -3, 0),
    collider='box',
    visible=False
)

# ---------------- MAP ----------------
def make_block(position, scale=(2,2,2), color=color.gray):
    return Entity(
        model='cube',
        position=position,
        scale=scale,
        color=color,
        collider='box'
    )

def build_map():

    make_block((0, 1, 0), scale=(4,2,2), color=color.orange)
    make_block((4, 1, -4), scale=(2,3,2), color=color.orange)
    make_block((-4, 1, 4), scale=(2,3,2), color=color.orange)

    make_block((0, 1, 8), scale=(12,2,2))
    make_block((0, 1, -8), scale=(12,2,2))

    make_block((-8, 1, 10), scale=(4,2,2), color=color.red)
    make_block((-12, 1, 16), scale=(3,2,3), color=color.red)
    make_block((-8, 1, 20), scale=(2,2,4), color=color.red)

    make_block((8, 1, 10), scale=(4,2,2), color=color.green)
    make_block((12, 1, 16), scale=(2,2,6), color=color.green)
    make_block((8, 1, 20), scale=(4,2,2), color=color.green)

    make_block((-4, 1, 12), scale=(2,2,2))
    make_block((4, 1, 12), scale=(2,2,2))

    make_block((0, 1, -30), scale=(60,2,2))
    make_block((0, 1, 30), scale=(60,2,2))
    make_block((-30, 1, 0), scale=(2,2,60))
    make_block((30, 1, 0), scale=(2,2,60))

build_map()

# ---------------- PLAYER ----------------
player = FirstPersonController()
player.cursor.visible = False
player.speed = 6
player.health = 100
player.position = (0, 10, -20)

camera.fov = 80

def reset_player():
    player.position = (0, 10, -20)
    player.health = 100

# ---------------- ROUND SYSTEM ----------------
round_active = False
round_number = 0
enemies_remaining = 0

round_text = Text("", origin=(0,0), scale=2, color=color.white)

def hide_round_text():
    round_text.text = ""

# -----------WEAPON STATE--------
ammo = 30
max_ammo = 30
weapon = "rifle"

# ---------------- UI (UPDATED FPS HUD) ----------------

# CROSSHAIR
crosshair = Entity(
    parent=camera.ui,
    model='quad',
    color=color.white,
    scale=0.008
)

# HITMARKER
hitmarker = Text(
    "+",
    origin=(0,0),
    scale=3,
    color=color.white,
    enabled=False
)

# DAMAGE FLASH
damage_flash = Entity(
    parent=camera.ui,
    model='quad',
    color=color.rgba(255, 0, 0, 80),
    scale=10,
    enabled=False
)

# ---------------- TOP ROUND DISPLAY ----------------
round_text = Text(
    "",
    origin=(0, 0),
    position=(0, 0.45),
    scale=2,
    color=color.white
)

# ---------------- AMMO (BOTTOM RIGHT) ----------------
ammo_text = Text(
    "",
    origin=(0, 0),
    position=(0.6, -0.45),
    scale=2,
    color=color.white
)

# ---------------- WEAPON (BOTTOM RIGHT ABOVE AMMO) ----------------
weapon_text = Text(
    "",
    origin=(0, 0),
    position=(0.6, -0.38),
    scale=1.5,
    color=color.azure
)

# ---------------- HEALTH BAR (BOTTOM LEFT) ----------------
health_bg = Entity(
    parent=camera.ui,
    model='quad',
    color=color.dark_gray,
    scale=(0.25, 0.03),
    position=(-0.65, -0.45)
)

health_bar = Entity(
    parent=camera.ui,
    model='quad',
    color=color.lime,
    scale=(0.25, 0.03),
    position=(-0.65, -0.45),
    origin=(-0.5, 0)
)

health_text = Text(
    "",
    origin=(0, 0),
    position=(-0.65, -0.40),
    scale=1.2,
    color=color.white
)

# ---------------- WEAPONS ----------------
weapons = {
    "rifle": {"damage": 50, "fire_rate": 0.12},
    "pistol": {"damage": 25, "fire_rate": 0.3}
}

last_shot = 0

# ---------------- GUN ----------------
gun = Entity(
    parent=camera,
    model='cube',
    color=color.black,
    scale=(0.2, 0.15, 0.6),
    position=(0.5, -0.4, 1),
    rotation=(0, 90, 0)
)

# ---------------- RELOAD ----------------
reloading = False
reload_text = None

# ---------------- ENEMIES ----------------
enemies = []
enemy_last_shot = {}

def spawn_enemies(count):
    global enemies, enemy_last_shot, enemies_remaining

    enemies.clear()
    enemy_last_shot.clear()

    enemies_remaining = count

    for i in range(count):
        pos = (
            random.randint(-15, 15),
            2,
            random.randint(-15, 15)
        )

        e = Entity(
            model='cube',
            color=color.red,
            scale=(1,2,1),
            position=pos,
            collider='box'
        )

        e.health = 100 + round_number * 10
        enemies.append(e)
        enemy_last_shot[e] = time.time()

def start_round():
    global round_active, round_number

    round_active = True
    round_number += 1

    round_text.text = f"Round {round_number}"
    invoke(hide_round_text, delay=2)

    reset_player()
    spawn_enemies(3 + round_number * 2)

# ---------------- SHOOT ----------------
def shoot():
    global ammo, last_shot, enemies_remaining

    w = weapons[weapon]

    if reloading:
        return

    if time.time() - last_shot < w["fire_rate"]:
        return

    if ammo <= 0:
        return

    last_shot = time.time()
    ammo -= 1

    hit = raycast(camera.world_position, camera.forward, distance=100)

    if hit.hit and hasattr(hit.entity, "health"):

        # HITMARKER
        hitmarker.enabled = True
        invoke(setattr, hitmarker, 'enabled', False, delay=0.08)

        hit.entity.health -= w["damage"]

        hit.entity.color = color.white
        invoke(setattr, hit.entity, 'color', color.red, delay=0.1)

        if hit.entity.health <= 0:
            destroy(hit.entity)

            if hit.entity in enemies:
                enemies.remove(hit.entity)
                enemies_remaining -= 1

# ---------------- AI ----------------
def enemy_ai():
    for e in enemies:
        dist = distance(e.position, player.position)

        if dist < 15:
            e.look_at(player)

            if dist > 3:
                e.position += e.forward * time.dt * 2

            if dist < 5:
                if time.time() - enemy_last_shot[e] > 2.0:
                    enemy_last_shot[e] = time.time()

                    player.health -= 5
                    damage_flash.enabled = True
                    invoke(setattr, damage_flash, 'enabled', False, delay=0.1)

                    if player.health <= 0:
                        print("YOU DIED")
                        application.pause()

# ---------------- INPUT ----------------
def input(key):
    global weapon, reloading, ammo, reload_text

    if key == 'left mouse down':
        shoot()

    if key == '1':
        weapon = "rifle"

    if key == '2':
        weapon = "pistol"

    if key == 'r' and not reloading:
        reloading = True
        reload_text = Text("Reloading...", origin=(0,0), scale=2, color=color.orange)

        def finish_reload():
            global ammo, reloading
            ammo = max_ammo
            reloading = False
            destroy(reload_text)

        invoke(finish_reload, delay=1.5)

# ---------------- UPDATE ----------------
def update():
    global round_active

    if player.y < -5:
        player.position = (0, 10, -20)

    ammo_text.text = f"Ammo: {ammo}/{max_ammo}"
    weapon_text.text = f"{weapon.upper()}"

    health_text.text = f"{player.health} HP"
    health_bar.scale_x = 0.25 * (player.health / 100)

    enemy_ai()

    if round_active and enemies_remaining <= 0:
        round_active = False
        invoke(start_round, delay=3)

# ---------------- START ----------------
invoke(start_round, delay=1)

app.run()