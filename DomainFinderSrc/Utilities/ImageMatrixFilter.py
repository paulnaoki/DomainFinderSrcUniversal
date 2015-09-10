class NonSquireMatrix:
    def __init__(self, width: int, height: int):
        assert width >= 2, "width has to be greater than 2."
        assert height >= 2, "height has to be greater than 2."
        self._width = width
        self._height = height
        self._matrix = []
        for i in range(height):
            self._matrix.append([0 for j in range(width)])

    def get_inner_matrix(self):
        return self._matrix


class Matrix:
    def __init__(self, dimension=2):
        assert dimension > 1, "dimension has to be greater than 1"
        self._dimention = dimension
        self._matrix = []
        for i in range(dimension):
            new_row = []
            for j in range(dimension):
                new_row.append(0)
            self._matrix.append(new_row)

    def reset(self):
        for row in self._matrix:
            for j in range(self._dimention):
                row[j] = 0

    def get_inner_matrix(self):
        return self._matrix


class WhiteNoiseFilterMatrix:
    def __init__(self, inner_dimension=1, outer_dimension=3):
        assert inner_dimension > 0, "inner dimension has to be greater than 0."
        assert inner_dimension >= 3, "outer dimension has to be at least 3"
        assert (outer_dimension-inner_dimension) % 2 == 0, "outer dimension - inner_dimension has to be a mutiple of 2"
        self._inner_d = inner_dimension
        self._outer_d = outer_dimension
        self._matrix = Matrix(dimension=outer_dimension)
        self._image_pixels = []

    def process_image_matrix(self, image_matrix: [[]], background_v=0, target_v=255):
        width = len(image_matrix[0])
        height = len(image_matrix)
        pass
        # if width > 0 and height > 0:
        #     for

