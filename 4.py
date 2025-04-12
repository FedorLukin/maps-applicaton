from PyQt6 import uic
from PyQt6.QtCore import Qt, QPointF, QSize
from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from dotenv import load_dotenv
import requests
import sys
import os


class Application(QMainWindow):
    def __init__(self) -> None:
        load_dotenv()
        self.apikey = os.getenv('APIKEY')
        super().__init__()
        uic.loadUi('src/maps1.ui', self)
        self.setFixedSize(540, 690)
        self.setWindowIcon(QIcon('src/icon.png'))
        self.nightMode = False
        self.image.setPixmap(QPixmap.fromImage(QImage('src/logo.png')))
        self.getmap.clicked.connect(self.get_map)
        self.theme.clicked.connect(self.change_theme)
        self.current_map = None

    def change_theme(self) -> None:
        self.nightMode = not self.nightMode
        icon, background = ('night.png', 'background_dark.jpg') if self.nightMode else ('day.png', 'background.jpg')
        self.theme.setIcon(QIcon(f'src/{icon}'))
        self.setStyleSheet(f"QMainWindow {{background-image: url(src/{background});}}")
        self.theme.setIconSize(QSize(50, 50))
        if self.current_map:
            self.get_map()
        

    def get_map(self) -> None:
        latitude, longitude = self.latitude.text(), self.longitude.text()
        zoom = self.zoom.value()

        try:
            latitude, longitude = float(latitude.replace(',', '.')), float(longitude.replace(',', '.'))
            if int(latitude) not in range(-85, 86) or int(longitude) not in range(-180, 181):
                raise ValueError

            if self.current_map == (latitude, longitude, zoom, self.nightMode):
                return

        except ValueError:
            self.image.setPixmap(QPixmap.fromImage(QImage('src/logo.png')))
            self.current_map = None
            msgBox = QMessageBox()
            msgBox.setWindowTitle('Ошибка!')
            msgBox.setText("Некорректные значения ширины или долготы.")
            msgBox.exec()

        else:
            map_params = {
                "apikey": self.apikey,
                "ll": f'{longitude},{latitude}',
                "z": zoom,
                "size": '450,450',
                "theme": 'dark' if self.nightMode else 'light'
            }

            map_api_server = "https://static-maps.yandex.ru/v1"
            response = requests.get(map_api_server, params=map_params)
            if response.ok:
                with open('res.jpg', 'wb') as file:
                    file.write(response.content)
                self.current_map = (latitude, longitude, zoom, self.nightMode)
                self.image.setPixmap(QPixmap.fromImage(QImage('res.jpg')))
                self.image.setFocus()
                os.remove('res.jpg')
            else:
                self.image.setPixmap(QPixmap.fromImage(QImage('src/logo.png')))
                self.current_map = None
                msgBox = QMessageBox()
                msgBox.setWindowTitle('Ошибка!')
                msgBox.setText("Ошибка при выполнении запроса к api яндекс карт.")
                msgBox.exec()

    def keyPressEvent(self, event):
        if event.key() in (16777238, 16777239):
            dt = 1 if event.key() == 16777238 else -1
            if 1 <= self.zoom.value() + dt <= 20:
                self.zoom.setValue(self.zoom.value() + dt)
                if self.current_map:
                    self.get_map()

        elif self.image.hasFocus() and self.current_map:
            if event.key() == Qt.Key.Key_Left:
                lng = self.current_map[1]
                new_lng = lng - 180 / 2 ** self.zoom.value()
                new_lng = new_lng if new_lng > -180 else 180 - abs(new_lng) % 180
                self.longitude.setText(str(new_lng))
                self.current_map = None
            if event.key() == Qt.Key.Key_Right:
                lng = self.current_map[1]
                new_lng = lng + 180 / 2 ** self.zoom.value()
                new_lng = new_lng if new_lng < 180 else -180 + new_lng % 180
                self.longitude.setText(str(new_lng))
                self.current_map = None
            if event.key() == Qt.Key.Key_Up:
                ltd = self.current_map[0]
                new_ltd = ltd + 90 / 2 ** self.zoom.value()
                new_ltd = new_ltd if new_ltd < 90 else -90 + new_ltd % 90
                self.latitude.setText(str(new_ltd))
                self.current_map = None
            if event.key() == Qt.Key.Key_Down:
                ltd = self.current_map[0]
                new_ltd = ltd - 90 / 2 ** self.zoom.value()
                new_ltd = new_ltd if new_ltd < 90 else -90 + new_ltd % 90
                self.latitude.setText(str(new_ltd))
                self.current_map = None
            self.get_map()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            x, y = event.position().x(), event.position().y()
            if 45 <= x <= 495 and 10 <= y <= 460:
                self.image.setFocus()
            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = Application()
    widget.show()
    sys.exit(app.exec())