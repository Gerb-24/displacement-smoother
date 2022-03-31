import os
from main import main_func
from errors import NoTopDisplacement,TopTextureUsedForNonDisp

dir = "C:\Program Files (x86)\Steam\steamapps\common\Team Fortress 2\my maps\python\displacement_editor_vmfs"
filepath = os.path.join(dir, "disp_prototype_duplicate.vmf")
sideTexture = "dev/dev_blendmeasure2"
topTexture = "customdev/dev_measurewall01blu"
try:
    main_func(filepath, topTexture, sideTexture)
except TopTextureUsedForNonDisp:
    print("hello!")
