import pytesseract
from PIL import Image
import cv2


def main():
    img = cv2.imread('resources/tondi_1.jpg')
    text = pytesseract.image_to_string(img)
    print(text)


if __name__ == '__main__':
    main()
