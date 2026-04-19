from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

app = Ursina()

# -----------------------
# CONFIG
# -----------------------
PLAYER_SPEED = 5
PLAYER_SENSITIVITY = 40
GRAVITY = 1


# -----------------------
# WORLD / MAP
# -----------------------
def create_world():
    global ground

    ground = Entity(
        model='cube',
        scale=(60,1,60),
        position=(0,0,0),
        collider='box',
        color=color.rgb(60, 180, 75)
    )

    # OUTER WALLS (clean arena)
    for i in range(-25, 26, 5):

        Entity(model='cube', scale=(5,5,1), position=(i,2,-25),
               collider='box', color=color.gray)

        Entity(model='cube', scale=(5,5,1), position=(i,2,25),
               collider='box', color=color.gray)

        Entity(model='cube', scale=(1,5,5), position=(-25,2,i),
               collider='box', color=color.gray)

        Entity(model='cube', scale=(1,5,5), position=(25,2,i),
               collider='box', color=color.gray)

    # COVER OBJECTS
    cover = [
        (0,1,0),
        (8,1,6),
        (-8,1,6),
        (8,1,-6),
        (-8,1,-6),
        (0,1,12),
        (0,1,-12),
    ]

    for p in cover:
        Entity(
            model='cube',
            scale=(2,2,2),
            position=p,
            collider='box',
            color=color.rgb(120, 90, 70)
        )


# -----------------------
# PLAYER
# -----------------------
def create_player():
    global player, pitch

    player = FirstPersonController()
    player.position = (0, 5, 0)
    player.speed = PLAYER_SPEED
    player.gravity = GRAVITY

    pitch = 0


# -----------------------
# WEAPONS
# -----------------------
weapons = {
    "rifle": {"damage": 25, "ammo": 30, "mag": 30, "recoil": 1.2, "reload_time": 1.5},
    "pistol": {"damage": 18, "ammo": 12, "mag": 12, "recoil": 0.6, "reload_time": 1.0}
}

current_weapon = "rifle"
can_shoot = True
reloading = False


# -----------------------
# RECOIL
# -----------------------
recoil = Vec3(0,0,0)
target_recoil = Vec3(0,0,0)


# -----------------------
# UI
# -----------------------
crosshair = Entity(parent=camera.ui, model='quad', scale=0.008, color=color.white)

ammo_text = Text("", parent=camera.ui, position=(0.7,-0.45), scale=2)
weapon_text = Text("", parent=camera.ui, position=(0.7,-0.40), scale=1.5)

hitmarker = Entity(parent=camera.ui, model='quad',
                   scale=0.01, color=color.red, enabled=False, z=-9)


def show_hitmarker():
    hitmarker.enabled = True
    invoke(hide_hitmarker, delay=0.08)

def hide_hitmarker():
    hitmarker.enabled = False


# -----------------------
# ENEMIES
# -----------------------
class Enemy(Entity):
    def __init__(self, position=(0,0,0)):
        super().__init__(
            model='cube',
            color=color.red,
            position=position,
            scale=(1,2,1),
            collider='box'
        )
        self.hp = 100

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.die()

    def die(self):
        self.enabled = False
        destroy(self)


enemies = [
    Enemy(position=(6,1,10)),
    Enemy(position=(-6,1,10))
]


# -----------------------
# SHOOTING
# -----------------------
def set_can_shoot():
    global can_shoot
    can_shoot = True


def shoot():
    global can_shoot, target_recoil

    if reloading:
        return

    w = weapons[current_weapon]

    if not can_shoot or w["ammo"] <= 0:
        return

    can_shoot = False
    invoke(set_can_shoot, delay=0.12)

    w["ammo"] -= 1

    # recoil
    target_recoil.y += w["recoil"] * 0.4
    target_recoil.x += random.uniform(-0.1, 0.1)

    hit = raycast(camera.world_position, camera.forward, distance=100, ignore=[player])

    if hit.hit and hasattr(hit.entity, "take_damage"):
        hit.entity.take_damage(w["damage"])
        show_hitmarker()


# -----------------------
# RELOAD SYSTEM (NEW)
# -----------------------
def reload():
    global reloading

    if reloading:
        return

    w = weapons[current_weapon]

    if w["ammo"] == w["mag"]:
        return

    reloading = True
    invoke(finish_reload, delay=w["reload_time"])


def finish_reload():
    global reloading

    w = weapons[current_weapon]
    w["ammo"] = w["mag"]

    reloading = False


# -----------------------
# INPUT
# -----------------------
def input(key):
    global current_weapon

    if key == 'left mouse down':
        shoot()

    if key == 'r':
        reload()

    if key == '1':
        current_weapon = "rifle"

    if key == '2':
        current_weapon = "pistol"


# -----------------------
# UPDATE
# -----------------------
def update():
    global pitch, recoil, target_recoil

    # look
    player.rotation_y += mouse.velocity[0] * PLAYER_SENSITIVITY

    pitch -= mouse.velocity[1] * PLAYER_SENSITIVITY
    pitch = clamp(pitch, -90, 90)

    # recoil smoothing
    target_recoil = lerp(target_recoil, Vec3(0,0,0), 8 * time.dt)
    recoil = lerp(recoil, target_recoil, 12 * time.dt)

    camera.rotation_x = pitch - recoil.y * 0.6
    camera.rotation_y = recoil.x * 2

    # enemy AI
    for e in enemies[:]:
        if not e:
            continue

        if distance(e.position, player.position) < 20:
            e.look_at(player.position)
            e.position += e.forward * time.dt

    # UI
    w = weapons[current_weapon]
    ammo_text.text = f"{w['ammo']} / {w['mag']}"
    weapon_text.text = current_weapon.upper()


# -----------------------
# START
# -----------------------
create_world()
create_player()

app.run()