import datetime
import json

import os

SRC_DIR = os.path.dirname(os.path.realpath(__file__))
INFO_DIR = os.path.join(SRC_DIR, "../info")
ASSETS_DIR = os.path.join(SRC_DIR, "../assets")
CREDENTIAL_PATH = os.path.join(INFO_DIR, "credential.json")
AUTHORIZED_PATH = os.path.join(INFO_DIR, "authorized_user.json")
CONFIG_PATH = os.path.join(INFO_DIR, "config.json")
PIE_CHART_PATH = os.path.join(ASSETS_DIR, "pie.png")
BAR_CHART_PATH = os.path.join(ASSETS_DIR, "bar.png")

from kivy.config import Config

Config.set('graphics', 'resizable', False)
Config.set('input', 'mouse', 'mouse,disable_multitouch')
Config.set('kivy', 'window_icon', os.path.join(ASSETS_DIR, "logo-transparent.png"))

from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.uix.anchorlayout import AnchorLayout
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivymd.app import MDApp, StringProperty
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list.list import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.navigationdrawer import MDNavigationDrawerItem
from kivymd.uix.bottomnavigation import MDBottomNavigation
from kivymd.uix.button.button import MDLabel, MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.transition import MDSlideTransition
from kivymd.uix.anchorlayout import MDAnchorLayout
from kivymd.uix.label.label import MDFloatLayout, MDIcon
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu.menu import MDDropdownMenu
from kivymd.uix.list import OneLineIconListItem
from kivymd.uix.pickers import MDDatePicker
from utils import SheetManager
from threading import Thread

# For graphing features
from math import pi
from pandas import Series
from bokeh.io import export_png
from bokeh.palettes import HighContrast3, Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum


class TemplateNavigationBar(MDBottomNavigation):
    pass


class TemplateTopBar(MDTopAppBar):
    pass


class LoadingOverlay(MDFloatLayout):
    pass


class SheetsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__()
        self.sheet_data = None
        self.scrollview = MDScrollView(do_scroll_x=False, do_scroll_y=True)
        self.add_widget(self.scrollview)

        self.card_container = MDGridLayout(cols=1, padding=20, spacing=[0, 20])
        self.card_container.size_hint_y = None
        self.scrollview.add_widget(self.card_container)
        self.card_container.bind(minimum_height=self.card_container.setter("height"))  # type: ignore

        self.create_button = FreeCreateButton()
        self.add_widget(self.create_button)

    def disable_create_button(self, state: bool):
        self.create_button.disabled = state

    def card_function(self, card, index):
        self.set_selected_card(card, index)
        self.update_form()
        self.change_form_screen()

    def update_form(self, delete_disabled=False):
        self.parent.get_screen("cardview screen").update_form(delete_disabled=delete_disabled)

    def set_selected_card(self, card, index):
        self.parent.get_screen("cardview screen").set_selected_card(card, index)

    def change_form_screen(self):
        self.parent.transition = MDSlideTransition(direction="left")
        self.parent.current = "cardview screen"

    def sheet_refresh(self):
        self.sheet_data = MDApp.get_running_app().sheet_manager.get_active_worksheet_data()
        self.ui_refresh()

    @mainthread
    def clear_cards(self):
        self.card_container.clear_widgets()

    @mainthread
    def ui_refresh(self):
        self.card_container.clear_widgets()
        for index in range(len(self.sheet_data) - 1, -1, -1):
            card = SheetCard(index, self.sheet_data[index], callback=self.card_function)
            self.card_container.add_widget(card)


