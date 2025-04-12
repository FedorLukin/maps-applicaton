from PyQt6 import uic
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
        self.image.setPixmap(QPixmap.fromImage(QImage('src/logo.png')))
        self.getmap.clicked.connect(self.get_map)
        self.current_map = None

    def get_map(self) -> None:
        latitude, longitude = self.latitude.text(), self.longitude.text()
        zoom = self.zoom.value()

        try:
            latitude, longitude = float(latitude.replace(',', '.')), float(longitude.replace(',', '.'))
            if int(latitude) not in range(-85, 86) or int(longitude) not in range(-180, 181):
                raise ValueError

            if self.current_map == (latitude, longitude, zoom):
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
                "size": '450,450'
            }

            map_api_server = "https://static-maps.yandex.ru/v1"
            response = requests.get(map_api_server, params=map_params)
            if response.ok:
                with open('res.jpg', 'wb') as file:
                    file.write(response.content)
                self.current_map = (latitude, longitude, zoom)
                self.image.setPixmap(QPixmap.fromImage(QImage('res.jpg')))
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
        return super().keyPressEvent(event)
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = Application()
    widget.show()
    sys.exit(app.exec())