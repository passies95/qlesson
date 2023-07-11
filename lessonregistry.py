# -*- coding: utf-8 -*-
"""
/***************************************************************************
lessonregistry.py
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
import zipfile

from qgis.core import QgsApplication, QgsSettings, QgsMessageLog
from qgis.PyQt.QtCore import QCoreApplication

from .lesson import Lesson
from . import lesson_utils as utils

pluginPath = os.path.dirname(__file__)


class QLessonRegistry:

    def __init__(self):
        self.groups = dict()
        self.lessons = dict()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(QLessonRegistry, cls).__new__(cls)

        return cls.instance

    def loadLessons(self, lessonpathlist):
        # load built-in lessons
        self._loadFromDirectory(lessonpathlist[0])

        # load lessons from other user directories
        for directory in lessonpathlist[1:]:
            if os.path.exists(directory):
                for entry in os.scandir(directory):
                    if entry.is_file():
                        continue

                    self._loadFromDirectory(entry.path)

    def addLessonsDirectory(self, directory):
        self._loadFromDirectory(directory)

    def removeLessonsDirectory(self, directory):
        for entry in os.scandir(directory):
            if utils.isLesson(os.path.join(directory, entry.name)):
                lessonId = Lesson.idFromYaml(os.path.join(directory, entry.name, 'lesson.yaml'))
                if lessonId:
                    self._removeLesson(lessonId)

    def lessonById(self, lessonId):
        group, name = lessonId.split(':')

        if group in self.lessons and lessonId in self.lessons[group]:
            return self.lessons[group][lessonId]

        return None

    def installLessonsFromZip(self, filePath):
        # TODO: allow multiple groups inside archive
        pathsList = QgsSettings().value('qlesson/lessonsPaths',
                                        [os.path.join(QgsApplication.qgisSettingsDirPath(), 'lessons')])

        if not os.path.exists(pathsList[0]):
            os.makedirs(pathsList[0])

        with zipfile.ZipFile(filePath, 'r') as zf:
            zf.extractall(pathsList[0])

        dirName = os.path.splitext(filePath)[0]
        self._loadFromDirectory(os.path.join(pathsList[0], dirName))
        return True

    def uninstallLesson(self, lessonId):
        lesson = self.lessonById(lessonId)
        if lesson:
            lessonsPath = QgsSettings().value('qlesson/lessonsPath',
                                              os.path.join(QgsApplication.qgisSettingsDirPath(), 'lessons'), str)
            # only user lessons can be uninstalled
            if not lesson.root.startswith(lessonsPath):
                QgsMessageLog.logMessage(self.tr('Lesson "{}" is not a user lesson and can not be uninstalled.'.format(lesson.name)))
                return False

            rootDirectory = lesson.root
            self._removeLesson(lessonId)
            shutil.rmtree(rootDirectory)
            return True

    def _loadFromDirectory(self, directory):
        for lessonDir in os.scandir(directory):
            root = os.path.join(directory, lessonDir.name)
            if utils.isLesson(root):
                lesson = Lesson.fromYaml(os.path.join(root, 'lesson.yaml'))
                if lesson:
                    self._addLesson(lesson)

    def _addLesson(self, lesson):
        groupId = lesson.groupId
        if groupId not in self.groups:
            self.groups[groupId] = lesson.group
            self.lessons[groupId] = {}

        if lesson.name in self.lessons[groupId]:
            QgsMessageLog.logMessage(self.tr('Duplicate lesson name "{}" for group "{}"'.format(lesson.name, groupId)))
            return

        self.lessons[groupId][lesson.id] = lesson

    def _removeLesson(self, lessonId):
        groupId, name = lessonId.split(':')
        if groupId not in self.groups:
            return

        if name in self.lessons[groupId]:
            del self.lessons[groupId][name]
            if len(self.lessons[groupId]) == 0:
                del self.lessons[groupId]
                del self.groups[groupId]

    def tr(self, text):
        return QCoreApplication.translate('LessonRegistry', text)
