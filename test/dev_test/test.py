import pandas as pd
from bokeh import plotting, embed, resources
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets


class Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)

        button = QtWidgets.QPushButton("Submit")
        self.m_output = QtWebEngineWidgets.QWebEngineView()

        button.clicked.connect(self.on_button_clicked)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(button)
        lay.addWidget(self.m_output)
        self.resize(640, 480)

    @QtCore.pyqtSlot()
    def on_button_clicked(self):
        p = plotting.figure(plot_width=300, plot_height=300)
        data = {"Day": [0, 1, 2, 3, 0, 1], "Num": [0, 0, 1, 1, 2, 3]}
        df = pd.DataFrame(data)
        p.hexbin(df.Day, df.Num, size=0.5)
        html = embed.file_html(p, resources.CDN, "my plot")
        self.m_output.setHtml(html)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    w = Widget()
    w.show()

    sys.exit(app.exec_())

###############################################################################

# from PyQt5 import QtCore, QtGui, QtWidgets,QtWebEngineWidgets
# import os
# class Ui_Dialog(object):
#     def setupUi(self, Dialog):
#         Dialog.setObjectName("Dialog")
#         Dialog.resize(400, 300)
#         self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
#         self.verticalLayout.setObjectName("verticalLayout")
#         self.centralwidget = QtWidgets.QWidget(Dialog)
#         self.centralwidget.setObjectName("centralwidget")
#         self.webEngineView = QtWebEngineWidgets.QWebEngineView(self.centralwidget)
#         self.webEngineView.load(QtCore.QUrl().fromLocalFile("/home/fabien/GPX_Tool/test.html"))
#         self.verticalLayout.addWidget(self.webEngineView)
#         self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
#         self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
#         self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
#         self.buttonBox.setObjectName("buttonBox")
#         self.verticalLayout.addWidget(self.buttonBox)
#         self.retranslateUi(Dialog)
#         self.buttonBox.accepted.connect(Dialog.accept)
#         self.buttonBox.rejected.connect(Dialog.reject)
#         QtCore.QMetaObject.connectSlotsByName(Dialog)
        
#     def retranslateUi(self, Dialog):
#         _translate = QtCore.QCoreApplication.translate
#         Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        
# if __name__ == "__main__":
#     import sys
#     app = QtWidgets.QApplication(sys.argv)
#     Dialog = QtWidgets.QDialog()
#     ui = Ui_Dialog()
#     ui.setupUi(Dialog)
#     Dialog.show()
#     sys.exit(app.exec_())

###############################################################################

# import sys
# from PyQt5 import uic
# from PyQt5.QtCore import *
# from PyQt5.QtGui import *
# from PyQt5.QtWidgets import *
# from PyQt5.QtWebEngineWidgets import *

# class Main(QWidget):

#     def __init__(self):
#         super().__init__()
#         self.initUI()

#     def initUI(self):
#         self.setWindowTitle('Name')
#         self.setWindowIcon(QIcon('icon.png'))

#         web = QWebEngineView()

#         web.load(QUrl("https://google.com"))

#         self.btn = QPushButton('Button', self)
#         self.btn.resize(self.btn.sizeHint())
#         lay = QVBoxLayout(self)
#         lay.addWidget(self.btn)
#         lay.addWidget(web)

# app = QApplication(sys.argv)
# main = Main()
# main.show()
# app.exec_()

###############################################################################

# # main.py
# import sys
# import os
# from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets


# class Browser(QtWebEngineWidgets.QWebEngineView):

#     def __init__(self):
#         super().__init__()

#         html = """
#         <!DOCTYPE html>
#         <html>
#             <head>
#                 <title>Example</title>
#                 <meta charset="utf-8" />
#             </head>
#             <body>
#                 <script>alert('Running some Javascript');</script>
#                 <h1>Hello world!</h1>
#                 <p>Goodbye, cruel world...</p>
#             </body>
#         </html>

#         """

#         # With QWebEnginePage.setHtml, the html is loaded immediately.
#         # baseUrl is used to resolve relative URLs in the document.
#         # For whatever reason, it seems like the baseUrl resolves to
#         # the parent of the path, not the baseUrl itself.  As a
#         # workaround, either append a dummy directory to the base url
#         # or start all relative paths in the html with the current
#         # directory.
#         # https://doc-snapshots.qt.io/qtforpython-5.15/PySide2/QtWebEngineWidgets/QWebEnginePage.html#PySide2.QtWebEngineWidgets.PySide2.QtWebEngineWidgets.QWebEnginePage.setHtml
#         # here = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
#         # base_path = os.path.join(os.path.dirname(here), 'src/app/map.html').replace('\\', '/')
#         self.url = QtCore.QUrl("file:///home/fabien/GPX_Tool/src/app/map.html")
#         self.page().setHtml(html, baseUrl=self.url)


# class MainWindow(QtWidgets.QMainWindow):

#     def __init__(self):
#         super().__init__()

#         self.init_widgets()
#         self.init_layout()

#     def init_widgets(self):
#         self.browser = Browser()
#         self.browser.loadFinished.connect(self.load_finished)

#     def init_layout(self):
#         layout = QtWidgets.QVBoxLayout()
#         layout.addWidget(self.browser)

#         centralWidget = QtWidgets.QWidget()
#         centralWidget.setLayout(layout)
#         self.setCentralWidget(centralWidget)

#     def load_finished(self, status):
#         self.msg = QtWidgets.QMessageBox()
#         self.msg.setIcon(QtWidgets.QMessageBox.Information)
#         self.msg.setWindowTitle('Load Status')
#         self.msg.setText(f"It is {str(status)} that the page loaded.")
#         self.msg.show()


# if __name__ == '__main__':
#     app = QtWidgets.QApplication(sys.argv)
#     main_window = MainWindow()
#     main_window.show()
#     sys.exit(app.exec_())

###############################################################################

# import sys
# import os
# # import site
# # site.addsitedir('/usr/local/lib/python2.7/site-packages')
# from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets

# app = QtWidgets.QApplication(sys.argv)
# view = QtWebEngineWidgets.QWebEngineView()

# # view.settings().setAttribute(QtWebEng.QWebSettings.LocalContentCanAccessRemoteUrls, True)

# # f = open('html/test.html', 'r')
# #
# # html = f.read()
# # f.close()

# # print(os.path.abspath(__file__))
# # path = os.path.abspath(__file__)
# # print()

# # view.setHtml(html)
# # view.setHtml(html, baseUrl=QtCore.QUrl().fromLocalFile(os.path.split(os.path.abspath(__file__))))

# # view.setUrl()
# # view.set
# # view.load(QtCore.QUrl('http://'))

# view.load(QtCore.QUrl().fromLocalFile("/home/fabien/GPX_Tool/test.html"))

# view.show()
# sys.exit(app.exec_())