class StatisticsScreen(MDScreen):
    MAX_BARS = 5

    def __init__(self, **kwargs):
        super().__init__()
        self.container = MDGridLayout(cols=1, rows=2)
        self.add_widget(self.container)

        self.pie_img = Image(source=PIE_CHART_PATH)
        self.bar_img = Image(source=BAR_CHART_PATH)

        self.container.add_widget(self.pie_img)
        self.container.add_widget(self.bar_img)

    def update_pie_chart(self):
        values = {}

        labels = MDApp.get_running_app().sheet_manager.get_categories()
        target_worksheet = MDApp.get_running_app().sheet_manager.get_active_worksheet()

        for category in labels:
            values[category] = MDApp.get_running_app().sheet_manager.calculate_sum_filter(
                filters=[["category", category]])

        data = Series(values).reset_index(name='value').rename(columns={'index': 'category'})
        data['angle'] = data['value'] / data['value'].sum() * 2 * pi
        data['color'] = Category20c[len(values)]

        p = figure(height=400, title=f"Pie Chart for {target_worksheet.title}", toolbar_location=None,
                   x_range=(-0.5, 1.0))

        p.wedge(x=0, y=1, radius=0.4,
                start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                line_color="white", fill_color='color', legend_field='category', source=data)
        export_png(p, filename=PIE_CHART_PATH)

    def update_bar_chart(self, start_index):
        last_worksheet_index = MDApp.get_running_app().sheet_manager.get_active_index()
        worksheets = MDApp.get_running_app().sheet_manager.get_all_worksheets()
        graph_size = min(len(worksheets) - start_index - 1, 5)
        time_stamps = [worksheets[start_index + inc].title for inc in range(graph_size)]
        option_data = {"time": time_stamps}
        for x in MDApp.get_running_app().PAID_FOR_OPTIONS:
            option_data[x] = []

        for inc in range(graph_size):
            MDApp.get_running_app().sheet_manager.set_active_worksheet(start_index + inc)
            for option in MDApp.get_running_app().PAID_FOR_OPTIONS:
                data = MDApp.get_running_app().sheet_manager.calculate_sum_filter(filters=[["paid for", option]])
                option_data[option].append(data)  # type: ignore

        MDApp.get_running_app().sheet_manager.set_active_worksheet(last_worksheet_index)

        p = figure(x_range=time_stamps, height=400, title="Bar chart for total budget usage", toolbar_location=None)

        p.vbar_stack(MDApp.get_running_app().PAID_FOR_OPTIONS, x='time', width=0.4, color=HighContrast3,
                     source=option_data, legend_label=MDApp.get_running_app().PAID_FOR_OPTIONS)
        export_png(p, filename=BAR_CHART_PATH)

    def statistics_refresh(self, start_index):
        self.update_pie_chart()
        self.update_bar_chart(start_index=start_index)
        self.image_refresh()

    @mainthread
    def image_refresh(self):
        self.pie_img.reload()
        self.bar_img.reload()


class SettingsScreen(MDScreen):
    sheet_id = StringProperty()
    credential = StringProperty()
    user_1 = StringProperty()
    user_2 = StringProperty()
    spending_1 = StringProperty()
    spending_2 = StringProperty()
    spending_diff = StringProperty()

    def __init__(self, **kwargs):
        super().__init__()
        self.sheet_id = MDApp.get_running_app().SHEET_ID
        self.credential = MDApp.get_running_app().CREDENTIAL
        self.user_1 = MDApp.get_running_app().USERS[0]
        self.user_2 = MDApp.get_running_app().USERS[1]

    def edit_config(self, *args):
        configs = []
        for field in [self.ids.credential, self.ids.sheet_id, self.ids.user_1, self.ids.user_2]:
            data = field.text.strip()
            if data == "":
                return
            configs.append(data)
        MDApp.get_running_app().write_config(configs[0], configs[1], [configs[2], configs[3]])
        MDApp.get_running_app().retrieve_saved_config()
        MDApp.get_running_app().on_start()

    def update_budget_split(self, data: list):
        diff = data[0][1] - data[1][1]
        self.spending_1 = f"{data[0][0]}: ${data[0][1]}"
        self.spending_2 = f"{data[1][0]}: ${data[1][1]}"
        self.spending_diff = f"Difference: ${diff:.2f}"


