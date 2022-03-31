import os

dir = "C:\Program Files (x86)\Steam\steamapps\common\Team Fortress 2\my maps\python\displacement_editor_vmfs"
filepath = os.path.join(dir, "disp_prototype.vmf")

with open(filepath, "r") as vmf:
    text = vmf.read()
    vmf.close()
filepath = os.path.join(dir, "disp_prototype_duplicate.vmf")

with open(filepath, "w") as vmf:
    vmf.writelines(text)
    vmf.close()
