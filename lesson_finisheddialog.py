# -*- coding: utf-8 -*-

"""
***************************************************************************
    lesson_finisheddialog.py
    ---------------------
    Date                 : July 2023
    Copyright            : (C) 2023 by Pascal Ogola
    Email                : passies95 at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Pascal Ogola'
__date__ = 'July 2023'
__copyright__ = '(C) 2023, Pascal Ogola'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt import uic

from . import lessonsRegistry

pluginPath = current_dir = os.path.dirname(__file__)
WIDGET, BASE = uic.loadUiType(os.path.join(pluginPath, 'lesson_finisheddialog.ui'))


class LessonFinalizedDialog(BASE, WIDGET):

    def __init__(self, parent=None):
        super(LessonFinalizedDialog, self).__init__(parent)
        self.setupUi(self)

        self.lesson = None

        self.txtRecommendedLesson.anchorClicked.connect(self.selectRecommendedLesson)

    def setRecommendedLesson(self, recommended):
        text = self.tr('<p><strong>Congratulations! You have successfully finished this lesson.</strong></p>'
                       '<p>Close this dialog to go back to the lessons library.</p>')

        if recommended:
            items = list()
            for item in recommended:
                lessonId = '{}:{}'.format(item[0], item[1])
                lesson = lessonsRegistry.lessonById(lessonId)
                if lesson:
                    items.append('<li><a href="{}">{}</a></li>'.format(lessonId, lesson.displayName))

            if items:
                intro = self.tr('<p><strong>Congratulations! You have successfully finished this lesson.</strong></p>'
                                '<p>The lesson\'s author(s) also recommend to complete following lessons:</p>')
                final = self.tr('You can either close this dialog and go back to the '
                                'lessons library or select one of the recommended lessons.')
                text = '{}<ul>{}</ul>{}'.format(intro, ''.join(items), final)

        self.txtRecommendedLesson.setHtml(text)

    def selectRecommendedLesson(self, url):
        self.lesson = lessonsRegistry.lessonById(url.toString())
        self.accept()
