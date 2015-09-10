from png import png
from DomainFinderSrc.Utilities import FileIO, ImageMatrixFilter
from unittest import TestCase
import array
from tkinter import *
from PIL import ImageFilter, Image
from DomainFinderSrc.Scrapers.LinkChecker import *


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def read_image(image_path: str):
    matrix = []
    reader = png.Reader(filename=image_path)
    w, h, pixels, metadata = reader.asRGBA()
    for row in pixels:
        matrix.append(row)

    height = len(matrix)
    width = len(matrix[0])
    magic_code = 61680
    new_matrix= []
    for row in matrix:
        new_row = []
        for pixel in row:
            if pixel == magic_code:
                new_row.append(255)
            else:
                new_row.append(0)
        new_matrix.append(new_row)
    return new_matrix, width, height


def insert_line(data: [[]], line_index: int, color: int, is_vertical=True):
    width = len(data[0])
    height = len(data)
    try:
        assert line_index >= 0, "line index has to be greater than 0."
        assert 0 < color < 256, "color has to be range(0,256)"
        if is_vertical:
            assert line_index < width, "line index has to be less than width in vertical mode."
            for row in data:
                row[line_index] = color
        else:
            assert line_index < height, "line index has to be less than height in horizontal mode."
            for i in range(0, width):
                data[line_index][i] = color
    except Exception as ex:
        print(ex)


def get_1d_array(matrix: [[]], target_v: int, height: int, width: int, start_portion: float, end_portion: float,
                 offset_tolerance_factor=0.2) -> [[]]:
    start_index = int(width*start_portion)
    end_index = int(width*end_portion)
    transformed_points = []
    temp_average = 0
    mov_av_len = 5
    current_column = 0
    row_offset = 50
    for column in range(start_index, end_index):
        # if current_column - mov_av_len > 0: # calculate previous moving average
        #     temp_average = sum([dot[1] for dot in transformed_points[current_column-1 - mov_av_len: current_column-1]])/mov_av_len
        default_v = Point(column, 0)
        column_collection = []
        for row in range(row_offset, height-row_offset):
            v = matrix[row][column]
            if v == target_v:
                column_collection.append(Point(column, row))
        if len(column_collection) > 0:  # determine best estimation
            min_distance = height
            close_point = column_collection[0]
            # for point in column_collection:
            #     distance = point[1] - temp_average
            #     if distance < min_distance:
            #         close_point = point
            #         min_distance = distance
            transformed_points.append(close_point)
        else:
            pass
            # transformed_points.append(default_v)
        current_column += 1

    # remove noise:
    total_width = len(transformed_points)
    offset_tolerance = height * offset_tolerance_factor
    total_sum = 0
    if total_width > 0:
        for i in range(total_width):
            ref_point = transformed_points[i]
            total_sum += ref_point.y
            if i + 1 >= total_width:
                break
            else:
                next_point = transformed_points[i+1]
                if abs(next_point.y - ref_point.y) > offset_tolerance:
                    transformed_points[i+1] = Point(next_point.x, ref_point.y)
        temp_matrix = ImageMatrixFilter.NonSquireMatrix(total_width, height).get_inner_matrix()
        # insert an average line:
        average = int(total_sum/total_width)
        index = 0
        one_d_array = []
        for point in transformed_points:
            point.x = index
            one_d_array.append(point.y)
            index += 1
            # temp_matrix[average][point.x] = 100
            temp_matrix[point.y][point.x] = 255

        # for i in range(width):
        #     for j in range(height):
        #         matrix[j][i] = 0
        # for point in transformed_points:
        #     matrix[point.y][point.x] = 255

        return temp_matrix, one_d_array, average
    else:
        return [], [], 0


def find_match_point(begin_index: int, match: int,  data: [], min_distance=2, rising_edge=True):
    assert min_distance >= 2, "minimum distance between edge point is 2."
    data_len = len(data)
    distance = 0
    found = begin_index
    previous_point = 0
    if begin_index < data_len - 1:
        for point in data[begin_index:]:
            if distance > min_distance:
                if rising_edge and point > match and point - previous_point > 0:
                    break
                elif not rising_edge and point < match and point - previous_point < 0:
                    break
            previous_point = point
            found += 1
            distance += 1
    return found


def find_min_point(begin_index, end_index, data:[]):
    min_v = 10000
    distance = 0
    count = begin_index
    for point in data[begin_index: end_index]:
        if point < min_v:
            min_v = point
            distance = count
        count += 1
    return min_v, distance


def find_peak(data: [], max_value: int,  average_scale=1.0, amplitude_scale=0.3, min_deviation=3):
    assert max_value > 0, "max_value of data point has to be greater than 0."
    assert 0 < average_scale <= 1.0, "average_scale has to be in range(0, 1), which is used to mutiple the base line average white noise."
    assert 0 < amplitude_scale <= 1.0, "amplitude_scale has to be in range(0, 1), which is used to measure the distance between peak value and white noise base line value"
    assert 3 <= min_deviation, "deviation value measures the distance between rising or falling edge to the central peak value in time series array."
    data_len = len(data)
    index = 0
    first_ref = 0
    second_ref = 0
    peak_value = 0
    min_distance = 2
    min_amplitude = max_value * amplitude_scale
    min_ref = 0
    min_v = 0
    if data_len > 0:
        average = int(sum(data)/data_len*average_scale)
        while first_ref < data_len and second_ref < data_len:
            first_ref = find_match_point(second_ref, average, data, min_distance=min_distance, rising_edge=False)
            second_ref = find_match_point(first_ref, average, data, min_distance=min_distance, rising_edge=True)
            min_v, min_ref = find_min_point(first_ref, second_ref, data)
            if average-min_v > min_amplitude and \
                    (abs(first_ref-min_ref) >= min_deviation or abs(second_ref-min_deviation) >= min_deviation):
                break
            elif first_ref == second_ref:
                break
            print("rising point: ", first_ref, "max point: ", min_ref, " v is: ", min_v, " falling point: ", second_ref)
        return first_ref, second_ref, min_ref, min_v
    else:
        raise ValueError("data len is none.")


