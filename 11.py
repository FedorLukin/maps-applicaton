from PyQt6 import uic
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QImage, QIcon, QKeyEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from dataclasses import dataclass
from dotenv import load_dotenv
import requests
import sys
import os


@dataclass
class Map:
    latitude: float
    longitude: float
    zoom: int
    theme: bool
    point: str

    def __eq__(self, values_tuple):
        return (self.latitude, self.longitude, self.zoom, self.theme) == values_tuple


@dataclass
class AddressDetails:
    address_line: str
    postal_code: str

    def get_full(self):
        return f'{self.address_line}, почтовый индекс: {self.postal_code}'


class Application(QMainWindow):
    def __init__(self) -> None:
        load_dotenv()
        self.static_apikey = os.getenv('STATIC_APIKEY')
        self.search_apikey = os.getenv('SEARCH_APIKEY')
        self.geocode_apikey = os.getenv('GEOCODE_APIKEY')
        super().__init__()
        uic.loadUi('src/maps4.ui', self)
        self.setFixedSize(540, 690)
        self.image.setPixmap(QPixmap.fromImage(QImage('src/logo.png')))
        self.setWindowIcon(QIcon('src/icon.png'))
        self.info.setVisible(False) 
        self.clear.clicked.connect(self.clear_ui)
        self.getmap.clicked.connect(self.get_map)
        self.theme.clicked.connect(self.change_theme)
        self.index.clicked.connect(self.change_postal_code_visibility)
        self.nightMode = False
        self.address_info = None
        self.current_map = None


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

    def change_postal_code_visibility(self) -> None:
        if not self.address_info:
            return

        if not self.index.isChecked():
            self.info.setText(self.address_info.address_line)
        elif self.address_info.postal_code:
                self.info.setText(self.address_info.get_full())
        else:
            self.get_map_by_name(self.address_info.address_line)

    def clear_ui(self) -> None:
        self.image.setPixmap(QPixmap.fromImage(QImage('src/logo.png')))
        self.address.setText('Введите адрес или координаты объекта')
        self.info.setVisible(False) 
        self.longitude.clear()
        self.latitude.clear()
        self.zoom.setValue(12)
        self.current_map = None
        self.address_info = None

    def error_message(self, message: str) -> None:
        self.clear_ui()
        msgBox = QMessageBox()
        msgBox.setWindowTitle('Ошибка!')
        msgBox.setText(message)
        msgBox.exec()
    
    def get_map_by_cords(self, latitude: float = None, longitude: float = None, new_point: bool = False) -> None:
        if not (latitude and longitude):
            latitude, longitude = self.latitude.text(), self.longitude.text()
            try:
                latitude, longitude = float(latitude.replace(',', '.')), float(longitude.replace(',', '.'))
                if int(latitude) not in range(-85, 86) or int(longitude) not in range(-180, 181):
                    raise ValueError

            except ValueError:
                self.error_message(message='Некорректные значения ширины или долготы.')
                return
            
        point = f'{longitude},{latitude},vkbkm' if new_point else self.current_map.point
        zoom = self.zoom.value()

        if self.current_map == (latitude, longitude, zoom, self.nightMode):
            return

        map_params = {
            "apikey": self.static_apikey,
            "ll": f'{longitude},{latitude}',
            "z": zoom,
            "size": '450,450',
            "pt": point,
            "theme": 'dark' if self.nightMode else 'light'
        }

        map_api_server = "https://static-maps.yandex.ru/v1"
        response = requests.get(map_api_server, params=map_params)
        if response.ok:
            with open('res.jpg', 'wb') as file:
                file.write(response.content)
            self.image.setPixmap(QPixmap.fromImage(QImage('res.jpg')))
            self.image.setFocus()
            os.remove('res.jpg')
            self.current_map = Map(latitude=latitude, longitude=longitude, zoom=zoom, theme=self.nightMode, point=point)
        else:
            self.error_message(message='Ошибка при выполнении запроса к api яндекс карт.')
            
    
    def get_map_by_name(self, object_name: str) -> None:
        search_params = {
            "apikey": self.search_apikey,
            "text": object_name,
            "lang": "ru_RU",
            "type": 'biz'
        }

        search_api_server = 'https://search-maps.yandex.ru/v1/'
        response = requests.get(search_api_server, params=search_params)
        if not response.ok:
            self.error_message(message='Ошибка при выполнении запроса к api яндекс карт.')
        else:
            json_response = response.json()

            try:
                longitude, latitude = json_response['features'][0]['geometry']['coordinates']
                address_line = json_response['features'][0]['properties']['description']
                postal_code = self.get_postal_code(address_line) if self.index.isChecked() else None
                self.address_info = AddressDetails(address_line=address_line, postal_code=postal_code)
                self.info.setText(f'{address_line}, почтовый индекс: {postal_code}' if postal_code else address_line)
                self.info.setVisible(True)
            except IndexError:
                self.error_message(message='Ошибка при обработке ответа от api яндекс карт.\nВероятная причина - неверный адрес.')
                return
            self.get_map_by_cords(latitude=latitude, longitude=longitude, new_point=True)
            self.latitude.setText(str(latitude))
            self.longitude.setText(str(longitude))
            
    def get_map(self) -> None:
        if self.address.text().strip() not in 'Введите адрес или координаты объекта':
            self.get_map_by_name(self.address.text().strip())
        else:
            self.get_map_by_cords(new_point=True)

    def get_postal_code(self, adress_line: str) -> str:
        search_params = {
            "apikey": self.geocode_apikey,
            "geocode": adress_line,
            "lang": "ru_RU",
            "format": 'json'
        }

        geocoder_api_server = 'https://geocode-maps.yandex.ru/v1'
        response = requests.get(geocoder_api_server, params=search_params)
        if not response.ok:
            self.error_message(message='Ошибка при выполнении запроса к api яндекс карт.')
        else:
            try:
                json_response = response.json()
                object_info = json_response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
                postal_code = object_info['metaDataProperty']['GeocoderMetaData']['Address']['postal_code']
                return postal_code
            except KeyError:
                return ''

    def get_nearest_organisation(self):

        text = self.address_info.address_line if self.address_info else f'{self.current_map.longitude},{self.current_map.latitude}'
        search_params = {
            "apikey": self.search_apikey,
            "text": text,
            "lang": "ru_RU",
            "type": 'biz',
            "ll": f'{self.current_map.longitude},{self.current_map.latitude}',
            "spn": '0.0015,0.0015',
            "results": '1',
            "format": 'json'
        }
        geocoder_api_server = 'https://search-maps.yandex.ru/v1/?'
        response = requests.get(geocoder_api_server, params=search_params)
        if not response.ok:
            self.error_message(message='Ошибка при выполнении запроса к api яндекс карт.')
        else:
            try:
                object_data = json_response["features"][0]
                object_cords = object_data["geometry"]["coordinates"]
                org_data = object_data["properties"]["CompanyMetaData"]
                org_name = org_data["name"]
                org_address = org_data["address"]
                info = f'{org_name}\n{org_address}\n'
                if org_data.get("url"):
                    info += org_data.get("url")
                if org_data.get("Phones"):
                    info += f'\n{','.join([ph["formatted"] for ph in org_data.get("Phones")])}'
                self.address_info = AddressDetails(address_line=info, postal_code='')
                self.info.setText(f'{info}')
                self.get_map_by_cords(*object_cords[::-1], True)
                

            except KeyError:
                return ''
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.current_map:
            x, y = event.pos().x() - 45, event.pos().y() - 10
            if 0 <= x <= 450 and 0 <= y <= 450:
                x -= 225
                y -= 225
                dt_lat = y * 15.5 / 2 ** (self.zoom.value() + 4)
                dt_ln = x * 22/ 2 ** (self.zoom.value() + 4)
                self.get_map_by_cords(self.current_map.latitude - dt_lat, self.current_map.longitude + dt_ln, True)

        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == 16777220:
            self.get_map()

        elif event.key() in (16777238, 16777239):
            dt = 1 if event.key() == 16777238 else -1
            if 1 <= self.zoom.value() + dt <= 20:
                self.zoom.setValue(self.zoom.value() + dt)
                if self.current_map:
                    self.get_map_by_cords(latitude=self.current_map.latitude, longitude=self.current_map.longitude)

        elif self.image.hasFocus() and self.current_map:
            if event.key() == Qt.Key.Key_Left:
                lng = self.current_map.longitude
                new_lng = lng - 180 / 2 ** self.zoom.value()
                new_lng = new_lng if new_lng > -180 else 180 - abs(new_lng) % 180
                self.longitude.setText(str(new_lng))
                self.current_map.longitude = 0
            if event.key() == Qt.Key.Key_Right:
                lng = self.current_map.longitude
                new_lng = lng + 180 / 2 ** self.zoom.value()
                new_lng = new_lng if new_lng < 180 else -180 + new_lng % 180
                self.longitude.setText(str(new_lng))
                self.current_map.longitude = 0
            if event.key() == Qt.Key.Key_Up:
                ltd = self.current_map.latitude
                new_ltd = ltd + 90 / 2 ** self.zoom.value()
                new_ltd = new_ltd if new_ltd < 90 else -90 + new_ltd % 90
                self.latitude.setText(str(new_ltd))
                self.current_map.latitude = 0
            if event.key() == Qt.Key.Key_Down:
                ltd = self.current_map.latitude
                new_ltd = ltd - 90 / 2 ** self.zoom.value()
                new_ltd = new_ltd if new_ltd < 90 else -90 + new_ltd % 90
                self.latitude.setText(str(new_ltd))
                self.current_map.latitude = 0
            self.get_map_by_cords()
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = Application()
    widget.show()
    sys.exit(app.exec())