class FreeCreateButton(AnchorLayout):
    def __init__(self, **kwargs):
        super().__init__()
        self.empty_card = None

    def create_button_callback(self):
        index = MDApp.get_running_app().sheet_manager.get_active_rows() - 1
        self.empty_card = SheetCard(index, [""] * 7)
        self.parent.set_selected_card(self.empty_card, index)
        self.parent.update_form(delete_disabled=True)
        self.parent.change_form_screen()


class CardLabel(MDLabel):
    pass


class IconListItem(OneLineIconListItem):
    icon = StringProperty()


class DropDownBase:
    def __init__(self, caller, items=[], position="bottom", width_mult=5):
        self.menu = None
        self.caller = caller
        self.items = items
        self.position = position
        self.width_mult = width_mult
        self.create_dropdown_menu()

    @mainthread
    def create_dropdown_menu(self):
        self.menu = MDDropdownMenu(
            caller=self.caller,
            items=self.items,
            position=self.position,
            width_mult=self.width_mult
        )
        self.menu.bind()

    def open(self):
        self.menu.check_position_caller(None, None, None)  # type: ignore
        self.menu.open()

    def dropdown_callback(self, text: str):
        self.caller.text = text
        self.menu.dismiss()


class NotificationDialog:
    def __init__(self, text):
        self.text = text
        self.dialog = None

    def show(self):
        if not self.dialog:
            self.dialog = MDDialog(
                text=self.text,
                buttons=[
                    MDRaisedButton(
                        text="OK",
                        theme_text_color="Custom",
                        on_release=lambda _: self.dialog.dismiss(force=True)
                    ),
                ],
            )
        self.dialog.open()


class ConfirmDialog:
    def __init__(self, callback=None):
        self.dialog = None
        self.callback = callback

    def show(self):
        if not self.dialog:
            self.dialog = MDDialog(
                text="Are you sure you want to delete this entry?",
                buttons=[
                    MDRaisedButton(
                        text="Confirm",
                        theme_text_color="Custom",
                        on_release=self.confirm_callback
                    ),
                    MDRectangleFlatButton(
                        text="Cancel",
                        theme_text_color="Custom",
                        on_release=lambda _: self.dialog.dismiss()  # type: ignore
                    ),
                ],
            )
        self.dialog.open()

    def confirm_callback(self, *args):
        if self.callback: self.callback()
        if self.dialog: self.dialog.dismiss(force=True)


class StatusDropdown(DropDownBase):
    choices = [
        {"text": "Paid", "icon": "check-bold"},
        {"text": "Pending", "icon": "alpha-x-circle"},
    ]

    def __init__(self, caller):
        self.items = [{
            "viewclass": "IconListItem",
            "icon": item["icon"],
            "text": item["text"],
            "height": dp(56),
            "on_release": lambda text=item["text"]: self.dropdown_callback(text),
        } for item in self.choices]
        super().__init__(caller, items=self.items)


class CategoryDropdown(DropDownBase):
    choices = [
        {"text": "Food", "icon": "food"},
        {"text": "Transportation", "icon": "train-car"},
        {"text": "Essentials", "icon": "heart"},
        {"text": "Entertainment", "icon": "controller"}
    ]

    def __init__(self, caller):
        self.items = [{
            "viewclass": "IconListItem",
            "icon": item["icon"],
            "text": item["text"],
            "height": dp(56),
            "on_release": lambda text=item["text"]: self.dropdown_callback(text),
        } for item in self.choices]
        super().__init__(caller, items=self.items)


class PaidDropdown(DropDownBase):
    def __init__(self, caller, paid_for=False):
        self.paid_for = paid_for
        self.create_items()
        super().__init__(caller, items=self.items)

    def create_items(self):
        names = MDApp.get_running_app().USERS
        if self.paid_for:
            names = MDApp.get_running_app().PAID_FOR_OPTIONS
        self.items = [{
            "viewclass": "IconListItem",
            "icon": "account",
            "text": name,
            "height": dp(56),
            "on_release": lambda account_name=name: self.dropdown_callback(account_name), } for name in names]

