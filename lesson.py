# -*- coding: utf-8 -*-
"""
/***************************************************************************
lesson.py
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
import importlib
import importlib.util
import traceback

import yaml

from qgis.PyQt.QtCore import Q_ENUMS, QCoreApplication
from qgis.core import QgsApplication, QgsMessageLog

from .helper_functions import loadProject
from .lesson_utils import menuByName


class LessonStep:

    class StepType:
        Manual = 0
        Menu = 1
        Automated = 2

    class FunctionType:
        Prepare = 0
        Execute = 1
        Check = 2

    Q_ENUMS(StepType)
    Q_ENUMS(FunctionType)

    def __init__(self, name, description, prepare=None, execute=None,
                 check=None, parameters=None, stepType=StepType.Manual):
        self.name = name
        self.description = description

        self.prepare = prepare
        self.execute = execute
        self.check = check
        self.parameters = parameters

        self.type = stepType

        self.signal = None
        self.handler = None

    def runFunction(self, functionType):
        params = self.functionParameters(functionType)

        if functionType == LessonStep.FunctionType.Prepare:
            return self.prepare(*params)
        elif functionType == LessonStep.FunctionType.Execute:
            return self.execute(*params)
        elif functionType == LessonStep.FunctionType.Check:
            return self.check(*params)

    def functionParameters(self, functionType):
        if functionType in self.parameters:
            return self.parameters[functionType]
        else:
            return tuple()

    def addSignalHandler(self, signal, handler):
        self.signal = signal
        self.handler = handler

class Lesson:

    def __init__(self, name, displayName, groupId, group, description, root=None):
        self.name = name
        self.groupId = groupId
        self.id = '{}:{}'.format(groupId, name)

        self.root = root

        self.displayName = displayName
        self.group = group
        self.description = self._findFile(description)

        self.steps = list()
        self.recommended = list()

        # add step to load QGIS project with lesson data, if any
        projectFile = os.path.join(self.root, 'data',  'project.qgs')
        if os.path.isfile(projectFile):
            self.addStep(self.tr('Open project'),
                         self.tr('Open project with lesson data.'),
                         execDefinition=lambda: loadProject(projectFile),
                         stepType=LessonStep.StepType.Automated)

    def addStep(self, name, description, prepDefinition=None, execDefinition=None, checkDefinition=None,
                stepType=LessonStep.StepType.Manual):
        prepare = None
        execute = None
        check = None

        parameters = dict()
        if prepDefinition is not None:
            prepare, p = self._findFunction(prepDefinition)
            parameters[LessonStep.FunctionType.Prepare] = p

        if execDefinition is not None:
            execute, p = self._findFunction(execDefinition)
            parameters[LessonStep.FunctionType.Execute] = p

        if checkDefinition is not None:
            check, p = self._findFunction(checkDefinition)
            parameters[LessonStep.FunctionType.Check] = p

        description = self._findFile(description)

        step = LessonStep(name, description, prepare, execute, check, parameters, stepType)
        self.steps.append(step)

    def addMenuStep(self, menuString, name='', description=''):
        action, parentMenu = menuByName(menuString)

        if action is None:
           raise Exception(self.tr('Can not find menu "{}".'.format(menuString)))

        if not name:
            name = 'Click on menu item'

        if description:
            description = self._findFile(description)
        else:
            description = 'Go to menu "{}". Once you click lesson will move to the next step.'.format(menuString.replace('&', '').replace('|', '→'))

        def _actionTriggered(sender):
            return sender.text() == action.text()

        step = LessonStep(name, description, stepType=LessonStep.StepType.Menu)
        step.addSignalHandler(parentMenu.triggered, _actionTriggered)
        self.steps.append(step)

    def addRecommendation(self, nameId, groupId):
        self.recommended.append((nameId, groupId))

    def setCleanupFunction(self, function):
        self.cleanup = function

    def _findFile(self, fileName):
        if fileName is None:
            return ''

        if os.path.splitext(fileName)[1] != '.html':
            return fileName

        for locale in [QgsApplication.locale(), 'en']:
            # first look for a localized version and fallback
            # to English in case of failure
            if not os.path.exists(os.path.join(locale, fileName)):
                path = os.path.join(self.root, locale, fileName)
                if os.path.exists(path):
                    return path

        # lesson without i18n support, file located in the root
        #return os.path.join(self.root, fileName)
        return ''

    def _findFunction(self, definition):
        if isinstance(definition, dict):
            if 'params' in definition:
                params = tuple(definition['params'])
            else:
                params = tuple()

            if definition['name'].startswith('functions.'):
                functionName = definition['name'].split('.')[1]
                function = getattr(importlib.import_module('lessons.functions'), functionName)
            else:
                spec = importlib.util.spec_from_file_location('functions', os.path.join(self.root, 'functions.py'))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                function = getattr(module, definition['name'])

            return function, params
        else:
            return definition, tuple()

    def tr(self, text):
        return QCoreApplication.translate('Lesson', text)

    @classmethod
    def fromYaml(cls, lessonFile):
        locale = QgsApplication.locale()

        with open(lessonFile, encoding='utf-8') as f:
            data = yaml.load(f)

        name = data['lesson']['name']
        groupId = data['lesson']['groupId']

        if locale in data['lesson']:
            definition = data['lesson'][locale]
        else:
            definition = data['lesson']['en']

        lesson = Lesson(name,
                        definition['displayName'],
                        groupId,
                        definition['group'],
                        definition['description'],
                        os.path.abspath(os.path.dirname(lessonFile)))

        # add lesson steps
        for step in definition['steps']:
            if 'menu' in step:
                # QGIS main menu interaction
                name = None
                description = None
                if 'name' in step:
                    name = step['name']

                if 'description' in step:
                    description = step['description']

                try:
                    lesson.addMenuStep(step['menu'], name, description)
                except Exception as e:
                    logmessage = cls.tr('Can not load lesson from {}:\n{}'.format(lessonFile, traceback.format_exc()))
                    QgsMessageLog.logMessage(logmessage, 'QLesson')
                    return None
            else:
                # all other steps
                prepare = None
                execute = None
                check = None

                if 'prepare' in step:
                    prepare = step['prepare']

                if 'execute' in step:
                    execute = step['execute']

                if 'check' in step:
                    check = step['check']

                try:
                    lesson.addStep(step['name'], step['description'],
                                   prepare, execute, check)
                except Exception as e:
                    QgsMessageLog.logMessage(cls.tr('Can not load lesson from {}:\n{}'.format(lessonFile, traceback.format_exc())), 'QLesson')
                    return None

        # add recommended lessons, if any
        if 'recommended' in data['lesson']:
            for r in data['lesson']['recommended']:
                lesson.addRecommendation(r['groupId'], r['name'])

        return lesson

    @staticmethod
    def idFromYaml(lessonFile):
        with open(lessonFile, encoding='utf-8') as f:
            data = yaml.load(f)

        name = data['lesson']['name']
        groupId = data['lesson']['groupId']
        return '{}:{}'.format(groupId, name)
