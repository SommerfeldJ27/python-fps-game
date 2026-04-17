from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import time

app = Ursina()

# ---------------- WORLD ----------------
Sky()

ground = Entity(
    model='plane',
    scale=(80, 1, 80),
    texture='white_cube',
    texture_scale=(80, 80),
    collider='box',
    color=color.dark_gray
)

DirectionalLight().look_at(Vec3(1, -1, -1))
AmbientLight(color=color.rgba(120, 120, 120, 0.5))

# cover / map objects
cover_positions = [
    (-6,1,-6),(6,1,-6),(-6,1,6),(6,1,6),
    (0,1,-8),(0,1,8),(-8,1,0),(8,1,0)
]

for p in cover_positions:
    Entity(
        model='cube',
        color=color.gray,
        scale=(2,2,2),
        position=p,
        collider='box'
    )

# ---------------- PLAYER ----------------
player = FirstPersonController()
player.cursor.visible = False
player.speed = 6
player.health = 100

# ---------------- CAMERA SETTINGS ----------------
camera.fov = 80

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

reload_text = None

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

# recoil system
recoil = 0
recoil_return_speed = 6

# ---------------- GUN VISUAL ----------------
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

def spawn_enemy(pos):
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

for i in range(6):
    spawn_enemy((random.randint(-10,10),1,random.randint(-10,10)))

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

    # recoil
    recoil += w["spread"]
    camera.rotation_x -= recoil

    # muzzle flash
    muzzle_flash.enabled = True
    invoke(setattr, muzzle_flash, 'enabled', False, delay=0.05)

    # FOV kick
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

# ---------------- RELOAD ----------------
def reload():
    global ammo, reloading, reload_text

    if reloading:
        return

    reloading = True

    reload_text = Text("Reloading...", origin=(0,0), scale=2, color=color.orange)

    def finish():
        global ammo, reloading, reload_text
        ammo = max_ammo
        reloading = False

        if reload_text:
            destroy(reload_text)
            reload_text = None

    invoke(finish, delay=1.5)

# ---------------- ENEMY AI ----------------
def enemy_ai():
    for e in enemies:
        if not e:
            continue

        dist = distance(e.position, player.position)
        e.look_at(player.position)

        if dist > 5:
            e.position += e.forward * time.dt * 1.5

        if dist < 25:
            if time.time() - enemy_last_shot[e] > 1.2:
                enemy_last_shot[e] = time.time()

                player.health -= 5

                if player.health < 0:
                    player.health = 0

                damage_flash.enabled = True
                invoke(setattr, damage_flash, 'enabled', False, delay=0.1)

                camera.position += Vec3(random.uniform(-0.05,0.05), random.uniform(-0.05,0.05), 0)

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

    # recoil recovery
    recoil = lerp(recoil, 0, recoil_return_speed * time.dt)
    camera.rotation_x = lerp(camera.rotation_x, 0, 5 * time.dt)

    # UI
    ammo_text.text = f"Ammo: {ammo}/{max_ammo}"
    hp_text.text = f"HP: {player.health}"
    weapon_text.text = f"Weapon: {weapon}"

    # enemy AI
    enemy_ai()

    # gun sway
    gun.y = -0.4 + sin(time.time() * 3) * 0.01
    gun.x = 0.5 + sin(time.time() * 2) * 0.01

    # camera shake recovery
    camera.position = lerp(camera.position, Vec3(0,0,0), 5 * time.dt)

app.run()