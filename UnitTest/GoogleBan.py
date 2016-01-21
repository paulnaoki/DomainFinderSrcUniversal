import PIL
from png import png

__author__ = 'superCat'

from unittest import TestCase
import unittest
# import cv2.cv as cv
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
from io import StringIO
import requests


def process_image(url):
    image = _get_image(url)
    image.filter(ImageFilter.SHARPEN)
    return pytesseract.image_to_string(image)


def _get_image(url):
    return Image.open(StringIO(requests.get(url).content))


def clean_image(img: Image):
    pixdata = img.load()

    # Make the letters bolder for easier recognition

    for y in range(img.size[1]):
        for x in range(img.size[0]):
            if pixdata[x, y][0] < 90:
                pixdata[x, y] = (0, 0, 0, 255)

    for y in range(img.size[1]):
        for x in range(img.size[0]):
            if pixdata[x, y][1] < 136:
                pixdata[x, y] = (0, 0, 0, 255)

    for y in range(img.size[1]):
        for x in range(img.size[0]):
            if pixdata[x, y][2] > 0:
                pixdata[x, y] = (255, 255, 255, 255)
    return img


class MyTestCase(TestCase):
    def test_imageRead(self):
        image_folder_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/GoogleBanImage/"
        test_image = "car_plate.jpg"
        # test_image = "test2.png"
        # temp_image = "back-white.png"
        img = Image.open(image_folder_path+test_image)

        img = img.convert("RGBA")
        img = img.resize((1000, 500), Image.BICUBIC)
        enc = ImageEnhance.Contrast(img)
        img = enc.enhance(2)
        # img.show("original")
        img.show("enhanced")
        #
        img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
        # img2 = img2.convert('L').convert('1')
        img.show("final")
        # code = pytesseract.image_to_string(img2, lang='eng')
        # print(code)
        pixdata = img.load()

        # Make the letters bolder for easier recognition

        img = clean_image(img)

        img.show()
        code = pytesseract.image_to_string(img, lang='eng')
        print(code)
        # image_info = {'height': 1000, 'width':500}
        # im = png.fromarray(pixdata, mode='L', info=image_info)
        # im.save(image_folder_path+temp_image)
        # show_im = Image.open(image_folder_path+temp_image)
        # show_im.show("png test")

        #   Make the image bigger (needed for OCR)
        # im_orig = Image.open('input-black.gifig = im_orig.resize((1000, 500), Image.NEAREST)
        # print(pytesseract.image_to_string(image))

    def test_sample_gen(self):
        original_folder = "/Users/superCat/Desktop/PycharmProjectPortable/test/GoogleBanImage/original/"
        sample_folder = "/Users/superCat/Desktop/PycharmProjectPortable/test/GoogleBanImage/samples/"
        image_format = "image{0:d}.jpeg"
        for i in range(1, 21):
            img = Image.open(original_folder+image_format.format(i,))
            img = img.convert("RGBA")
            img = clean_image(img)
            img.save(sample_folder+image_format.format(i,), 'tiff')

if __name__ == '__main__':
    unittest.main()