class PNGTester(TestCase):
    def testGet_SampleImages(self):
        url_format = "https://majestic.com/charts/backlinks-discovery-chart?d={0:s}&se=1&w=1000&h=300&t=l&ctype=0&bc=EAEEF0&IndexDataSource=D"
        file_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/spam_test1.txt"
        save_file_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/Image_Samples/"
        FileIO.FileHandler.create_file_if_not_exist(save_file_path)
        domain_list = FileIO.FileHandler.read_lines_from_file(file_path)
        for item in domain_list:
            print("doing: item:", item)
            s = LinkChecker.get_common_request_session(retries=1, redirect=2)
            # NOTE the stream=True parameter
            r = s.get(url_format.format(item,), stream=True, timeout=5)
            full_path =save_file_path+item+".png"
            with open(full_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
                        f.flush()
                f.close()

    def testImageFilter(self):
        new_image_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/Image/61680.png"
        im = Image.open(new_image_path)
        im.show()
        im1 = im.filter(ImageFilter.GaussianBlur)
        im1.show()

    def testImageTransformBatch(self):
        file_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/spam_test1.txt"
        read_file_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/Image_Samples/"
        save_file_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/Image_Filtered/"
        FileIO.FileHandler.create_file_if_not_exist(save_file_path)
        domain_list = FileIO.FileHandler.read_lines_from_file(file_path)
        for item in domain_list:
            print("doing: item:", item)
            peak_scale_factor = 0.9
            image_path = read_file_path + item + ".png"
            matrix, width, height = read_image(image_path)
            new_matrix, one_d_array, average = get_1d_array(matrix, 255, height, width, 0.5, 0.97)
            first_ref, second_ref, min_ref, min_v = find_peak(one_d_array,
                                                              max_value=height, average_scale=peak_scale_factor,
                                                              amplitude_scale=0.3, min_deviation=3)
            insert_line(new_matrix, first_ref, 50)
            insert_line(new_matrix, second_ref, 50)
            insert_line(new_matrix, min_ref, 50)
            insert_line(new_matrix, int(average*peak_scale_factor), 200, is_vertical=False)
            formated = png.from_array(new_matrix, mode='L')
            new_path = save_file_path + item + ".png"
            formated.save(new_path)

    def testImageTransform1(self):
        peak_scale_factor = 0.9
        image_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/Image_Samples/3xstar.net.png"
        matrix, width, height = read_image(image_path)
        new_matrix, one_d_array, average = get_1d_array(matrix, 255, height, width, 0.5, 0.97)
        first_ref, second_ref, min_ref, min_v = find_peak(one_d_array,
                                                          max_value=height, average_scale=peak_scale_factor,
                                                          amplitude_scale=0.3, min_deviation=3)
        insert_line(new_matrix, first_ref, 50)
        insert_line(new_matrix, second_ref, 50)
        insert_line(new_matrix, min_ref, 50)
        insert_line(new_matrix, int(average*peak_scale_factor), 200, is_vertical=False)
        formated = png.from_array(new_matrix, mode='L')
        new_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/test_filterd1.png"
        formated.save(new_path)
        im = Image.open(new_path)
        im.show()

    def testRead(self):
        image_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/BacklinkHistoryChart.png"
        new_image_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/Image/{0:d}.png"
        matrix = []
        reader = png.Reader(filename=image_path)
        pixel_dict = {}
        w, h, pixels, metadata = reader.asRGBA()
        for row in pixels:
            matrix.append(row)
            for pixcel in row:
                if pixcel in pixel_dict.keys():
                    v = pixel_dict[pixcel]
                    pixel_dict.update({pixcel: v+1})
                else:
                    pixel_dict.update({pixcel: 1})
        height = len(matrix)
        width = len(matrix[0])
        print("height:", height, "width:", width)
        print("variations:")

        sort = [x for x in sorted(pixel_dict.items(), key=lambda pixel_count: pixel_count[1], reverse=True) if 20000> x[1] > 50]
        count = 0
        for item in sort:
            new_matrix= []
            for row in matrix:
                new_row = []
                for pixel in row:
                    if pixel == item[0]:
                        new_row.append(255)
                    else:
                        new_row.append(0)
                new_matrix.append(new_row)
            formated = png.from_array(new_matrix, mode='L')
            new_path = new_image_path.format(item[0],)
            FileIO.FileHandler.create_file_if_not_exist(new_path)
            formated.save(new_path)
            count += 1
            if count == 10:
                break

    def testPNGpixelOrder(self):
        new_image_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/test_order.png"
        matrix = [[255, 0, 255, 0, 255],
                  [255, 255, 255, 255, 255],
                  [0, 0, 255, 255, 255]]
        im = png.fromarray(matrix, mode='L')
        im.save(new_image_path)
        show_im = Image.open(new_image_path)
        show_im.show("png test")