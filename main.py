from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

app = Ursina()

ground = Entity(
    model='cube',
    scale=(50, 1, 50),
    position=(0, 0, 0),
    collider='box',
    color=color.rgb(0,255,0)
)
"""ground.color=color.green"""

# -----------------------
# MAP
# -----------------------
def create_map():

    # outer walls
    for i in range(-20, 21, 4):
        Entity(
            model='cube',
            scale=(4,4,1),
            position=(i,2,-20),
            collider='box',
            color=color.gray,
            scale_y=3.8
        )

        Entity(
            model='cube',
            scale=(4,4,1),
            position=(i,2,20),
            collider='box',
            color=color.gray,
            scale_y=3.8
        )

        Entity(
            model='cube',
            scale=(1,4,4),
            position=(-20,2,i),
            collider='box',
            color=color.gray,
            scale_y=3.8
        )
        
        Entity(
            model='cube',
            scale=(1,4,4),
            position=(20,2,i),
            collider='box',
            color=color.gray,
            scale_y=3.8
        )

    # structured cover (clean FPS layout)
    cover_positions = [
        (6,1,0),
        (-6,1,0),
        (0,1,6),
        (0,1,-6),
        (10,1,10),
        (-10,1,10),
        (10,1,-10),
        (-10,1,-10),
    ]

    for pos in cover_positions:
        Entity(
            model='cube',
            scale=(2,2,2),
            position=pos,
            collider='box',
            color=color.rgb(90,70,60)
        )

create_map()

window.title = "FPS Fixed Build"
window.show_fps_counter = True
mouse.locked = True
window.vsync = True


# -----------------------
# SOUND
# -----------------------

rifle_fire_sfx = Audio('assets/sounds/rifle_fire.wav', autoplay=False, volume=0.6)
pistol_fire_sfx = Audio('assets/sounds/pistol_fire.wav', autoplay=False, volume=0.6)
reload_sfx = Audio('assets/sounds/reload.wav', autoplay=False, volume=0.8)
hit_sfx = Audio('assets/sounds/hit.wav', autoplay=False, volume=1.0)



# -----------------------
# PLAYER
# -----------------------

player = FirstPersonController()
player.position = (0, 8, 0)   # spawn clearly ABOVE ground
player.gravity = 1
player.speed = 5




# -----------------------
# LOOK CONTROL (FIXED)
# -----------------------

pitch = 0


# -----------------------
# WEAPONS
# -----------------------

weapons = {
    "rifle": {"damage": 25, "ammo": 30, "mag": 30, "recoil": 1.2},
    "pistol": {"damage": 18, "ammo": 12, "mag": 12, "recoil": 0.6}
}

current_weapon = "rifle"
can_shoot = True
reloading = False


# -----------------------
# RECOIL SYSTEM (CLEAN)
# -----------------------

recoil = Vec3(0, 0, 0)
target_recoil = Vec3(0, 0, 0)


# -----------------------
# HUD (UPGRADED)
# -----------------------

hitmarker = Entity(
    parent=camera.ui,
    model='quad',
    scale=0.01,
    color=color.red,
    enabled=False,
    z=-9
)

# crosshair
crosshair = Entity(
    parent=camera.ui,
    model='quad',
    scale=0.008,
    color=color.white,
    z=-10
)

# ammo
ammo_text = Text(
    "",
    parent=camera.ui,
    position=(0.7, -0.45),
    scale=2,
    color=color.white
)

# weapon name
weapon_text = Text(
    "",
    parent=camera.ui,
    position=(0.7, -0.40),
    scale=1.5,
    color=color.gray
)

hp_bar_bg = Entity(
    parent=camera.ui,
    model='quad',
    scale=(0.3, 0.03),
    position=(-0.65, -0.45),
    color=color.dark_gray,
    z=0
)

