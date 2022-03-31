from PyQt6.QtWidgets import QFileDialog
import ast
import os

def load_vmf(self):
    filepath, _ = QFileDialog.getOpenFileName(self, "Load File", self.dirName, "VMF(*.vmf)")
    if filepath == "":
        return
    else:
        self.fileName = filepath
        self.fileNameLe.setText(os.path.basename(filepath))
        self.styleLog("standard")
        self.compileLogTe.setText('''
Ready to compile''')
        save_vmf_dir(self, filepath)

def save_vmf_dir(self, filepath):
    dirName = os.path.dirname(filepath)
    self.dirName = dirName
    with open("settings.txt", "w") as text:
        save_tex_dict = {
        'dirName':      self.dirName,
        'topTexture':   self.topTexture,
        'sideTexture':  self.sideTexture,
        }
        text.writelines(str(save_tex_dict))
        text.close()

def save_tex(self):
    with open("settings.txt", "w") as text:
        save_tex_dict = {
        'dirName':      self.dirName,
        'topTexture':   self.topTexture,
        'sideTexture':  self.sideTexture,
        }
        text.writelines(str(save_tex_dict))
        text.close()

def load_tex(self):
    with open("settings.txt", "r") as text:
        load_tex_dict = ast.literal_eval(text.readline())
        self.dirName = load_tex_dict["dirName"]
        self.topTextureLe.setText(load_tex_dict["topTexture"])
        self.sideTextureLe.setText(load_tex_dict["sideTexture"])
