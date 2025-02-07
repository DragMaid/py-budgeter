from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color
from graph import Graph

LABEL_HEIGHT = 40
BAR_INIT_HEIGHT = 0
DEFAULT_COLOR_TEMPLATE = [
        [0, 0.247, 0.36, 1], 
        [0.345, 0.313, 0.553, 1],
        [0.737, 0.313, 0.564, 1],
        [1, 0.388, 0.38, 1], 
        [1, 0.65, 0, 1]]

class StackedBarGraph(MDBoxLayout):
    def __init__(self, months=[], data=[], color_list=DEFAULT_COLOR_TEMPLATE, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)  # Increase graph size
        if len(months) != len(data[0]): raise Exception
        self.months : list = months
        self.values : list = data
        self.color_list : list = color_list
        self.bars : list = []
        # Set background for debugging
        with self.canvas:
            Color(1, 0, 0, 1)  # White background
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.plot_bar_graph()
        self.bind(size=self.update_rect, pos=self.update_rect)

        self.plot_bar_graph()

    def update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos
        self.plot_bar_graph()

    def get_max_value(self):
        max_value = [0] * len(self.values[0])
        for value_list in self.values:
            for j, value in enumerate(value_list):
                max_value[j] += value
        max_value = max(max_value)
        return max_value

    def plot_bar_graph(self):
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
                    self.bars.append(Rectangle(pos=(self.column_width * i + self.bar_padding_left + self.pos[0], last_height[i] + self.pos[1]), size=(self.bar_width, bar_height)))
                last_height[i] += bar_height


class StackedBarWidget(MDFloatLayout):
    def __init__(self, bar_graph, **kwargs):
        super().__init__(**kwargs)
        self.bar_graph = bar_graph
        self.max_value = self.bar_graph.get_max_value()
        self.graph_outer= Graph(
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
            y=LABEL_HEIGHT) 

        self.add_widget(self.graph_outer)
        self.add_widget(self.bar_graph)

        # self.graph.bind(view_pos=self.reposition_bar)
        self.graph_outer.bind(size=self.resize_bar, pos=self.reposition_bar)
        self.graph_outer.bind(size=self.update_label_layout, pos=self.update_label_layout)

        self.add_month_labels()

    def reposition_bar(self, *args):
        self.bar_graph.pos[0] = self.graph_outer.pos[0] + self.graph_outer.view_pos[0]
        self.bar_graph.pos[1] = self.graph_outer.pos[1] + self.graph_outer.view_pos[1]

    def resize_bar(self, *args):
        self.bar_graph.size = self.graph_outer.size

    def add_month_labels(self):
        self.label_layout = MDBoxLayout(orientation='horizontal', size_hint_x=1, size_hint_y=None, height=40, md_bg_color="cyan")
        for month in self.bar_graph.months:
            label = Label(text=f'[color=ff3333]{month}[/color]', size_hint_x=None, markup=True, halign="center")
            label.bind(size=self.update_label_alignment)
            self.label_layout.add_widget(label)
        self.add_widget(self.label_layout)

    def update_label_layout(self, *args):
        self.label_layout.size[0] = self.graph_outer.size[0]
        self.label_layout.pos[0] = self.graph_outer.view_pos[0]
        for label in self.label_layout.children:
            label.width = self.bar_graph.column_width
        print(self.label_layout.pos)

    def update_label_alignment(self, instance, value):
        instance.text_size = (value[0], None)  # Ensures proper alignment

if __name__ == '__main__':
    from kivymd.app import MDApp
    class Test(MDApp):
        def build(self):
            self.bl = MDFloatLayout(size_hint=[1,1], md_bg_color="green")
            self.bar = StackedBarGraph(months=["Jan", "Feb", "Mar", "May"], data=[[1,2,0,5],[1,5,9,8]])     
            max_value = self.bar.get_max_value()

            # self.bl = StackedBarWidget(self.bar, md_bg_color="green")
            # max_value = self.bar.

            self.graph = Graph(
                y_ticks_minor=int(max_value / 25),
                y_ticks_major=int(max_value / 5),
                y_grid_label=True,
                x_grid_label=True,
                padding=5,
                xlog=False,
                ylog=False,
                x_grid=True,
                y_grid=True,
                ymin=0,
                ymax=max_value,
                y=LABEL_HEIGHT) 

            self.bl.add_widget(self.graph)
            self.bl.add_widget(self.bar)
            self.graph.bind(view_pos=self.reposition_bar)
            self.graph.bind(size=self.resize_bar)
            self.graph.bind(size=self.update_label_layout)
            self.add_month_labels()
            return self.bl

        def reposition_bar(self, *args):
            self.bar.pos[0] = self.graph.pos[0] + self.graph.view_pos[0]
            self.bar.pos[1] = self.graph.pos[1] + self.graph.view_pos[1]

        def resize_bar(self, *args):
            self.bar.size = self.graph.size

        def add_month_labels(self):
            self.label_layout = MDBoxLayout(orientation='horizontal', size_hint_x=1, size_hint_y=None, height=40, md_bg_color="cyan")
            for month in self.bar.months:
                label = Label(text=f'[color=ff3333]{month}[/color]', size_hint_x=None, markup=True, halign="center")
                label.bind(size=self.update_label_alignment)
                self.label_layout.add_widget(label)
            self.bl.add_widget(self.label_layout)

        def update_label_layout(self, *args):
            self.label_layout.size[0] = self.graph.size[0]
            self.label_layout.pos[0] = self.graph.view_pos[0]
            for label in self.label_layout.children:
                label.width = self.bar.column_width
            print(self.label_layout.pos)

        def update_label_alignment(self, instance, value):
            instance.text_size = (value[0], None)  # Ensures proper alignment
                       
    Test().run()

