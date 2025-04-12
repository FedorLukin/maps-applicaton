from PyQt6 import uic
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from dotenv import load_dotenv
import requests
import sys
import os


class Application(QMainWindow):
    def __init__(self) -> None:
        load_dotenv()
        self.static_apikey = os.getenv('STATIC_APIKEY')
        self.search_apikey = os.getenv('SEARCH_APIKEY')
        super().__init__()
        uic.loadUi('src/maps3.ui', self)
        self.setFixedSize(540, 690)
        self.image.setPixmap(QPixmap.fromImage(QImage('src/logo.png')))
        self.setWindowIcon(QIcon('src/icon.png'))
        self.info.setVisible(False) 
        self.clear.clicked.connect(self.clear_ui)
        self.getmap.clicked.connect(self.get_map)
        self.theme.clicked.connect(self.change_theme)
        self.nightMode = False
        self.current_map = None
        self.point = None

    def change_theme(self) -> None:
        self.nightMode = not self.nightMode
        icon, background = ('night.png', 'background_dark.jpg') if self.nightMode else ('day.png', 'background.jpg')
        logo, color = ('logo_dark.png', '#574e80') if self.nightMode else ('logo.png', '#e2393a')
        self.setStyleSheet(f'QMainWindow {{background-image: url(src/{background});}}')
        self.getmap.setStyleSheet(f'background-color: {color}; color: white')
        self.clear.setStyleSheet(f'background-color: {color}; color: white')
        self.image.setPixmap(QPixmap.fromImage(QImage(f'src/{logo}')))
        self.theme.setIcon(QIcon(f'src/{icon}'))
        self.theme.setIconSize(QSize(50, 50))
        if self.current_map:
            self.get_map_by_cords()

    def clear_ui(self) -> None:
        self.image.setPixmap(QPixmap.fromImage(QImage('src/logo.png')))
        self.address.setText('Введите адрес или координаты объекта')
        self.info.setVisible(False) 
        self.longitude.clear()
        self.latitude.clear()
        self.zoom.setValue(5)
        self.current_map = None

    def error_message(self, message: str) -> None:
        self.image.setPixmap(QPixmap.fromImage(QImage('src/logo.png')))
        self.current_map = None
        msgBox = QMessageBox()
        msgBox.setWindowTitle('Ошибка!')
        msgBox.setText(message)
        msgBox.exec()
    
    def get_map_by_cords(self, latitude: float = None, longitude: float = None, point=False) -> None:
        if not (latitude and longitude):
            latitude, longitude = self.latitude.text(), self.longitude.text()
            try:
                latitude, longitude = float(latitude.replace(',', '.')), float(longitude.replace(',', '.'))
                if int(latitude) not in range(-85, 86) or int(longitude) not in range(-180, 181):
                    raise ValueError

            except ValueError:
                self.error_message(message='Некорректные значения ширины или долготы.')
                return
            
        if point:
            self.point = f'{longitude},{latitude},vkbkm'

        zoom = self.zoom.value()
        if self.current_map == (latitude, longitude, zoom, self.nightMode):
            return

        map_params = {
            "apikey": self.static_apikey,
            "ll": f'{longitude},{latitude}',
            "z": zoom,
            "size": '450,450',
            "pt": self.point,
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
            print(response.url)
            self.error_message(message='Ошибка при выполнении запроса к api яндекс карт.')
    
    def get_map_by_name(self, object_name) -> None:
        search_api_server = 'https://search-maps.yandex.ru/v1/'
        search_params = {
            "apikey": self.search_apikey,
            "text": object_name,
            "lang": "ru_RU",
            "type": "biz",
        }

        response = requests.get(search_api_server, params=search_params)
        if not response.ok:
            self.error_message(message='Ошибка при выполнении запроса к api яндекс карт.')
        else:
            json_response = response.json()
            try:
                longitude, latitude = json_response['features'][0]['geometry']['coordinates']
                self.info.setText(json_response['features'][0]['properties']['description'])
                self.info.setVisible(True)
            except IndexError:
                self.error_message(message='Ошибка при обработке ответа от api яндекс карт.\nВероятная причина - неверный адрес.')
                return
            self.get_map_by_cords(latitude=latitude, longitude=longitude, point=True)
            self.latitude.setText(str(latitude))
            self.longitude.setText(str(longitude))
            

    def get_map(self) -> None:
        if self.address.text().strip() not in 'Введите адрес или координаты объекта':
            self.get_map_by_name(self.address.text().strip())
        else:
            self.get_map_by_cords(point=True)

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            self.get_map()

        elif event.key() in (16777238, 16777239):
            dt = 1 if event.key() == 16777238 else -1
            if 1 <= self.zoom.value() + dt <= 20:
                self.zoom.setValue(self.zoom.value() + dt)
                if self.current_map:
                    self.get_map_by_cords()

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
            self.get_map_by_cords()
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = Application()
    widget.show()
    sys.exit(app.exec())