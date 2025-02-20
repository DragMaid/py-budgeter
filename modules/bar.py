from kivy.graphics import Rectangle, Color
from kivy.uix.label import Label
from kivy.utils import get_color_from_hex as rgb
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout

from modules.graph import Graph
from modules.legend import LegendTree

LABEL_HEIGHT = 20
BAR_INIT_HEIGHT = 0
DEFAULT_COLOR_TEMPLATE = [
    [0, 0.247, 0.36, 1],
    [0.345, 0.313, 0.553, 1],
    [0.737, 0.313, 0.564, 1],
    [1, 0.388, 0.38, 1],
    [1, 0.65, 0, 1]]

DEFAULT_GRAPH_THEME = {
    'label_options': {'color': rgb('444444'), 'bold': True},
    'background_color': rgb('f8f8f2'),
    'tick_color': rgb('808080'),
    'border_color': rgb('808080')
}


class StackedBarGraph(MDBoxLayout):
    def __init__(self, months=[], data=[], keys=[], color_list=DEFAULT_COLOR_TEMPLATE, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)  # Increase graph size
        self.months: list = months
        self.values: list = data
        self.color_list: list = color_list
        self.bars: list = []
        self.keys: list = keys
        if not self.is_valid_data(): raise Exception
        self.plot_bar_graph()
        self.bind(size=self.plot_bar_graph, pos=self.plot_bar_graph)

    def is_valid_data(self):
        if len(self.values) == 0 or len(self.months) != len(self.values[0]):
            return False
        return True

    def get_max_value(self):
        max_value = [0] * len(self.values[0])
        for value_list in self.values:
            for j, value in enumerate(value_list):
                max_value[j] += value
        max_value = max(max_value)
        return max_value

    def plot_bar_graph(self, *args):
        for bar in self.bars:
            self.canvas.remove(bar)
        self.bars = []

        self.column_width = self.width / len(self.months)  # Ensure proper spacing
        self.bar_width = self.column_width * 0.8
        self.bar_padding_left = self.bar_width * 0.1

        max_value = [0 for x in range(len(self.values[0]))]
        for value_list in self.values:
            for i, value in enumerate(value_list):
                max_value[i] += value
        max_value = max(max_value)

        last_height = [BAR_INIT_HEIGHT for x in range(len(self.values[0]))]
        for j, value_list in enumerate(self.values):
            bar_color = self.color_list[j]
            for i, value in enumerate(value_list):
                bar_height = (value / max_value) * (self.height - 100)  # Scale bars properly
                with self.canvas:
                    Color(rgba=bar_color)
                    self.bars.append(Rectangle(
                        pos=(self.column_width * i + self.bar_padding_left + self.pos[0], last_height[i] + self.pos[1]),
                        size=(self.bar_width, bar_height)))
                last_height[i] += bar_height


class StackedBarWidget(MDFloatLayout):
    def __init__(self, bar_graph, graph_theme=DEFAULT_GRAPH_THEME, **kwargs):
        super().__init__(**kwargs)
        self.bar_graph = bar_graph
        self.max_value = self.bar_graph.get_max_value()
        self.graph_outer = Graph(
            y_ticks_minor=int(self.max_value / 25),
            y_ticks_major=int(self.max_value / 5),
            y_grid_label=True,
            x_grid_label=True,
            padding=5,
            xlog=False,
            ylog=False,
            x_grid=True,
            y_grid=True,
            ymin=0,
            ymax=self.max_value,
            y=LABEL_HEIGHT,
            **graph_theme)
        self.data = {}

        self.add_widget(self.graph_outer)
        self.add_widget(self.bar_graph)

        self.graph_outer.bind(view_pos=self.reposition_bar)
        self.graph_outer.bind(size=self.resize_bar, view_pos=self.resize_bar, pos=self.reposition_bar)
        self.graph_outer.bind(size=self.update_label_layout, pos=self.update_label_layout,
                              view_pos=self.update_label_layout)

        self.add_month_labels()

        # Add a legend for stacked bar graph
        for index, value in enumerate(self.bar_graph.keys):
            self.data[value] = [0, 0, self.bar_graph.color_list[index]]

        self.legend = LegendTree(self.data, self.pos, self.size)
        self.add_widget(self.legend)

        self.bind(size=self._update_plot, pos=self._update_plot)
        self.bind(size=self._update_legend, pos=self._update_legend)

    def _update_plot(self, instance, value):
        self.graph_outer.size[1] = instance.size[1] * 2 / 3
        print(self.graph_outer.size[1])
        self.graph_outer.pos[1] = instance.pos[1] + instance.size[1] - self.graph_outer.size[1]

    def _update_legend(self, instance, value):
        self.legend.size = (instance.size[0], instance.size[1] * 1 / 3 - self.label_layout.size[1])
        self.legend.pos = (instance.pos[0], instance.pos[1])

    def reposition_bar(self, *args):
        self.bar_graph.pos[0] = self.graph_outer.pos[0] + self.graph_outer.view_pos[0]
        self.bar_graph.pos[1] = self.graph_outer.pos[1] + self.graph_outer.view_pos[1]

    def resize_bar(self, *args):
        self.bar_graph.size[0] = self.graph_outer.size[0] - self.graph_outer.view_pos[0]
        self.bar_graph.size[1] = self.graph_outer.size[1] - self.graph_outer.view_pos[1]

    def add_month_labels(self):
        self.label_layout = MDBoxLayout(orientation='horizontal', size_hint_x=1, size_hint_y=None, height=LABEL_HEIGHT)
        for month in self.bar_graph.months:
            label = Label(text=f'[color=#000000]{month}[/color]', size_hint_x=None, markup=True, halign="center",
                          font_size='10sp')
            label.bind(size=self.update_label_alignment)
            self.label_layout.add_widget(label)
        self.add_widget(self.label_layout)

    def update_label_layout(self, *args):
        self.label_layout.size[0] = self.graph_outer.size[0] - self.graph_outer.view_pos[0]
        self.label_layout.pos[0] = self.graph_outer.view_pos[0]
        self.label_layout.pos[1] = self.graph_outer.pos[1] - self.label_layout.size[1]
        for label in self.label_layout.children:
            label.width = self.bar_graph.column_width

    def update_label_alignment(self, instance, value):
        instance.text_size = (value[0], None)  # Ensures proper alignment


if __name__ == '__main__':
    from kivymd.app import MDApp


    class Test(MDApp):
        def build(self):
            self.bar = StackedBarGraph(months=["Jan", "Feb", "Mar", "May"], data=[[1, 2, 0, 5], [1, 5, 9, 8]])
            self.bl = StackedBarWidget(self.bar)
            return self.bl


    Test().run()
