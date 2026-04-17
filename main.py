from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import time
import random

app = Ursina()

# ---------------- FIXED VISUAL SYSTEM ----------------
window.color = color.rgb(90, 110, 140)

Sky()

DirectionalLight().look_at(Vec3(1, -1, -1))
AmbientLight(color=color.rgba(80, 80, 80, 1))

# ---------------- GROUND ----------------
ground = Entity(
    model='cube',
    scale=(100, 2, 100),
    position=(0, -1, 0),
    collider='box',
    color=color.rgb(40, 40, 45)
)

# ---------------- MAP ----------------
def make_block(position, scale=(2,2,2), color=color.gray):
    return Entity(
        model='cube',
        position=position,
        scale=scale,
        color=color,
        collider='box',
        unlit=False
    )

def build_map():
    make_block((0, 1, 0), scale=(4,2,2), color=color.orange)

    make_block((4, 1, -4), scale=(2,3,2), color=color.rgb(80,80,90))
    make_block((-4, 1, 4), scale=(2,3,2), color=color.rgb(80,80,90))

    make_block((0, 1, 8), scale=(12,2,2), color=color.rgb(60,60,65))
    make_block((0, 1, -8), scale=(12,2,2), color=color.rgb(60,60,65))

    make_block((-8, 1, 10), scale=(4,2,2), color=color.rgb(200,60,60))
    make_block((8, 1, 10), scale=(4,2,2), color=color.rgb(60,200,60))

    make_block((0, 1, -30), scale=(60,2,2), color=color.rgb(50,50,55))
    make_block((0, 1, 30), scale=(60,2,2), color=color.rgb(50,50,55))
    make_block((-30, 1, 0), scale=(2,2,60), color=color.rgb(50,50,55))
    make_block((30, 1, 0), scale=(2,2,60), color=color.rgb(50,50,55))

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

# ---------------- WEAPON ----------------
weapon = "rifle"
ads = False

ammo = 30
max_ammo = 30
reloading = False
reload_anim = False

weapons = {
    "rifle": {"damage": 50, "fire_rate": 0.12, "recoil": 0.08},
    "pistol": {"damage": 25, "fire_rate": 0.3, "recoil": 0.04}
}

last_shot = 0

# ---------------- GUN ----------------
gun = Entity(parent=camera)

gun_body = Entity(parent=gun, model='cube', color=color.rgb(40,40,40),
                  scale=(0.25,0.15,0.7), position=(0.5,-0.4,1))

gun_barrel = Entity(parent=gun, model='cube', color=color.rgb(10,10,10),
                   scale=(0.08,0.08,0.9), position=(0.5,-0.35,1.3))

gun_base_pos = Vec3(0.5, -0.4, 1)

# ---------------- ANIMATION ----------------
recoil_kick = Vec3(0,0,0)
sway = Vec2(0,0)
bob_timer = 0
bob = 0

# ---------------- UI ----------------
crosshair = Entity(parent=camera.ui, model='quad', color=color.rgb(20,255,120), scale=0.01)
hitmarker = Text("+", origin=(0,0), scale=4, color=color.lime, enabled=False)

ammo_text = Text("", position=(0.6,-0.45), scale=2, color=color.white)
weapon_text = Text("", position=(0.6,-0.38), scale=1.5, color=color.white)
health_text = Text("", position=(-0.65,-0.40), scale=1.2, color=color.white)

health_bar = Entity(
    parent=camera.ui,
    model='quad',
    color=color.lime,
    scale=(0.25,0.03),
    position=(-0.65,-0.45),
    origin=(-0.5,0)
)

# ---------------- ENEMIES ----------------
enemies = []
enemy_last_shot = {}
round_active = False
round_number = 0
enemies_remaining = 0

def spawn_enemies(count):
    global enemies, enemy_last_shot, enemies_remaining

    enemies.clear()
    enemy_last_shot.clear()
    enemies_remaining = count

    for i in range(count):
        e = Entity(
            model='cube',
            color=color.rgb(200,60,60),
            scale=(1,2,1),
            position=(random.randint(-15,15), 2, random.randint(-15,15)),
            collider='box'
        )
        e.health = 100
        enemies.append(e)
        enemy_last_shot[e] = time.time()

