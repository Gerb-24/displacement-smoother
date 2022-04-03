import sys
import traceback
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QTextEdit, QVBoxLayout
from PyQt6 import uic, QtCore
from PyQt6.QtGui import QIcon
from filemanagement import load_vmf, save_tex, load_tex
from main import main_func
from errors import NoTopTexture, TopTextureUsedForNonDisp, SideTextureUsedForNonDisp



class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('gui.ui', self)
        self.setWindowTitle("Displacement Smoother")
        self.setWindowIcon(QIcon('appicon.ico'))
        self.setFixedSize(self.size())


        # initial values
        self.fileName = ""
        self.dirName = ""
        self.topTexture = ""
        self.sideTexture = ""
        self.compileLogTe.setText('''
Open vmf before compiling''')

        # handling events
        self.topTextureLe.textChanged.connect(lambda: self.topTexture_setter(self.topTextureLe.text()))
        self.sideTextureLe.textChanged.connect(lambda: self.sideTexture_setter(self.sideTextureLe.text()))

        self.openFileBtn.clicked.connect(lambda: load_vmf(self))
        self.savePreferencesBtn.clicked.connect(lambda: save_tex(self))
        self.compileBtn.clicked.connect( self.compile )

        load_tex(self)

        self.smoothRBtnList = [
            self.smooth0RBtn,
            self.smooth1RBtn,
            self.smooth2RBtn,
            self.smooth3RBtn,
        ]

        for btn_index in range(len(self.smoothRBtnList)):
            btn = self.smoothRBtnList[btn_index]
            if btn_index == 0:
                radio_style = f"""
                QRadioButton#smooth{btn_index}RBtn::indicator::unchecked {{
                    image: url(ui_images/smooth{btn_index}_disabled.png);
                }}
                """
            else:
                radio_style = f"""
                QRadioButton#smooth{btn_index}RBtn::indicator::unchecked {{
                    image: url(ui_images/smooth{btn_index}_unchecked.png);
                }}
                QRadioButton#smooth{btn_index}RBtn::indicator::checked {{
                    image: url(ui_images/smooth{btn_index}_checked.png);
                }}
                """
            btn.setStyleSheet(radio_style)

    def topTexture_setter( self, text ):
        self.topTexture = text

    def sideTexture_setter( self, text ):
        self.sideTexture = text
        
    def compile( self ):
        def smoothness_returner():
            for btn_index in range(len(self.smoothRBtnList)):
                btn = self.smoothRBtnList[btn_index]
                if btn.isChecked():
                    return btn_index

        smoothness = smoothness_returner()
        self.compileLogTe.setText("Compiling...")
        self.styleLog("standard")

        try:
            main_func( self.fileName, self.topTexture, self.sideTexture, smoothness )
            self.styleLog("succes")
            self.compileLogTe.setText('''
Compiled succesfully.''')
        except NoTopTexture:
            self.styleLog("error")
            self.compileLogTe.setText('''
Compile Error: NoTopTexture
It seems like you forgot to use the toptexture for some top displacements.''')
        except TopTextureUsedForNonDisp:
            self.styleLog("error")
            self.compileLogTe.setText('''
Compile Error: TopTextureUsedForNonDisp
It seems like you used the toptexture on a face that has no displacement on it.''')
        except SideTextureUsedForNonDisp:
            self.styleLog("error")
            self.compileLogTe.setText('''
Compile Error: SideTextureUsedForNonDisp
It seems like you used the sidetexture on a face that has no displacement on it.''')
        except Exception as e:
            print(traceback.format_exc())
            self.styleLog("error")
            self.compileLogTe.setText('''
Compile Error: GeneralError
Something seems to be going wrong. Check if everything looks fine in the vmf''')
    def styleLog( self, type: str):
        if type == "standard":
            self.compileLogTe.setStyleSheet('''
                QTextEdit {
                    background-color: #95a5a6;
                    color: #34495e;
                }
                ''')
        elif type == "error":
            self.compileLogTe.setStyleSheet('''
                QTextEdit {
                    background-color: #e74c3c;
                    color: #ecf0f1;
                }
                ''')
        elif type == "succes":
            self.compileLogTe.setStyleSheet('''
                QTextEdit {
                    background-color: #27ae60;
                    color: #ecf0f1;
                }
                ''')

if __name__ == '__main__':
    app = QApplication(sys.argv)

    app.setStyleSheet(open('stylesheet.css').read())

    window = MyApp()
    window.show()
    try:
        sys.exit(app.exec())
    except SystemExit:
        print(' Closing Window ... ')