hp_bar = Entity(
    parent=camera.ui,
    model='quad',
    scale=(0.3, 0.03),
    position=(-0.65, -0.45),
    color=color.red,
    z=-0.01   # 🔥 THIS FIXES FLICKER
)

# -----------------------
# HITMARKER
# -----------------------

def show_hitmarker():
    hitmarker.enabled = True
    invoke(hide_hitmarker, delay=0.08)

def hide_hitmarker():
    hitmarker.enabled = False

# -----------------------
# GUNS
# -----------------------

rifle = Entity(
    parent=camera,
    model='cube',
    color=color.black,
    scale=(0.18, 0.12, 0.6),
    position=(0.35, -0.35, 0.7)
)

pistol = Entity(
    parent=camera,
    model='cube',
    color=color.gray,
    scale=(0.12, 0.1, 0.35),
    position=(0.35, -0.38, 0.6),
    enabled=False
)


def update_guns():
    rifle.enabled = current_weapon == "rifle"
    pistol.enabled = current_weapon == "pistol"


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
            destroy(self)


enemies = [
    Enemy(position=(5,1,10)),
    Enemy(position=(-5,1,10))
]

def set_can_shoot():
    global can_shoot
    can_shoot = True

# -----------------------
# SHOOT
# -----------------------

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

    if current_weapon == "rifle":
        rifle_fire_sfx.play()
    else:
        pistol_fire_sfx.play()

    # recoil (safe system)
    target_recoil.y += weapons[current_weapon]["recoil"] * 0.4
    target_recoil.x += random.uniform(-0.08, 0.08)

    target_recoil.x += random.uniform(-0.15, 0.15)
    target_recoil.x = clamp(target_recoil.x, -0.5, 0.5)

    hit = raycast(camera.world_position, camera.forward, distance=100, ignore=[player])

    if hit.hit and hasattr(hit.entity, "take_damage"):
        hit.entity.take_damage(w["damage"])
        hit_sfx.play()

        # ONLY SHOW HITMARKER HERE
        hitmarker.scale = 0.02
        invoke(lambda: setattr(hitmarker, 'scale', 0.01), delay=0.1)
        show_hitmarker()
        
# -----------------------
# RELOAD
# -----------------------

def reload():
    global reloading

    if reloading:
        return

    reloading = True
    reload_sfx.play()
    invoke(finish_reload, delay=1.2)


def finish_reload():
    global reloading
    weapons[current_weapon]["ammo"] = weapons[current_weapon]["mag"]
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
# UPDATE LOOP (STABLE CORE)
# -----------------------

def update():
    global pitch, recoil, target_recoil

    update_guns()

    # -----------------------
    # LOOK (ONLY SYSTEM CONTROLLING CAMERA)
    # -----------------------
    player.rotation_y += mouse.velocity[0] * 40

    pitch -= mouse.velocity[1] * 40
    pitch = clamp(pitch, -90, 90)
    camera.rotation_x = pitch

    # -----------------------
    # RECOIL (SMOOTH + SAFE)
    # -----------------------
    # smooth recoil decay
    target_recoil = lerp(target_recoil, Vec3(0, 0, 0), 8 * time.dt)
    recoil = lerp(recoil, target_recoil, 12 * time.dt)

    # apply ONLY to camera pitch (vertical)
    pitch -= recoil.y * 0.6
    pitch = clamp(pitch, -90, 90)
    camera.rotation_x = pitch

    # tiny horizontal camera sway (NOT player rotation)
    camera.rotation_y = recoil.x * 2

    # -----------------------
    # ENEMIES
    # -----------------------
    for e in enemies:
        if e and distance(e.position, player.position) < 20:
            e.look_at(player.position)
            e.position += e.forward * time.dt

    # HUD update
    w = weapons[current_weapon]

    ammo_text.text = f"{w['ammo']} / {w['mag']}"
    weapon_text.text = current_weapon.upper()

    hp = 100
    hp_bar.scale_x = 0.3 * (hp / 100)


app.run()