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
        self.photo_path = None
        self.initial_pos = None
        self.getmap.clicked.connect(self.get_map)

    def get_map(self) -> None:
        latitude, longitude = self.latitude.text(), self.longitude.text()
        try:
            latitude, longitude = float(latitude.replace(',', '.')), float(longitude.replace(',', '.'))

        except ValueError:
            msgBox = QMessageBox()
            msgBox.setWindowTitle('Ошибка!')
            msgBox.setText("Некорректные значения ширины или долготы.")
            msgBox.exec()

        else:
            zoom = self.zoom.value()
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
                self.image.setPixmap(QPixmap.fromImage(QImage('res.jpg')))
                os.remove('res.jpg')
            else:
                self.image.setPixmap(QPixmap.fromImage(QImage('src/logo.png')))
                msgBox = QMessageBox()
                msgBox.setWindowTitle('Ошибка!')
                msgBox.setText("Ошибка при выполнении запроса, проверьте корректность указанных координат.")
                msgBox.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = Application()
    widget.show()
    sys.exit(app.exec())
