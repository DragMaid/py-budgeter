from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label


class LegendTree(GridLayout):
    def __init__(self, data, position, size, **kwargs):
        super(LegendTree, self).__init__(**kwargs)
        self.cols = 1
        self.rows = 1
        self.position = position
        self.size = size
        self.padding = [20, 0, 0, 0]
        self.spacing = 5
        self.legends = []
        self.size_hint = (None, None)

        count = 0
        for key, value in data.items():
            color = value[2]
            # add legend (rectangle and text)
            self.legends.append(Legend(pos=(self.position[0], self.position[1] - count * self.size[1] * 0.15),
                                       size=self.size,
                                       color=color,
                                       name=key))
            self.add_widget(self.legends[count])
            self.rows += 1
            count += 1

        # Background for debugging
        # with self.canvas.before:
        # Color(1, 0, 1, 1)
        # self.rect = Rectangle(pos=self.pos, size=self.size)
        # self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


# Class for creating Legend
class Legend(FloatLayout):
    def __init__(self, pos, size, color, name, **kwargs):
        super(Legend, self).__init__(**kwargs)
        # self.cols = 2
        # self.rows = 1
        self.size = size
        self.button_padding_left = 5
        self.name = name
        with self.canvas.before:
            Color(*color)
            self.rect = Rectangle(pos=(pos[0] + size[0] * 1.3, pos[1] + size[1] * 0.9),
                                  size=(size[0] * 0.1, size[1] * 0.1))
            self.label = Label(text=f"[color=#000000]{name}[/color]", halign='left', valign='center', markup=True)

        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = (instance.pos[0], instance.pos[1])
        self.rect.size = (max(min(self.size[0] * 0.1, self.size[1] * 0.1), 25) for i in range(2))
        self.label.pos = (self.rect.pos[0] + self.rect.size[0] + self.button_padding_left * 2,
                          self.rect.pos[1])
        self.label.size = (self.size[0] - self.rect.size[0] - self.button_padding_left * 3, self.rect.size[1])
        self.label.text_size = self.label.size