class FormDatePicker:
    def __init__(self, caller):
        self.caller = caller
        self.date_dialog = MDDatePicker()
        self.date_dialog.bind(on_save=self.on_save, on_cancel=self.on_cancel)

    def open(self, *args):
        self.date_dialog.open()

    def on_cancel(self, *args):
        pass

    def on_save(self, instance, value, *args):
        self.caller.text = value.strftime("%d/%m/%Y")


class CardViewScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__()
        self.selected_card = None
        self.index = None
        self.scrollview = MDScrollView(do_scroll_x=False, do_scroll_y=True)

        self.screen_container = MDGridLayout(cols=1, orientation="lr-bt")
        self.form_container = MDGridLayout(cols=1, padding=10, spacing=10, size_hint_y=None)
        self.control_container = MDGridLayout(cols=1, rows=2, size_hint_x=1, size_hint_y=None)

        self.edit_control = MDGridLayout(cols=2, rows=1, padding=[10, 10, 10, 10], spacing=[10, 0], size_hint_x=1,
                                         size_hint_y=None, height="70px")

        self.edit_control_center = MDAnchorLayout(anchor_x="center", anchor_y="center")
        self.delete_control_center = MDAnchorLayout(anchor_x="center", anchor_y="center", padding=[10, 10],
                                                    height="50px")

        self.save_button = MDRaisedButton(text="save", size_hint=[.5, .7], on_release=self.save_button_callback)
        self.cancel_button = MDRectangleFlatButton(text="cancel", size_hint=[.5, .7],
                                                   on_release=self.cancel_button_callback)
        self.delete_button = MDRaisedButton(md_bg_color="red", text="delete", size_hint=[1, 1],
                                            on_release=self.delete_button_callback)

        self.edit_control.add_widget(self.save_button)
        self.edit_control.add_widget(self.cancel_button)

        self.edit_control_center.add_widget(self.edit_control)
        self.delete_control_center.add_widget(self.delete_button)

        self.control_container.add_widget(self.edit_control_center)
        self.control_container.add_widget(self.delete_control_center)

        self.screen_container.add_widget(self.control_container)
        self.screen_container.add_widget(self.form_container)
        self.scrollview.add_widget(self.screen_container)
        self.add_widget(self.scrollview)

        self.form_container.bind(minimum_height=self.form_container.setter("height"))  # type: ignore

        self.product_field = MDTextField(mode="rectangle", hint_text="Product", required=True)
        self.price_field = MDTextField(mode="rectangle", hint_text="Price", helper_text="Price must be a number",
                                       helper_text_mode="on_error", required=True)

        self.date_field = MDTextField(mode="rectangle", hint_text="Date", readonly=True, required=True)
        self.date_picker = FormDatePicker(self.date_field)
        self.date_field.bind(focus=lambda obj, focus: self.date_picker.open() if focus else False)

        self.category_field = MDTextField(mode="rectangle", hint_text="Category", readonly=True, required=True)
        self.category_dropdown = CategoryDropdown(self.category_field)
        self.category_field.bind(focus=lambda obj, focus: self.category_dropdown.open() if focus else False)

        self.status_field = MDTextField(mode="rectangle", hint_text="Status", readonly=True, required=True)
        self.status_dropdown = StatusDropdown(self.status_field)
        self.status_field.bind(focus=lambda obj, focus: self.status_dropdown.open() if focus else False)

        self.paid_for_field = MDTextField(mode="rectangle", hint_text="Paid for", readonly=True, required=True)
        self.paid_for_dropdown = PaidDropdown(self.paid_for_field, paid_for=True)
        self.paid_for_field.bind(focus=lambda obj, focus: self.paid_for_dropdown.open() if focus else False)

        self.paid_by_field = MDTextField(mode="rectangle", hint_text="Paid by", readonly=True, required=True)
        self.paid_by_dropdown = PaidDropdown(self.paid_by_field)
        self.paid_by_field.bind(focus=lambda obj, focus: self.paid_by_dropdown.open() if focus else False)

        self.fields = {"product": self.product_field,
                       "cost": self.price_field,
                       "date": self.date_field,
                       "category": self.category_field,
                       "status": self.status_field,
                       "paid for": self.paid_for_field,
                       "paid by": self.paid_by_field}

        for key, field in self.fields.items():
            self.form_container.add_widget(field)

    def update_users(self):
        self.paid_by_dropdown.create_items()
        self.paid_by_dropdown.create_dropdown_menu()
        self.paid_for_dropdown.create_items()
        self.paid_for_dropdown.create_dropdown_menu()

    def disable_delete_button(self, state):
        self.delete_button.disabled = state

    def set_selected_card(self, card, index):
        self.selected_card = card
        self.index = index

    def update_form(self, delete_disabled=False):
        self.disable_delete_button(delete_disabled)
        if not self.selected_card is None:
            data = self.selected_card.get_data()
            for key, field in self.fields.items():
                text = MDApp.get_running_app().sheet_manager.get_data_by_name(data, key)
                field.text = text if text != "unknown" else ""  # type: ignore

    def validate_form(self):
        if (self.date_field.text != ""
                and self.product_field.text != ""
                and self.category_field.text != ""
                and self.status_field.text != ""
                and self.paid_for_field.text != ""
                and self.paid_by_field.text != ""):

            price_text = self.price_field.text.strip()
            target = price_text
            if price_text[0] == "$":
                target = price_text[1:-1]
            try:
                float(target)
                self.price_field.error = False
                return True
            except ValueError:
                self.price_field.error = True
                return False
        return False

    def change_sheets_screen(self):
        self.parent.transition = MDSlideTransition(direction="right")
        self.parent.current = "sheets screen"

    def cancel_button_callback(self, *args):
        self.change_sheets_screen()

    def save_button_callback(self, *args):
        if self.selected_card and self.validate_form():
            MDApp.get_running_app().sheet_manager.modify_cell(
                self.selected_card.get_index(),
                date=self.date_field.text,
                expense=self.product_field.text,
                category=self.category_field.text,
                cost=self.price_field.text,
                status=self.status_field.text,
                paid_for=self.paid_for_field.text,
                paid_by=self.paid_by_field.text
            )
            self.parent.transition = MDSlideTransition(direction="right")
            MDApp.get_running_app().threaded_screen_update(MDApp.get_running_app().sheet_manager.get_active_index())
            self.parent.current = "sheets screen"

    def delete_button_callback(self, *args):
        dialog = ConfirmDialog(callback=self.delete_button_confirm)
        dialog.show()

    def delete_button_confirm(self):
        if self.selected_card:
            MDApp.get_running_app().sheet_manager.delete_entry(self.selected_card.get_index() + 2)
            MDApp.get_running_app().threaded_screen_update(MDApp.get_running_app().sheet_manager.get_active_index())
            self.change_sheets_screen()


