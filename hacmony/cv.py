import cv2
import numpy as np
import time
import math

def load_image_from_buf(img_bytes):
    """
    Load an image from a byte array
    :param img_bytes: The byte array of an image
    :return:
    """
    img_bytes = np.array(img_bytes)
    return cv2.imdecode(img_bytes, cv2.IMREAD_UNCHANGED)


def cal_angles(triangle):
    point_a = triangle[0][0]
    point_b = triangle[1][0]
    point_c = triangle[2][0]
    return (cal_angle(point_a, point_b, point_c), 
            cal_angle(point_b, point_a, point_c), 
            cal_angle(point_a, point_c, point_b))

def cal_center(triangle):
    point_a = triangle[0][0]
    point_b = triangle[1][0]
    point_c = triangle[2][0]
    return((point_a[0] + point_b[0] + point_c[0])/3, (point_a[1] + point_b[1] + point_c[1])/3)

def cal_angle(point_a, point_b, point_c):
    a_x, b_x, c_x = point_a[0], point_b[0], point_c[0]  
    a_y, b_y, c_y = point_a[1], point_b[1], point_c[1] 
    if len(point_a) == len(point_b) == len(point_c) == 3:
        a_z, b_z, c_z = point_a[2], point_b[2], point_c[2]
    else:
        a_z, b_z, c_z = 0,0,0  
    x1,y1,z1 = (a_x-b_x),(a_y-b_y),(a_z-b_z)
    x2,y2,z2 = (c_x-b_x),(c_y-b_y),(c_z-b_z)
    cos_b = (x1*x2 + y1*y2 + z1*z2) / (math.sqrt(x1**2 + y1**2 + z1**2) *(math.sqrt(x2**2 + y2**2 + z2**2))) 
    B = math.degrees(math.acos(cos_b)) 
    return B

def canny(img_bytes):
    img_bytes = np.array(img_bytes)
    img = cv2.imdecode(img_bytes, cv2.IMREAD_UNCHANGED)
    grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(grayimg, (5, 5), 0)
    edges = cv2.Canny(blurred, 100, 200)
    return edges

def get_play_coordinates(img_bytes):
    coordinates = []
    # edges = canny(img_bytes)
    # contours,_ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours,_ = cv2.findContours(img_bytes, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.05*cv2.arcLength(cnt, True), True)
        if len(approx) == 3:
            (degree1, degree2, degree3) = cal_angles(approx)
            if np.all(np.array([degree1,degree2,degree3]) < 70):
                coordinates.append(cal_center(approx))
    return coordinates

def calculate_dhash(img):
    """
    Calculate the dhash value of an image.
    :param img: numpy.ndarray, representing an image in opencv
    :return:
    """
    difference = calculate_pixel_difference(img)
    # convert to hex
    decimal_value = 0
    hash_string = ""
    for index, value in enumerate(difference):
        if value:
            decimal_value += value * (2 ** (index % 8))
        if index % 8 == 7:  # every eight binary bit to one hex number
            hash_string += str(hex(decimal_value)[2:-1].rjust(2, "0"))  # 0xf=>0x0f
            decimal_value = 0
    return hash_string

def calculate_pixel_difference(img):
    """
    Calculate difference between pixels
    :param img: numpy.ndarray, representing an image in opencv
    """
    resize_width = 18
    resize_height = 16
    # 1. resize to 18*16
    smaller_image = cv2.resize(img, (resize_width, resize_height))

    # 2. calculate grayscale
    grayscale_image = cv2.cvtColor(smaller_image, cv2.COLOR_BGR2GRAY)

    # 3. calculate difference between pixels
    difference = []
    for row in range(resize_height):
        for col in range(resize_width - 1):
            difference.append(grayscale_image[row][col] > grayscale_image[row][col + 1])
    return difference


def img_hamming_distance(img1, img2):
    """
    Calculate the hamming distance between two images
    :param img1: numpy.ndarray, representing an image in opencv
    :param img2: numpy.ndarray, representing an image in opencv
    :return: int, the hamming distance between two images
    """
    # A. use dHash value to calculate hamming distance
    if isinstance(img1, str) and isinstance(img2, str):
        return dhash_hamming_distance(img1, img2)

    # B. use numpy.ndarray to calculate hamming distance
    _hamming_distance = 0
    image1_difference = calculate_pixel_difference(img1)
    image2_difference = calculate_pixel_difference(img2)
    for index, img1_pix in enumerate(image1_difference):
        img2_pix = image2_difference[index]
        if img1_pix != img2_pix:
            _hamming_distance += 1
    return _hamming_distance

def dhash_hamming_distance(dhash1, dhash2):
    """
    Calculate the hamming distance between two dhash values
    :param dhash1: str, the dhash of an image returned by `calculate_dhash`
    :param dhash2: str, the dhash of an image returned by `calculate_dhash`
    :return: int, the hamming distance between two dhash values
    """
    difference = (int(dhash1, 16)) ^ (int(dhash2, 16))
    return bin(difference).count("1")
