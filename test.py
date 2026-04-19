from ursina import *

app = Ursina()

print(">>> CLEAN TEST RUN <<<")

ground = Entity(model='cube', scale=(50,1,50), color=color.gray)

app.run()