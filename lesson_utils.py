# -*- coding: utf-8 -*-
"""
/***************************************************************************
lesson_utils.py
    ---------------------
        Date                 : 2023-07-07
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Pascal Ogola
        email                : passies95@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Pascal Ogola'
__date__ = 'July 2023'
__copyright__ = '(C) 2023, Pascal Ogola'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import shutil
import tempfile

from qgis.utils import iface


def tempDirectory():
    tmpPath = os.path.join(tempfile.gettempdir(), 'qlesson')
    if not os.path.exists(tmpPath):
        os.mkdir(tmpPath)

    return tmpPath


def removeTemporaryFiles():
    shutil.rmtree(tempDirectory(), True)


def menuByName(menuString):
    menu = None
    action = None

    tokens = menuString.split('|')
    actions = iface.mainWindow().menuBar().actions()

    for t in tokens:
        for a in actions:
            if a.text().replace('&', '') == t:
                if a.menu():
                    menu = a.menu()
                    actions = menu.actions()
                    break
                else:
                    action = a

    return action, menu


def isLesson(dirName):
    return os.path.isdir(dirName) and os.path.isfile(os.path.join(dirName, 'lesson.yaml'))
