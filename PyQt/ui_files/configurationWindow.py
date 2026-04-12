# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'configurationwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PyQt5.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PyQt5.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PyQt5.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QGroupBox, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QWidget)

class DialogConfiguration(object):
    def setupUi(self, DialogConfiguration):
        if not DialogConfiguration.objectName():
            DialogConfiguration.setObjectName(u"DialogConfiguration")
        DialogConfiguration.resize(400, 399)
        self.btn_ok_cancel = QDialogButtonBox(DialogConfiguration)
        self.btn_ok_cancel.setObjectName(u"btn_ok_cancel")
        self.btn_ok_cancel.setGeometry(QRect(210, 360, 171, 32))
        self.btn_ok_cancel.setOrientation(Qt.Horizontal)
        self.btn_ok_cancel.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.gb_origen = QGroupBox(DialogConfiguration)
        self.gb_origen.setObjectName(u"gb_origen")
        self.gb_origen.setGeometry(QRect(20, 10, 361, 80))
        self.label = QLabel(self.gb_origen)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(20, 10, 161, 16))
        self.txt_origen = QLineEdit(self.gb_origen)
        self.txt_origen.setObjectName(u"txt_origen")
        self.txt_origen.setGeometry(QRect(20, 40, 261, 23))
        self.btn_examinar_origen = QPushButton(self.gb_origen)
        self.btn_examinar_origen.setObjectName(u"btn_examinar_origen")
        self.btn_examinar_origen.setGeometry(QRect(290, 40, 61, 23))
        self.gb_destino = QGroupBox(DialogConfiguration)
        self.gb_destino.setObjectName(u"gb_destino")
        self.gb_destino.setGeometry(QRect(20, 100, 361, 80))
        self.label_3 = QLabel(self.gb_destino)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(20, 10, 161, 16))
        self.txt_destino = QLineEdit(self.gb_destino)
        self.txt_destino.setObjectName(u"txt_destino")
        self.txt_destino.setGeometry(QRect(20, 40, 261, 23))
        self.btn_examinar_destino = QPushButton(self.gb_destino)
        self.btn_examinar_destino.setObjectName(u"btn_examinar_destino")
        self.btn_examinar_destino.setGeometry(QRect(290, 40, 61, 23))
        self.gb_unidad = QGroupBox(DialogConfiguration)
        self.gb_unidad.setObjectName(u"gb_unidad")
        self.gb_unidad.setGeometry(QRect(20, 190, 171, 71))
        self.label_4 = QLabel(self.gb_unidad)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(20, 10, 101, 16))
        self.cb_unidad = QComboBox(self.gb_unidad)
        self.cb_unidad.setObjectName(u"cb_unidad")
        self.cb_unidad.setGeometry(QRect(20, 30, 69, 22))
        self.gb_pantalla = QGroupBox(DialogConfiguration)
        self.gb_pantalla.setObjectName(u"gb_pantalla")
        self.gb_pantalla.setGeometry(QRect(210, 190, 171, 71))
        self.label_5 = QLabel(self.gb_pantalla)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(20, 10, 91, 16))
        self.cb_pantalla = QComboBox(self.gb_pantalla)
        self.cb_pantalla.setObjectName(u"cb_pantalla")
        self.cb_pantalla.setGeometry(QRect(20, 30, 141, 22))
        self.gb_compartir = QGroupBox(DialogConfiguration)
        self.gb_compartir.setObjectName(u"gb_compartir")
        self.gb_compartir.setGeometry(QRect(20, 270, 361, 80))
        self.txt_correo = QLineEdit(self.gb_compartir)
        self.txt_correo.setObjectName(u"txt_correo")
        self.txt_correo.setGeometry(QRect(109, 8, 240, 23))
        self.label_6 = QLabel(self.gb_compartir)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(10, 10, 101, 16))
        self.label_7 = QLabel(self.gb_compartir)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(11, 42, 91, 16))
        self.txt_password = QLineEdit(self.gb_compartir)
        self.txt_password.setObjectName(u"txt_password")
        self.txt_password.setGeometry(QRect(110, 40, 240, 23))
        self.txt_password.setEchoMode(QLineEdit.Password)

        self.retranslateUi(DialogConfiguration)
        self.btn_ok_cancel.accepted.connect(DialogConfiguration.accept)
        self.btn_ok_cancel.rejected.connect(DialogConfiguration.reject)

        QMetaObject.connectSlotsByName(DialogConfiguration)
    # setupUi

    def retranslateUi(self, DialogConfiguration):
        DialogConfiguration.setWindowTitle(QCoreApplication.translate("DialogConfiguration", u"Configuraci\u00f3n", None))
        self.label.setText(QCoreApplication.translate("DialogConfiguration", u"Carpeta de origen de la copia:", None))
        self.btn_examinar_origen.setText(QCoreApplication.translate("DialogConfiguration", u"Examinar", None))
        self.label_3.setText(QCoreApplication.translate("DialogConfiguration", u"Carpeta destino de la copia:", None))
        self.btn_examinar_destino.setText(QCoreApplication.translate("DialogConfiguration", u"Examinar", None))
        self.label_4.setText(QCoreApplication.translate("DialogConfiguration", u"Unidad Temporal:", None))
        self.label_5.setText(QCoreApplication.translate("DialogConfiguration", u"Tipo de Pantalla:", None))
        self.gb_compartir.setTitle("")
        self.txt_correo.setText("")
        self.label_6.setText(QCoreApplication.translate("DialogConfiguration", u"Correo Electronico:", None))
        self.label_7.setText(QCoreApplication.translate("DialogConfiguration", u"Password:", None))
        self.txt_password.setText("")
    # retranslateUi

