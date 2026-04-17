from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import time

app = Ursina()

# ---------------- WORLD ----------------
Sky()

DirectionalLight().look_at(Vec3(1, -1, -1))
AmbientLight(color=color.rgba(120, 120, 120, 0.5))

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

# ---------------- GROUND ----------------
    Entity(
        model='cube',
        scale=(100, 1, 100),
        position=(0, 0, 0),
        collider='box',
        color=color.dark_gray
    )

    # MID
    make_block((0, 1, 0), scale=(4,2,2), color=color.orange)
    make_block((4, 1, -4), scale=(2,3,2), color=color.orange)
    make_block((-4, 1, 4), scale=(2,3,2), color=color.orange)

    make_block((0, 1, 8), scale=(12,2,2))
    make_block((0, 1, -8), scale=(12,2,2))

    # A SITE
    make_block((-8, 1, 10), scale=(4,2,2), color=color.red)
    make_block((-12, 1, 16), scale=(3,2,3), color=color.red)
    make_block((-8, 1, 20), scale=(2,2,4), color=color.red)
    make_block((-14, 2, 18), scale=(2,1,2), color=color.yellow)

    # B SITE
    make_block((8, 1, 10), scale=(4,2,2), color=color.green)
    make_block((12, 1, 16), scale=(2,2,6), color=color.green)
    make_block((8, 1, 20), scale=(4,2,2), color=color.green)
    make_block((14, 1, 22), scale=(2,3,2), color=color.green)

    # ROTATION
    make_block((-4, 1, 12), scale=(2,2,2), color=color.black)
    make_block((4, 1, 12), scale=(2,2,2), color=color.black)

    # BOUNDS
    make_block((0, 1, -30), scale=(60,2,2), color=color.blue)
    make_block((0, 1, 30), scale=(60,2,2), color=color.blue)
    make_block((-30, 1, 0), scale=(2,2,60), color=color.blue)
    make_block((30, 1, 0), scale=(2,2,60), color=color.blue)

build_map()

# ---------------- PLAYER ----------------
player = FirstPersonController()
player.cursor.visible = False
player.speed = 6
player.health = 100
player.position = (0, 5, -20)

camera.fov = 80

# ---------------- SAFETY NET (PREVENT FALLING BUGS) ----------------
def safety_check():
    if player.y < -10:
        player.position = (0, 5, -20)

# ---------------- UI ----------------
crosshair = Entity(parent=camera.ui, model='quad', color=color.white, scale=0.008)

ammo_text = Text("", position=(-0.85, 0.45), scale=1.5)
hp_text = Text("", position=(-0.85, 0.4), scale=1.5)
weapon_text = Text("", position=(-0.85, 0.35), scale=1.5)

hitmarker = Text("+", origin=(0,0), scale=3, color=color.white, enabled=False)

damage_flash = Entity(
    parent=camera.ui,
    model='quad',
    color=color.rgba(255, 0, 0, 80),
    scale=10,
    enabled=False
)

# ---------------- WEAPONS ----------------
weapon = "rifle"

weapons = {
    "rifle": {"damage": 50, "fire_rate": 0.12, "spread": 0.6},
    "pistol": {"damage": 25, "fire_rate": 0.3, "spread": 1.2}
}

ammo = 30
max_ammo = 30
reloading = False
last_shot = 0

recoil = 0
recoil_return_speed = 6

# ---------------- GUN ----------------
gun = Entity(
    parent=camera,
    model='cube',
    color=color.black,
    scale=(0.2, 0.15, 0.6),
    position=(0.5, -0.4, 1),
    rotation=(0, 90, 0)
)

muzzle_flash = Entity(
    parent=gun,
    model='quad',
    color=color.yellow,
    scale=0.1,
    position=(0, 0, 1),
    enabled=False
)

# ---------------- ENEMIES ----------------
enemies = []
enemy_last_shot = {}

enemy_spawns = [
    (-10, 2, 18),
    (10, 2, 18),
    (0, 2, 10)
]

def spawn_enemies():
    for pos in enemy_spawns:
        e = Entity(
            model='cube',
            color=color.red,
            scale=(1,2,1),
            position=pos,
            collider='box'
        )
        e.health = 100
        enemies.append(e)
        enemy_last_shot[e] = time.time()

spawn_enemies()

# ---------------- SHOOT ----------------
def shoot():
    global ammo, last_shot, recoil

    w = weapons[weapon]

    if reloading:
        return

    if time.time() - last_shot < w["fire_rate"]:
        return

    if ammo <= 0:
        return

    last_shot = time.time()
    ammo -= 1

    recoil += w["spread"]
    camera.rotation_x -= recoil

    muzzle_flash.enabled = True
    invoke(setattr, muzzle_flash, 'enabled', False, delay=0.05)

    camera.fov = 85
    invoke(setattr, camera, 'fov', 80, delay=0.05)

    hit = raycast(camera.world_position, camera.forward, distance=100)

    if hit.hit and hasattr(hit.entity, "health"):
        hitmarker.enabled = True
        invoke(setattr, hitmarker, 'enabled', False, delay=0.08)

        hit.entity.health -= w["damage"]

        hit.entity.color = color.white
        invoke(setattr, hit.entity, 'color', color.red, delay=0.1)

        if hit.entity.health <= 0:
            destroy(hit.entity)
            if hit.entity in enemies:
                enemies.remove(hit.entity)

# ---------------- RELOAD ----------------
def reload():
    global ammo, reloading

    if reloading:
        return

    reloading = True
    reload_text = Text("Reloading...", origin=(0,0), scale=2, color=color.orange)

    def finish():
        global ammo, reloading
        ammo = max_ammo
        reloading = False
        destroy(reload_text)

    invoke(finish, delay=1.5)

# ---------------- ENEMY AI ----------------
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
    global weapon

    if key == 'left mouse down':
        shoot()

    if key == 'r':
        reload()

    if key == '1':
        weapon = "rifle"

    if key == '2':
        weapon = "pistol"

# ---------------- UPDATE ----------------
def update():
    global recoil

    recoil = lerp(recoil, 0, recoil_return_speed * time.dt)
    camera.rotation_x = lerp(camera.rotation_x, 0, 5 * time.dt)

    ammo_text.text = f"Ammo: {ammo}/{max_ammo}"
    hp_text.text = f"HP: {player.health}"
    weapon_text.text = f"Weapon: {weapon}"

    enemy_ai()
    safety_check()

    gun.y = -0.4 + sin(time.time() * 3) * 0.01
    gun.x = 0.5 + sin(time.time() * 2) * 0.01

app.run()