class CardTextArea(MDBoxLayout):
    price = StringProperty()
    product = StringProperty()
    date = StringProperty()

    def __init__(self, price="", product="", date=""):
        super().__init__()
        self.price = price
        self.product = product
        self.date = date
        self.price_label = CardLabel(text=f"Price: {price}")
        self.product_label = CardLabel(text=f"Product: {product}")
        self.date_label = CardLabel(text=f"Date: {date}")
        self.add_widget(self.price_label)
        self.add_widget(self.product_label)
        self.add_widget(self.date_label)


class CardLeftWidget(MDBoxLayout):
    CATEGORY_ICON = {
        "food": ["food", "orange"],
        "transportation": ["train-car", "purple"],
        "essentials": ["heart", "yellow"],
        "entertainment": ["controller", "green"],
        "unknown": ["help", "black"]
    }

    STATE_COLOR = {
        "paid": {"background": "green", "text": "#FFFFFF"},
        "pending": {"background": "red", "text": "#000000"},
        "unknown": {"background": "red", "text": "#000000"}
    }

    def __init__(self, category="", status=""):
        super().__init__()
        self.category = category.lower()
        self.status = status.lower()

        # Just a temporary fix for now
        self.secondary_widget = MDLabel(text=self.status, halign="center", valign="middle", theme_text_color="Custom")
        self.secondary_widget.md_bg_color = self.STATE_COLOR[self.status]["background"]
        self.secondary_widget.text_color = self.STATE_COLOR[self.status]["text"]
        self.secondary_widget.size_hint = (.8, .9)
        self.ids.secondary_container.add_widget(self.secondary_widget)

        self.primary_widget = MDIcon(icon=self.CATEGORY_ICON[self.category][0])
        self.ids.primary_container.md_bg_color = self.CATEGORY_ICON[self.category][1]
        self.ids.primary_container.add_widget(self.primary_widget)

    def modify_icon(self, icon):
        self.primary_widget.icon = icon

    def modify_chip_text(self, text):
        self.secondary_widget.text = text


