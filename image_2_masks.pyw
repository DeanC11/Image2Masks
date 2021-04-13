import sys

import pyperclip
from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QFileDialog, QLabel, QPushButton, QSpinBox,
                             QCheckBox, QHBoxLayout, QVBoxLayout, QGridLayout)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # set window options
        self.setWindowTitle('Image 2 Masks')
        self.setWindowIcon(QIcon('./images/mask_icon.ico'))
        self.setMinimumSize(400, 255)

        # define class-wide variables
        self.image_chosen: bool = False
        self.image: Image = None
        self.image_width: int = 0
        self.image_height: int = 0
        self.image_aspect_ratio = 0

        # top elements
        image_button = QPushButton('&Browse')
        image_button.clicked.connect(self.browse_images)
        image_button.setStyleSheet("width: 100px;")
        self.image_label = QLabel('Please choose an image')
        # create the top layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.image_label, Qt.AlignLeft)
        top_layout.addWidget(image_button, 100, Qt.AlignRight)

        # width input elements
        self.width_field = QSpinBox()
        self.width_field.valueChanged.connect(self.width_edited)
        self.width_field.setSuffix(" px")
        self.width_field.setMaximum(10000)
        width_label = QLabel('&Width:\t')
        width_label.setBuddy(self.width_field)
        # create horizontal width input layout
        width_layout = QHBoxLayout()
        width_layout.addWidget(width_label, alignment=Qt.AlignLeft)
        width_layout.addWidget(self.width_field, 1, alignment=Qt.AlignLeft)

        # height input elements
        self.height_field = QSpinBox()
        self.height_field.valueChanged.connect(self.height_edited)
        self.height_field.setSuffix(" px")
        self.height_field.setMaximum(10000)
        height_label = QLabel('&Height:\t')
        height_label.setBuddy(self.height_field)
        # create horizontal height input layout
        height_layout = QHBoxLayout()
        height_layout.addWidget(height_label, alignment=Qt.AlignLeft)
        height_layout.addWidget(self.height_field, 1, alignment=Qt.AlignLeft)

        # image options elements
        self.save_bmp_checkbox = QCheckBox('&Save a copy as BMP')
        self.custom_palette_checkbox = QCheckBox('&Use custom colours')
        self.custom_palette_checkbox.stateChanged.connect(self.image_options)
        # create image options layout
        image_options_layout = QHBoxLayout()
        image_options_layout.addWidget(self.save_bmp_checkbox, alignment=Qt.AlignLeft)
        image_options_layout.addSpacing(5)
        image_options_layout.addWidget(self.custom_palette_checkbox, alignment=Qt.AlignLeft)

        # middle layout elements
        self.keep_aspect_checkbox = QCheckBox('&Keep aspect ratio')
        self.keep_aspect_checkbox.stateChanged.connect(self.calculate_image_size)
        # create the middle layout
        middle_layout = QVBoxLayout()
        middle_layout.addLayout(width_layout)
        middle_layout.addSpacing(5)
        middle_layout.addLayout(height_layout)
        middle_layout.addSpacing(10)
        middle_layout.addWidget(self.keep_aspect_checkbox, alignment=Qt.AlignLeft)
        middle_layout.addLayout(image_options_layout)

        # bottom elements
        create_button = QPushButton('&Create Masks')
        create_button.clicked.connect(self.create_pressed)
        create_button.setStyleSheet("width: 140px;")
        self.create_label = QLabel()
        self.create_label.setStyleSheet("font-size: 12px")
        # create the bottom layout
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(create_button, alignment=Qt.AlignLeft)
        bottom_layout.addWidget(self.create_label, alignment=Qt.AlignLeft)
        bottom_layout.addStretch(100)

        # create the main layout
        main_layout = QGridLayout()
        main_layout.addLayout(top_layout, 0, 0, Qt.AlignTop)
        main_layout.addLayout(middle_layout, 1, 0)
        main_layout.addLayout(bottom_layout, 2, 0, Qt.AlignBottom)

        widget = QWidget()
        widget.setLayout(main_layout)

        self.setCentralWidget(widget)

    def browse_images(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image File", filter="Image Files (*.bmp *.jpeg *.jpg "
                                                                                  "*.jfif *.png *.tiff)")
        if filename:
            self.image_chosen = True
            self.image_label.setText(filename)
            self.create_label.setText("")

            # open selected image
            self.image = Image.open(filename)
            # save image width and height
            self.image_width = self.image.width
            self.image_height = self.image.height
            self.image_aspect_ratio = self.image_width / self.image_height
            # set width and height fields
            self.width_field.setValue(self.image_width)
            self.height_field.setValue(self.image_height)

    def save_bmp(self, image: Image):
        filename, _ = QFileDialog.getSaveFileName(self, "Save As BMP", filter="256 Colour Bitmap (*.bmp)")

        if filename:
            new_image = image.convert("RGB", dither=0).quantize(colors=256, method=0, dither=0)
            new_image.save(filename)

    def width_edited(self):
        if self.image_chosen:
            self.image_width = self.width_field.value()
            self.calculate_image_size(True)
        else:
            # if no image was chosen, reset the field
            self.width_field.setValue(0)

    def height_edited(self):
        if self.image_chosen:
            self.image_height = self.height_field.value()
            self.calculate_image_size(False)
        else:
            # if no image was chosen, reset the field
            self.height_field.setValue(0)

    def calculate_image_size(self, width_changed_last: bool = True):
        if self.image_chosen:
            if self.keep_aspect_checkbox.isChecked():
                if width_changed_last:
                    self.image_height = round(self.image_width / self.image_aspect_ratio)
                    self.height_field.setValue(self.image_height)
                else:
                    self.image_width = round(self.image_height * self.image_aspect_ratio)
                    self.width_field.setValue(self.image_width)

    def image_options(self):
        if self.custom_palette_checkbox.isChecked() and not self.save_bmp_checkbox.isChecked():
            self.save_bmp_checkbox.setChecked(True)

    def create_pressed(self):
        if self.image_chosen:
            # process the image and create masks
            resized_image, converted_image = process_image(self.image, self.image_width, self.image_height)
            create_masks(resized_image, converted_image)
            self.create_label.setText("Masks copied to clipboard!")

            # save a copy as BMP if specified by user
            if self.save_bmp_checkbox.isChecked():
                if self.custom_palette_checkbox.isChecked():
                    self.save_bmp(resized_image)
                else:
                    self.save_bmp(converted_image)
        else:
            self.create_label.setText('No image was chosen')


def process_image(image: Image, width: int, height: int):
    # resize the image
    if image.width != width or image.height != height:
        resized_image = image.resize((width, height), resample=Image.BICUBIC)
    else:
        resized_image = image

    # change colour palette
    palette = [0, 0, 0, 0, 0, 170, 0, 170, 0, 0, 170, 170, 170, 0, 0, 170, 0, 170, 170, 85, 0, 170, 170, 170, 85,
               85, 85, 85, 85, 255, 85, 255, 85, 85, 255, 255, 255, 85, 85, 255, 85, 255, 255, 255, 85, 255, 255,
               255, 0, 0, 0, 16, 16, 16, 32, 32, 32, 53, 53, 53, 69, 69, 69, 85, 85, 85, 101, 101, 101, 117, 117,
               117, 138, 138, 138, 154, 154, 154, 170, 170, 170, 186, 186, 186, 202, 202, 202, 223, 223, 223, 239,
               239, 239, 255, 255, 255, 0, 0, 255, 65, 0, 255, 130, 0, 255, 190, 0, 255, 255, 0, 255, 255, 0, 190,
               255, 0, 130, 255, 0, 65, 255, 0, 0, 255, 65, 0, 255, 130, 0, 255, 190, 0, 255, 255, 0, 190, 255, 0,
               130, 255, 0, 65, 255, 0, 0, 255, 0, 0, 255, 65, 0, 255, 130, 0, 255, 190, 0, 255, 255, 0, 190, 255,
               0, 130, 255, 0, 65, 255, 130, 130, 255, 158, 130, 255, 190, 130, 255, 223, 130, 255, 255, 130, 255,
               255, 130, 223, 255, 130, 190, 255, 130, 158, 255, 130, 130, 255, 158, 130, 255, 190, 130, 255, 223,
               130, 255, 255, 130, 223, 255, 130, 190, 255, 130, 158, 255, 130, 130, 255, 130, 130, 255, 158, 130,
               255, 190, 130, 255, 223, 130, 255, 255, 130, 223, 255, 130, 190, 255, 130, 158, 255, 186, 186, 255,
               202, 186, 255, 223, 186, 255, 239, 186, 255, 255, 186, 255, 255, 186, 239, 255, 186, 223, 255, 186,
               202, 255, 186, 186, 255, 202, 186, 255, 223, 186, 255, 239, 186, 255, 255, 186, 239, 255, 186, 223,
               255, 186, 202, 255, 186, 186, 255, 186, 186, 255, 202, 186, 255, 223, 186, 255, 239, 186, 255, 255,
               186, 239, 255, 186, 223, 255, 186, 202, 255, 0, 0, 113, 28, 0, 113, 57, 0, 113, 85, 0, 113, 113, 0,
               113, 113, 0, 85, 113, 0, 57, 113, 0, 28, 113, 0, 0, 113, 28, 0, 113, 57, 0, 113, 85, 0, 113, 113, 0,
               85, 113, 0, 57, 113, 0, 28, 113, 0, 0, 113, 0, 0, 113, 28, 0, 113, 57, 0, 113, 85, 0, 113, 113, 0,
               85, 113, 0, 57, 113, 0, 28, 113, 57, 57, 113, 69, 57, 113, 85, 57, 113, 97, 57, 113, 113, 57, 113,
               113, 57, 97, 113, 57, 85, 113, 57, 69, 113, 57, 57, 113, 69, 57, 113, 85, 57, 113, 97, 57, 113, 113,
               57, 97, 113, 57, 85, 113, 57, 69, 113, 57, 57, 113, 57, 57, 113, 69, 57, 113, 85, 57, 113, 97, 57,
               113, 113, 57, 97, 113, 57, 85, 113, 57, 69, 113, 81, 81, 113, 89, 81, 113, 97, 81, 113, 105, 81, 113,
               113, 81, 113, 113, 81, 105, 113, 81, 97, 113, 81, 89, 113, 81, 81, 113, 89, 81, 113, 97, 81, 113,
               105, 81, 113, 113, 81, 105, 113, 81, 97, 113, 81, 89, 113, 81, 81, 113, 81, 81, 113, 89, 81, 113, 97,
               81, 113, 105, 81, 113, 113, 81, 105, 113, 81, 97, 113, 81, 89, 113, 0, 0, 65, 16, 0, 65, 32, 0, 65,
               49, 0, 65, 65, 0, 65, 65, 0, 49, 65, 0, 32, 65, 0, 16, 65, 0, 0, 65, 16, 0, 65, 32, 0, 65, 49, 0, 65,
               65, 0, 49, 65, 0, 32, 65, 0, 16, 65, 0, 0, 65, 0, 0, 65, 16, 0, 65, 32, 0, 65, 49, 0, 65, 65, 0, 49,
               65, 0, 32, 65, 0, 16, 65, 32, 32, 65, 40, 32, 65, 49, 32, 65, 57, 32, 65, 65, 32, 65, 65, 32, 57, 65,
               32, 49, 65, 32, 40, 65, 32, 32, 65, 40, 32, 65, 49, 32, 65, 57, 32, 65, 65, 32, 57, 65, 32, 49, 65,
               32, 40, 65, 32, 32, 65, 32, 32, 65, 40, 32, 65, 49, 32, 65, 57, 32, 65, 65, 32, 57, 65, 32, 49, 65,
               32, 40, 65, 45, 45, 65, 49, 45, 65, 53, 45, 65, 61, 45, 65, 65, 45, 65, 65, 45, 61, 65, 45, 53, 65,
               45, 49, 65, 45, 45, 65, 49, 45, 65, 53, 45, 65, 61, 45, 65, 65, 45, 61, 65, 45, 53, 65, 45, 49, 65,
               45, 45, 65, 45, 45, 65, 49, 45, 65, 53, 45, 65, 61, 45, 65, 65, 45, 61, 65, 45, 53, 65, 45, 49, 65,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    pal_image = Image.new("P", resized_image.size)
    pal_image.putpalette(palette)

    converted_image = resized_image.convert("RGB").quantize(palette=pal_image, dither=0)

    return resized_image, converted_image


def create_masks(resized_image: Image, converted_image: Image):
    # create character mask
    palette_dict = {(0, 0, 0): ' 00h', (0, 0, 170): ' 01h', (0, 170, 0): ' 02h', (0, 170, 170): ' 03h',
                    (170, 0, 0): ' 04h', (170, 0, 170): ' 05h', (170, 85, 0): ' 06h', (170, 170, 170): ' 1Ah',
                    (85, 85, 85): ' 15h', (85, 85, 255): ' 09h', (85, 255, 85): ' 0Ah', (85, 255, 255): ' 0Bh',
                    (255, 85, 85): ' 0Ch', (255, 85, 255): ' 0Dh', (255, 255, 85): ' 0Eh', (255, 255, 255): ' 0Fh',
                    (16, 16, 16): ' 11h', (32, 32, 32): ' 12h', (53, 53, 53): ' 13h', (69, 69, 69): ' 14h',
                    (101, 101, 101): ' 16h', (117, 117, 117): ' 17h', (138, 138, 138): ' 18h', (154, 154, 154): ' 19h',
                    (186, 186, 186): ' 1Bh', (202, 202, 202): ' 1Ch', (223, 223, 223): ' 1Dh', (239, 239, 239): ' 1Eh',
                    (0, 0, 255): ' 20h', (65, 0, 255): ' 21h', (130, 0, 255): ' 22h', (190, 0, 255): ' 23h',
                    (255, 0, 255): ' 24h', (255, 0, 190): ' 25h', (255, 0, 130): ' 26h', (255, 0, 65): ' 27h',
                    (255, 0, 0): ' 28h', (255, 65, 0): ' 29h', (255, 130, 0): ' 2Ah', (255, 190, 0): ' 2Bh',
                    (255, 255, 0): ' 2Ch', (190, 255, 0): ' 2Dh', (130, 255, 0): ' 2Eh', (65, 255, 0): ' 2Fh',
                    (0, 255, 0): ' 30h', (0, 255, 65): ' 31h', (0, 255, 130): ' 32h', (0, 255, 190): ' 33h',
                    (0, 255, 255): ' 34h', (0, 190, 255): ' 35h', (0, 130, 255): ' 36h', (0, 65, 255): ' 37h',
                    (130, 130, 255): ' 38h', (158, 130, 255): ' 39h', (190, 130, 255): ' 3Ah', (223, 130, 255): ' 3Bh',
                    (255, 130, 255): ' 3Ch', (255, 130, 223): ' 3Dh', (255, 130, 190): ' 3Eh', (255, 130, 158): ' 3Fh',
                    (255, 130, 130): ' 40h', (255, 158, 130): ' 41h', (255, 190, 130): ' 42h', (255, 223, 130): ' 43h',
                    (255, 255, 130): ' 44h', (223, 255, 130): ' 45h', (190, 255, 130): ' 46h', (158, 255, 130): ' 47h',
                    (130, 255, 130): ' 48h', (130, 255, 158): ' 49h', (130, 255, 190): ' 4Ah', (130, 255, 223): ' 4Bh',
                    (130, 255, 255): ' 4Ch', (130, 223, 255): ' 4Dh', (130, 190, 255): ' 4Eh', (130, 158, 255): ' 4Fh',
                    (186, 186, 255): ' 50h', (202, 186, 255): ' 51h', (223, 186, 255): ' 52h', (239, 186, 255): ' 53h',
                    (255, 186, 255): ' 54h', (255, 186, 239): ' 55h', (255, 186, 223): ' 56h', (255, 186, 202): ' 57h',
                    (255, 186, 186): ' 58h', (255, 202, 186): ' 59h', (255, 223, 186): ' 5Ah', (255, 239, 186): ' 5Bh',
                    (255, 255, 186): ' 5Ch', (239, 255, 186): ' 5Dh', (223, 255, 186): ' 5Eh', (202, 255, 186): ' 5Fh',
                    (186, 255, 186): ' 60h', (186, 255, 202): ' 61h', (186, 255, 223): ' 62h', (186, 255, 239): ' 63h',
                    (186, 255, 255): ' 64h', (186, 239, 255): ' 65h', (186, 223, 255): ' 66h', (186, 202, 255): ' 67h',
                    (0, 0, 113): ' 68h', (28, 0, 113): ' 69h', (57, 0, 113): ' 6Ah', (85, 0, 113): ' 6Bh',
                    (113, 0, 113): ' 6Ch', (113, 0, 85): ' 6Dh', (113, 0, 57): ' 6Eh', (113, 0, 28): ' 6Fh',
                    (113, 0, 0): ' 70h', (113, 28, 0): ' 71h', (113, 57, 0): ' 72h', (113, 85, 0): ' 73h',
                    (113, 113, 0): ' 74h', (85, 113, 0): ' 75h', (57, 113, 0): ' 76h', (28, 113, 0): ' 77h',
                    (0, 113, 0): ' 78h', (0, 113, 28): ' 79h', (0, 113, 57): ' 7Ah', (0, 113, 85): ' 7Bh',
                    (0, 113, 113): ' 7Ch', (0, 85, 113): ' 7Dh', (0, 57, 113): ' 7Eh', (0, 28, 113): ' 7Fh',
                    (57, 57, 113): ' 80h', (69, 57, 113): ' 81h', (85, 57, 113): ' 82h', (97, 57, 113): ' 83h',
                    (113, 57, 113): ' 84h', (113, 57, 97): ' 85h', (113, 57, 85): ' 86h', (113, 57, 69): ' 87h',
                    (113, 57, 57): ' 88h', (113, 69, 57): ' 89h', (113, 85, 57): ' 8Ah', (113, 97, 57): ' 8Bh',
                    (113, 113, 57): ' 8Ch', (97, 113, 57): ' 8Dh', (85, 113, 57): ' 8Eh', (69, 113, 57): ' 8Fh',
                    (57, 113, 57): ' 90h', (57, 113, 69): ' 91h', (57, 113, 85): ' 92h', (57, 113, 97): ' 93h',
                    (57, 113, 113): ' 94h', (57, 97, 113): ' 95h', (57, 85, 113): ' 96h', (57, 69, 113): ' 97h',
                    (81, 81, 113): ' 98h', (89, 81, 113): ' 99h', (97, 81, 113): ' 9Ah', (105, 81, 113): ' 9Bh',
                    (113, 81, 113): ' 9Ch', (113, 81, 105): ' 9Dh', (113, 81, 97): ' 9Eh', (113, 81, 89): ' 9Fh',
                    (113, 81, 81): '0A0h', (113, 89, 81): '0A1h', (113, 97, 81): '0A2h', (113, 105, 81): '0A3h',
                    (113, 113, 81): '0A4h', (105, 113, 81): '0A5h', (97, 113, 81): '0A6h', (89, 113, 81): '0A7h',
                    (81, 113, 81): '0A8h', (81, 113, 89): '0A9h', (81, 113, 97): '0AAh', (81, 113, 105): '0ABh',
                    (81, 113, 113): '0ACh', (81, 105, 113): '0ADh', (81, 97, 113): '0AEh', (81, 89, 113): '0AFh',
                    (0, 0, 65): '0B0h', (16, 0, 65): '0B1h', (32, 0, 65): '0B2h', (49, 0, 65): '0B3h',
                    (65, 0, 65): '0B4h', (65, 0, 49): '0B5h', (65, 0, 32): '0B6h', (65, 0, 16): '0B7h',
                    (65, 0, 0): '0B8h', (65, 16, 0): '0B9h', (65, 32, 0): '0BAh', (65, 49, 0): '0BBh',
                    (65, 65, 0): '0BCh', (49, 65, 0): '0BDh', (32, 65, 0): '0BEh', (16, 65, 0): '0BFh',
                    (0, 65, 0): '0C0h', (0, 65, 16): '0C1h', (0, 65, 32): '0C2h', (0, 65, 49): '0C3h',
                    (0, 65, 65): '0C4h', (0, 49, 65): '0C5h', (0, 32, 65): '0C6h', (0, 16, 65): '0C7h',
                    (32, 32, 65): '0C8h', (40, 32, 65): '0C9h', (49, 32, 65): '0CAh', (57, 32, 65): '0CBh',
                    (65, 32, 65): '0CCh', (65, 32, 57): '0CDh', (65, 32, 49): '0CEh', (65, 32, 40): '0CFh',
                    (65, 32, 32): '0D0h', (65, 40, 32): '0D1h', (65, 49, 32): '0D2h', (65, 57, 32): '0D3h',
                    (65, 65, 32): '0D4h', (57, 65, 32): '0D5h', (49, 65, 32): '0D6h', (40, 65, 32): '0D7h',
                    (32, 65, 32): '0D8h', (32, 65, 40): '0D9h', (32, 65, 49): '0DAh', (32, 65, 57): '0DBh',
                    (32, 65, 65): '0DCh', (32, 57, 65): '0DDh', (32, 49, 65): '0DEh', (32, 40, 65): '0DFh',
                    (45, 45, 65): '0E0h', (49, 45, 65): '0E1h', (53, 45, 65): '0E2h', (61, 45, 65): '0E3h',
                    (65, 45, 65): '0E4h', (65, 45, 61): '0E5h', (65, 45, 53): '0E6h', (65, 45, 49): '0E7h',
                    (65, 45, 45): '0E8h', (65, 49, 45): '0E9h', (65, 53, 45): '0EAh', (65, 61, 45): '0EBh',
                    (65, 65, 45): '0ECh', (61, 65, 45): '0EDh', (53, 65, 45): '0EEh', (49, 65, 45): '0EFh',
                    (45, 65, 45): '0F0h', (45, 65, 49): '0F1h', (45, 65, 53): '0F2h', (45, 65, 61): '0F3h',
                    (45, 65, 65): '0F4h', (45, 61, 65): '0F5h', (45, 53, 65): '0F6h', (45, 49, 65): '0F7h'}

    new_line: str = "\n\t\t\t\tdb "  # added every new line
    character_mask: str = "\tch\t\t\tdb "  # character mask

    palette = converted_image.getpalette()
    for y in range(0, converted_image.height):
        for x in range(0, converted_image.width):
            p_index = converted_image.getpixel((x, y)) * 3
            rgb_tuple = (palette[p_index], palette[p_index + 1], palette[p_index + 2])
            character_mask += palette_dict[rgb_tuple] + ','

        character_mask = character_mask[:-1]
        character_mask += new_line

    character_mask = character_mask[:-8]

    # create screen mask
    screen_mask: str = "\tchMask\t\tdb "

    if resized_image.mode == "RGBA":
        for y in range(0, resized_image.height):
            for x in range(0, resized_image.width):
                pixel = resized_image.getpixel((x, y))
                if pixel[3] == 0:
                    screen_mask += '0FFh,'
                else:
                    screen_mask += ' 00h,'

            screen_mask = screen_mask[:-1]  # remove last comma from each row
            screen_mask += new_line  # add new line
    else:
        for y in range(0, resized_image.height):
            for x in range(0, resized_image.width):
                screen_mask += '0FFh,'

            screen_mask = screen_mask[:-1]  # remove last comma from each row
            screen_mask += new_line  # add new line

    screen_mask = screen_mask[:-8]  # remove last redundant new line

    # copy masks to clipboard
    final_masks: str = character_mask + "\n\n" + screen_mask
    pyperclip.copy(final_masks)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet("QLabel { font-size: 14px; }"
                      "QPushButton { font-size: 14px; height: 20px; }"
                      "QSpinBox { font-size: 14px; width: 250px }"
                      "QCheckBox { font-size: 14px; }")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
