from math import atan2, sqrt, pow, degrees, sin, cos, radians
from random import random

from kivy.graphics import Ellipse, Color
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.vector import Vector

from modules.legend import LegendTree


class PieGraph(FloatLayout):
    def __init__(self, data, position, legend_enable=True, **kwargs):
        super(PieGraph, self).__init__(**kwargs)

        # main layout parameters
        self.position = position
        self.size_mine = (0, 0)
        self.data = {}
        self.temp = []

        # Background for debugging
        # with self.canvas:
        # Color(1, 1, 0, 1)
        # self.rect = Rectangle(pos=self.pos, size=self.size)
        # self.bind(size=self._update_rect, pos=self._update_rect)

        for key, value in data.items():
            # Used when no default color is set
            if type(value) is int:
                percentage = (value / float(sum(data.values())) * 100)
                color = [random(), random(), random(), 1]
                self.data[key] = [value, percentage, color]

            # Used when a default color is provided
            elif type(value) is tuple:
                vals = []
                for l in data.values():
                    vals.append(l[0])
                color = value[1]
                percentage = (value[0] / float(sum(vals)) * 100)
                self.data[key] = [value[0], percentage, color]

        self.pie = Pie(self.data, self.position, self.size_mine)
        self.add_widget(self.pie)

        # Legend will be added on the right side of the graph -> not very mobile friendly
        # TODO: Add legend to the bottom alongside a scroll view instead of splitting the screen for each feature

        if legend_enable:
            self.legend = LegendTree(self.data, self.position, self.size_mine)
            self.add_widget(self.legend)
            self.bind(size=self._update_legend, pos=self._update_legend)

        self.bind(size=self._update_pie, pos=self._update_pie)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _update_pie(self, instance, value):
        self.pie.size = (min(instance.size) for i in range(2))
        self.pie.pos = (instance.pos[0], instance.pos[1] + instance.size[1] - self.pie.size[1])

    def _update_legend(self, instance, value):
        self.legend.size = (instance.size[0], instance.size[1] - self.pie.size[1])
        self.legend.pos = instance.pos


class Pie(FloatLayout):
    def __init__(self, data, position, size, **kwargs):
        super(Pie, self).__init__(**kwargs)
        self.position = position
        self.size = size
        angle_start = 0
        count = 0
        self.temp = []

        # with self.canvas:
        # Color(1, 1, 1, 0)
        # self.rect = Rectangle(pos=self.pos, size=self.size)
        # self.bind(size=self._update_rect, pos=self._update_rect)

        for key, value in data.items():
            percentage = value[1]
            color = value[2]
            angle_end = angle_start + 3.6 * percentage
            # add part of Pie
            self.temp.append(PieSlice(pos=self.position, size=self.size,
                                      angle_start=angle_start,
                                      angle_end=angle_end, color=color,
                                      name=key))
            self.add_widget(self.temp[count])
            angle_start = angle_end
            count += 1

        self.bind(size=self._update_temp, pos=self._update_temp)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _update_temp(self, instance, value):
        for slice in self.temp:
            slice.pos = instance.pos