class SheetCard(ButtonBehavior, MDBoxLayout):  # type: ignore
    def __init__(self, index, data: list, callback=None):
        super(SheetCard, self).__init__()
        self.index = index
        self.data = data
        self.left_widget = CardLeftWidget(
            category=MDApp.get_running_app().sheet_manager.get_data_by_name(data, "category"),
            status=MDApp.get_running_app().sheet_manager.get_data_by_name(data, "status"))
        self.text_area = CardTextArea(date=MDApp.get_running_app().sheet_manager.get_data_by_name(data, "date"),
                                      product=MDApp.get_running_app().sheet_manager.get_data_by_name(data, "product"),
                                      price=MDApp.get_running_app().sheet_manager.get_data_by_name(data, "cost"))
        self.add_widget(self.left_widget)
        self.add_widget(self.text_area)

        if not callback is None:
            self.bind(on_release=lambda x=index: callback(self, x))

    def get_data(self): return self.data

    def set_data(self, data): self.data = data

    def get_index(self): return self.index

    def set_index(self, value): self.index = value


class WorksheetNavigationItem(MDNavigationDrawerItem):
    def __init__(self, index, text, callback):
        super().__init__(icon="calendar", text=text, on_release=lambda _: callback(index))
        self.index = index


class App(MDApp):
    thread = None
    worksheet_items = []
    TODAY_MONTH = datetime.date.today().strftime("%B").lower()
    TODAY_YEAR = datetime.date.today().strftime("%Y")
    sheet_manager = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nav_drawer = None
        self.loading_overlay = None
        self.CREDENTIAL = None
        self.PAID_FOR_OPTIONS = None
        self.USERS = None
        self.SHEET_ID = None
        self.DATA = None
        self.retrieve_saved_config()

    def retrieve_saved_config(self):
        with open(CONFIG_PATH, "r") as file:
            self.DATA = json.load(file)
            self.SHEET_ID = self.DATA["sheet_id"]
            self.USERS = self.DATA["users"]
            self.PAID_FOR_OPTIONS = self.USERS + ["Both"]

        with open(CREDENTIAL_PATH, "r") as file:
            self.CREDENTIAL = file.read().strip()

    def write_config(self, credential, sheet_id, users):
        with open(CREDENTIAL_PATH, "w") as file:
            file.write(credential)
        with open(CONFIG_PATH, "w") as file:
            self.DATA["sheet_id"] = sheet_id
            self.DATA["users"] = users
            file.write(json.dumps(self.DATA))

    def clear_nav_worksheets(self):
        for widget in self.worksheet_items:
            self.nav_drawer.children[0].children[0].remove_widget(widget)
        self.worksheet_items = []

    @mainthread
    def clear_nav_main(self):
        self.clear_nav_worksheets()

    @mainthread
    def update_nav_worksheets(self):
        self.clear_nav_worksheets()
        worksheets = MDApp.get_running_app().sheet_manager.get_all_worksheets()
        for index in range(len(worksheets) - 1):
            worksheet_item = WorksheetNavigationItem(index, worksheets[index].title, self.worksheet_item_callback)
            self.nav_drawer.children[0].add_widget(worksheet_item)
            self.worksheet_items.append(worksheet_item)

    def worksheet_item_callback(self, index):
        self.select_active_worksheet(index)
        self.threaded_screen_update(index)
        self.nav_drawer.set_state("close")

    def select_active_worksheet(self, index):
        MDApp.get_running_app().sheet_manager.set_active_worksheet(index)
        self.root.ids.top_nav.title = MDApp.get_running_app().sheet_manager.get_active_worksheet().title  # type: ignore

    def screen_update(self, start_index):
        MDApp.get_running_app().sheet_manager.update_all_worksheets()
        self.select_active_worksheet(start_index)
        self.root.ids.top_nav.title = MDApp.get_running_app().sheet_manager.get_active_worksheet().title  # type: ignore
        self.root.ids.bottom_nav.ids.set_scr.update_budget_split(
            MDApp.get_running_app().sheet_manager.split_budget())  # type: ignore
        self.root.ids.bottom_nav.ids.scr_mgr.get_screen("cardview screen").update_users()  # type: ignore
        self.root.ids.bottom_nav.ids.scr_mgr.get_screen("sheets screen").sheet_refresh()  # type: ignore
        self.root.ids.bottom_nav.ids.stat_scr.statistics_refresh(start_index=start_index)  # type: ignore
        self.update_nav_worksheets()
        self.close_loading_screen()
        self.thread = None

    @mainthread
    def open_loading_screen(self):
        self.loading_overlay = LoadingOverlay()
        self.root.add_widget(self.loading_overlay)

    @mainthread
    def close_loading_screen(self):
        self.root.remove_widget(self.loading_overlay)

    def threaded_screen_update(self, start_index):
        self.open_loading_screen()
        if self.thread is None:
            self.thread = Thread(target=self.screen_update, args=(start_index,))
            self.thread.start()

    @mainthread
    def open_error_dialog(self):
        error_dialog = NotificationDialog(
            "[ERROR] A problem arose while trying to connect to google sheet!! Please check your connections or ensure credential settings are correct")
        error_dialog.show()

    def startup_process(self):
        try:
            self.root.ids.bottom_nav.ids.scr_mgr.get_screen("sheets screen").clear_cards()  # type: ignore
            self.clear_nav_main()
            MDApp.get_running_app().sheet_manager = SheetManager(
                credential_path=CREDENTIAL_PATH,
                authorized_path=AUTHORIZED_PATH,
                sheet_id=MDApp.get_running_app().SHEET_ID,
                users=MDApp.get_running_app().USERS)
            MDApp.get_running_app().sheet_manager.update_all_worksheets()
            if self.is_new_month():
                MDApp.get_running_app().sheet_manager.create_new_month_sheet(self.TODAY_MONTH, self.TODAY_YEAR)
            self.screen_update(0)
            self.root.ids.bottom_nav.ids.scr_mgr.get_screen("sheets screen").disable_create_button(False)  # type: ignore
        except:
            self.root.ids.bottom_nav.ids.scr_mgr.get_screen("sheets screen").disable_create_button(True)  # type: ignore
            self.open_error_dialog()

        self.close_loading_screen()
        self.thread = None

    def threaded_startup_process(self):
        self.open_loading_screen()
        if self.thread is None:
            self.thread = Thread(target=self.startup_process)
            self.thread.start()

    def is_new_month(self):
        last_date = MDApp.get_running_app().sheet_manager.get_last_sheet_date()
        if (self.TODAY_MONTH != last_date["month"] or
                self.TODAY_YEAR != last_date["year"]):
            return True
        return False

    def on_start(self):
        self.nav_drawer = self.root.ids.navigation_drawer  # type: ignore
        self.threaded_startup_process()

    def build(self):
        self.title = "Py-Budgeter"
        self.theme_cls.material_style = "M3"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.accent_palette = "Red"
        return Builder.load_file("./styles.kv")


if __name__ == "__main__":
    App().run()
