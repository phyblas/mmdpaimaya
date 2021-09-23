# -*- coding: utf-8 -*-
import sys
from PySide2.QtWidgets import QApplication
from .gui import Natanglak

def yamikuma():
    qAp = QApplication.instance()
    if(qAp==None):
        qAp = QApplication(sys.argv)
    natanglak = Natanglak()
    natanglak.show()
    return natanglak