def start_round():
    global round_active, round_number
    round_active = True
    round_number += 1
    reset_player()
    spawn_enemies(3 + round_number * 2)

# ---------------- SHOOT ----------------
def shoot():
    global ammo, last_shot, enemies_remaining, recoil_kick

    if reloading:
        return

    w = weapons[weapon]

    if time.time() - last_shot < w["fire_rate"]:
        return

    if ammo <= 0:
        return

    last_shot = time.time()
    ammo -= 1

    # recoil (camera + gun)
    recoil_kick.z -= w["recoil"]
    recoil_kick.y += w["recoil"] * 0.6

    camera.rotation_x -= w["recoil"] * 20
    camera.rotation_y += random.uniform(-0.5, 0.5)

    hit = raycast(camera.world_position, camera.forward, distance=100)

    if hit.hit and hasattr(hit.entity, "health"):
        hit.entity.health -= w["damage"]

        hitmarker.enabled = True
        invoke(setattr, hitmarker, 'enabled', False, delay=0.08)

        if hit.entity.health <= 0:
            if hit.entity in enemies:
                enemies.remove(hit.entity)
                enemies_remaining -= 1
            destroy(hit.entity)

# ---------------- INPUT ----------------
def input(key):
    global weapon, reloading, ammo, ads, reload_anim

    if key == 'left mouse down':
        shoot()

    if key == '1':
        weapon = "rifle"

    if key == '2':
        weapon = "pistol"

    if key == 'right mouse down':
        ads = True
        camera.fov = 60

    if key == 'right mouse up':
        ads = False
        camera.fov = 80

    if key == 'r' and not reloading:
        reloading = True
        reload_anim = True

        def finish():
            global ammo, reloading, reload_anim
            ammo = max_ammo
            reloading = False
            reload_anim = False

        invoke(finish, delay=1.5)

# ---------------- UPDATE ----------------
def update():
    global bob_timer, bob, recoil_kick

    ammo_text.text = f"Ammo: {ammo}/{max_ammo}"
    weapon_text.text = weapon.upper()
    health_text.text = f"{player.health} HP"

    health_bar.scale_x = 0.25 * (player.health / 100)

    # recoil recovery
    recoil_kick = lerp(recoil_kick, Vec3(0,0,0), 10 * time.dt)

    # sway
    sway.x = lerp(sway.x, mouse.velocity[0], 6 * time.dt)
    sway.y = lerp(sway.y, mouse.velocity[1], 6 * time.dt)

    # bob
    moving = held_keys['w'] or held_keys['a'] or held_keys['s'] or held_keys['d']
    if moving:
        bob_timer += time.dt * 10
        bob = sin(bob_timer) * 0.02
    else:
        bob = lerp(bob, 0, 5 * time.dt)

    ads_mult = 0.3 if ads else 1.0

    # reload animation
    if reload_anim:
        gun.y = lerp(gun.y, -0.7, 12 * time.dt)
        gun.rotation_x = lerp(gun.rotation_x, 30, 12 * time.dt)
    else:
        gun.y = lerp(gun.y, -0.4, 10 * time.dt)
        gun.rotation_x = lerp(gun.rotation_x, 0, 10 * time.dt)

    gun.position = gun_base_pos + recoil_kick + Vec3(
        -sway.x * 2 * ads_mult,
        -sway.y * 2 * ads_mult + bob,
        0
    )

    # enemy AI
    for e in enemies[:]:
        dist = distance(e.position, player.position)

        if dist < 15:
            e.look_at(player)

            if dist > 3:
                e.position += e.forward * time.dt * 2

            if dist < 5:
                if time.time() - enemy_last_shot[e] > 2:
                    enemy_last_shot[e] = time.time()
                    player.health -= 5

                    if player.health <= 0:
                        print("YOU DIED")
                        application.pause()

# ---------------- START ----------------
invoke(start_round, delay=1)

app.run()