# Class for making one part of Pie
# Main functions for handling move out/in and click inside area recognition
class PieSlice(FloatLayout):
    def __init__(self, pos, color, size, angle_start, angle_end, name, **kwargs):
        super(PieSlice, self).__init__(**kwargs)
        self.moved = False
        self.angle = 0
        self.name = name
        self.value = (angle_end - angle_start) / 360 * 100

        with self.canvas.before:
            Color(*color)
            self.slice = Ellipse(pos=pos, size=size,
                                 angle_start=angle_start,
                                 angle_end=angle_end)

        self.value_label = Label(text=f"{self.value:.1f}%", size=(20, 20), size_hint=(None, None), valign="center",
                                 halign="center")
        self.add_widget(self.value_label)

        self.bind(size=self._update_slice, pos=self._update_slice)
        self.bind(size=self._update_label, pos=self._update_label)

    def _update_slice(self, instance, value):
        self.slice.pos = (instance.pos[0], instance.pos[1])
        self.slice.size = (min(instance.size) for i in range(2))

    def get_label_pos(self, modifier: float = 1.0):
        reversed_angle = int(360 - self.slice.angle_end + ((self.slice.angle_end - self.slice.angle_start) / 2))
        transform_matrix = [
            [cos(radians(reversed_angle)), -sin(radians(reversed_angle))],
            [sin(radians(reversed_angle)), cos(radians(reversed_angle))]
        ]
        center_coordinate = [self.slice.pos[0] + self.slice.size[0] / 2, self.slice.pos[1] + self.slice.size[1] / 2]
        base_coordinate = [0, self.slice.size[0] / 2]

        target_coordinate = [0, 0]
        for index, vector in enumerate(transform_matrix):
            for i in range(len(vector)):
                target_coordinate[index] += vector[i] * base_coordinate[i]

        for i in range(len(target_coordinate)):
            target_coordinate[i] = int(target_coordinate[i] * modifier)
            target_coordinate[i] = target_coordinate[i] + center_coordinate[i] - self.value_label.size[i] / 2

        return target_coordinate

    def _update_label(self, *args):
        value_label_pos = self.get_label_pos(modifier=0.6)
        self.value_label.pos = value_label_pos

    # Function for moving part of pie outside of circle
    def move_pie_out(self):
        ang = self.slice.angle_start + (self.slice.angle_end - self.slice.angle_start) / 2
        vector_x = cos(radians(ang - 90)) * 50
        vector_y = sin(radians(ang + 90)) * 50
        if not self.moved:
            self.slice.pos = Vector(vector_x, vector_y) + self.slice.pos
            self.moved = True
        else:
            self.slice.pos = Vector(-vector_x, -vector_y) + self.slice.pos
            self.moved = False

    # Function for moving part of pie inside of circle
    def move_pie_in(self):
        ang = self.slice.angle_start + (self.slice.angle_end - self.slice.angle_start) / 2
        vector_x = cos(radians(ang - 90)) * 50
        vector_y = sin(radians(ang + 90)) * 50
        if self.moved:
            self.slice.pos = Vector(-vector_x, -vector_y) + self.slice.pos
            self.moved = False

    # Click handler on Pie Part
    # If click is inside Pie Part, move it out
    def on_touch_down(self, touch):
        if self.is_inside_pie(*touch.pos):
            self.move_pie_out()

    # Function for checking if click is inside Pie Slice
    def is_inside_pie(self, *touch_pos):
        y_pos = touch_pos[1] - self.slice.pos[1] - self.slice.size[1] / 2
        x_pos = touch_pos[0] - self.slice.pos[0] - self.slice.size[0] / 2
        angle = degrees(1.5707963268 - atan2(y_pos, x_pos))
        if angle < 0:
            angle += 360
        self.angle = angle
        radius = sqrt(pow(x_pos, 2) + pow(y_pos, 2))
        if self.slice.angle_start < angle < self.slice.angle_end:
            return radius < self.slice.size[0] / 2


if __name__ == '__main__':
    from kivy.app import App


    class MainWindow(GridLayout):
        def __init__(self, **kwargs):
            super(MainWindow, self).__init__(**kwargs)
            self.cols = 1
            self.rows = 2

            # with self.canvas:
            # Color(1, 0, 0, 1)
            # self.rect = Rectangle(pos=self.pos, size=self.size)
            # self.bind(size=self._update_rect, pos=self._update_rect)

            in_data = {"Opera": (350, [.1, .1, .4, 1]),
                       "Steam": (234, [.1, .7, .3, 1]),
                       "Overwatch": (532, [.9, .1, .1, 1]),
                       "PyCharm": (485, [.8, .7, .1, 1]),
                       "YouTube": (221, [.3, .4, .9, 1])}

            # Temporary variables

            self.chart = PieGraph(data=in_data, position=self.pos, size=self.size, legend_enable=True)
            self.add_widget(self.chart)
            self.bind(size=self._update_graph, pos=self._update_graph)

        # def _update_rect(self, instance, value):
        # self.rect.pos = instance.pos
        # self.rect.size = instance.size

        def _update_graph(self, instance, value):
            self.chart.pos = instance.pos
            self.chart.size = instance.size


    class PieChartApp(App):
        def build(self):
            fl = FloatLayout()
            mw = MainWindow(size_hint=(None, None), size=(360, 300), pos=(200, 500))
            fl.add_widget(mw)
            return fl


    PieChartApp().run()
