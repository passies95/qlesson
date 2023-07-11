# -*- coding: utf-8 -*-
"""
/***************************************************************************
helper_functions.py
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
import uuid

from qgis.utils import iface

# import the lesson_utils.py
from . import lesson_utils as utils


def loadProject(projectPath):
    root = os.path.dirname(projectPath)
    fileName = os.path.basename(projectPath)
    tmp = os.path.join(utils.tempDirectory(), uuid.uuid4().hex)
    shutil.copytree(root, tmp)
    iface.addProject(os.path.join(tmp, fileName))
