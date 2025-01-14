#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2018 Andy Stewart
#
# Author:     Andy Stewart <lazycat.manatee@gmail.com>
# Maintainer: Andy Stewart <lazycat.manatee@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from core.utils import get_local_ip, get_free_port, get_emacs_var, message_to_emacs
import subprocess
import os
import qrcode
import signal
import tempfile
import uuid

from core.buffer import Buffer

class AppBuffer(Buffer):
    def __init__(self, buffer_id, url, argument):
        Buffer.__init__(self, buffer_id, url, argument, False)

        self.background_color = QColor(get_emacs_var("eaf-emacs-theme-background-color"))

        self.add_widget(FileUploaderWidget(url,
                                           get_emacs_var("eaf-emacs-theme-background-color"),
                                           get_emacs_var("eaf-emacs-theme-foreground-color")))

    def destroy_buffer(self):
        os.kill(self.buffer_widget.background_process.pid, signal.SIGKILL)

        super().destroy_buffer()

        message_to_emacs("Stop: {0} -> {1}".format(self.buffer_widget.address, self.buffer_widget.url))

class Image(qrcode.image.base.BaseImage):
    def __init__(self, border, width, box_size):
        self.border = border
        self.width = width
        self.box_size = box_size
        size = (width + border * 2) * box_size
        self._image = QtGui.QImage(size, size, QtGui.QImage.Format_RGB16)
        self._image.fill(QtCore.Qt.white)

    def pixmap(self):
        return QtGui.QPixmap.fromImage(self._image)

    def drawrect(self, row, col):
        painter = QtGui.QPainter(self._image)
        painter.fillRect(
            (col + self.border) * self.box_size,
            (row + self.border) * self.box_size,
            self.box_size, self.box_size,
            QtCore.Qt.black)

    def save(self, stream, kind=None):
        pass

class FileUploaderWidget(QWidget):
    def __init__(self, url, background_color, foreground_color):
        QWidget.__init__(self)

        self.setStyleSheet("background-color: transparent;")

        self.url = os.path.expanduser(url)

        self.file_name_font = QFont()
        self.file_name_font.setPointSize(24)

        self.file_name_label = QLabel()
        self.file_name_label.setText("Your smartphone file will be shared at\n{0}".format(url))
        self.file_name_label.setFont(self.file_name_font)
        self.file_name_label.setAlignment(Qt.AlignCenter)
        self.file_name_label.setStyleSheet("color: {}".format(foreground_color))

        self.qrcode_label = QLabel()

        self.notify_font = QFont()
        self.notify_font.setPointSize(12)
        self.notify_label = QLabel()
        self.notify_label.setText("Scan the QR code above to upload a file from your smartphone.\nMake sure the smartphone is connected to the same WiFi network as this computer.")
        self.notify_label.setFont(self.notify_font)
        self.notify_label.setAlignment(Qt.AlignCenter)
        self.notify_label.setStyleSheet("color: {}".format(foreground_color))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(self.qrcode_label, 0, Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.file_name_label, 0, Qt.AlignCenter)
        layout.addSpacing(40)
        layout.addWidget(self.notify_label, 0, Qt.AlignCenter)
        layout.addStretch()

        self.port = get_free_port()
        self.local_ip = get_local_ip()
        self.address = "http://{0}:{1}".format(self.local_ip, self.port)

        self.qrcode_label.setPixmap(qrcode.make(self.address, image_factory=Image).pixmap())

        tmp_db_file = os.path.join(tempfile.gettempdir(), "filebrowser-" + uuid.uuid1().hex + ".db")
        self.background_process = subprocess.Popen(
            "filebrowser --noauth -d {0} --address {1} -p {2}".format(tmp_db_file, self.local_ip, self.port),
            cwd=self.url,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True)
        message_to_emacs("Start: {0} -> {1}".format(self.address, self.url))
