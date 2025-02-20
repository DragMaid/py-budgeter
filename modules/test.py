from kivy.app import App
from kivy.graphics import Rectangle, Color
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label


class GraphWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas.clear()
        with self.canvas:
            Color(1, 1, 1, 1)  # White background
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_rect, pos=self.update_rect)
        self.plot_bar_graph()
        self.add_month_labels()

    def update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos

    def plot_bar_graph(self):
        self.months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        values = [10, 20, 30, 50, 40, 70, 90, 60, 30, 20, 80, 100]  # Sample data

        bar_width = self.width / 13  # Leave space for labels
        max_value = max(values)

        for i, value in enumerate(values):
            bar_height = (value / max_value) * (self.height - 50)
            with self.canvas:
                Color(1, 0, 0, 1)  # Red bars
                Rectangle(pos=(i * bar_width + 10, 50), size=(bar_width * 0.8, bar_height))

    def add_month_labels(self):
        label_layout = GridLayout(cols=12, size_hint_y=None, height=30)
        for month in self.months:
            label_layout.add_widget(
                Label(text=f'[color=ff3333]{month}[/color]', size_hint_x=None, width=50, markup=True))
        self.add_widget(label_layout)


if __name__ == '__main__':
    class GraphApp(App):
        def build(self):
            bl = BoxLayout(size_hint=[1, 1])
            bl.add_widget(GraphWidget(size=[500, 500]))
            return bl


    GraphApp().run()
