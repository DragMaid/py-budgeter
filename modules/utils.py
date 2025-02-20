import datetime
import os

import gspread

# | date | product | category | cost | status | paid_for | paid_by
STRUCTURE_DICT = {"date": 0, "product": 1, "category": 2, "cost": 3, "status": 4, "paid for": 5, "paid by": 6}
CATEGORIES = ["Food", "Transportation", "Essentials", "Entertainment"]
STATUSES = ["Paid", "Pending"]


class SheetManager:
    def __init__(self, credential_path="", authorized_path="", sheet_id="", users=[]):
        self.GOOGLE_SHEET = None
        self.GOOGLE_ACCOUNT = None
        self.last_index = None
        self.active_worksheet = None
        self.worksheet_data = None
        self.active_index = None
        self.worksheets = []

        if len(users) != 2: raise Exception("[ERROR]: Invalid number of users")
        self.USERS = users
        self.PAID_FOR_OPTIONS = self.USERS + ["Both"]

        self.SHEET_ID = sheet_id
        self.CREDENTIAL_PATH = credential_path
        self.AUTHORIZED_PATH = authorized_path

        try:
            self.init_gspread()
        except Exception as e:
            if type(e).__name__ == "RefreshError":
                os.remove(self.AUTHORIZED_PATH)
                self.init_gspread()

    def init_gspread(self):
        self.GOOGLE_ACCOUNT = gspread.oauth(
            credentials_filename=self.CREDENTIAL_PATH,
            authorized_user_filename=self.AUTHORIZED_PATH)  # type: ignore
        self.GOOGLE_SHEET = self.GOOGLE_ACCOUNT.open_by_key(self.SHEET_ID)

    def update_all_worksheets(self):
        self.worksheets = self.GOOGLE_SHEET.worksheets()
        if self.active_worksheet is None:
            self.set_active_worksheet(0)

    def update_first_worksheet(self):
        first_worksheet = self.GOOGLE_SHEET.get_worksheet(0)
        if len(self.worksheets) > 0:
            self.worksheets[0] = first_worksheet
        else:
            self.worksheets.append(first_worksheet)
        self.set_active_worksheet(0)

    def get_active_index(self):
        return self.active_index

    def get_paid_for_options(self):
        return self.PAID_FOR_OPTIONS

    def get_categories(self):
        return CATEGORIES

    def get_element_index(self, element):
        return STRUCTURE_DICT[element]

    def get_data_by_name(self, data, name):
        data = data[STRUCTURE_DICT[name.lower().strip()]]
        if data == "":
            return "unknown"
        return data

    def get_all_worksheets(self):
        return self.worksheets

    def get_worksheet_by_index(self, index):
        return self.worksheets[index]

    def get_last_sheet_date(self):
        last_sheet_name = self.worksheets[0].title.lower()
        last_date = last_sheet_name.split("-")
        return {"month": last_date[0], "year": last_date[1]}

    def set_active_worksheet(self, index):
        self.active_index = index
        self.active_worksheet = self.get_worksheet_by_index(index)
        self.worksheet_data = self.active_worksheet.get_all_values()  # type: ignore

    def create_new_month_sheet(self, month, year):
        self.worksheets[-1].duplicate(new_sheet_name=f"{month}-{year}")
        self.update_all_worksheets()
        self.set_active_worksheet(0)

    def get_active_worksheet(self):
        return self.active_worksheet

    def get_active_rows(self):
        return len(self.worksheet_data)

    def get_active_worksheet_data(self):
        return self.worksheet_data[1:]

    def get_today_format(self):
        return datetime.date.today().strftime("%d/%m/%Y")

    def modify_cell(self, row_index: int, date="today",
                    expense="", category="",
                    cost="", status="",
                    paid_for="", paid_by=""):
        date = self.get_today_format() if (date.lower() == "today") else date
        row_index = self.get_active_rows() + 1 if (row_index == -1) else row_index + 2
        work_range = f"A{row_index}:G{row_index}"
        formatted_date = datetime.datetime.strptime(date, '%d/%m/%Y').strftime('%m/%d/%Y')
        work_data = [[formatted_date, expense, category, cost, status, paid_for, paid_by]]
        self.active_worksheet.update(work_data, work_range)

    def delete_entry(self, index):
        self.active_worksheet.delete_rows(index)

    def is_filter_passed(self, filters, data):
        for group, target in filters:
            if not target == data[self.get_element_index(group)]:
                return False
        return True

    def format_entry(self, price_text):
        price_text = price_text.strip()
        if price_text[0] == "$":
            return float(price_text[1:])
        return float(price_text)

    def calculate_sum_filter(self, filters=[]):
        # Check for all filter conditions before summing up all values
        total_cost = 0
        for index in range(1, len(self.worksheet_data)):
            if self.is_filter_passed(filters, self.worksheet_data[index]):
                price_text = self.worksheet_data[index][self.get_element_index("cost")]
                price = self.format_entry(price_text)
                total_cost += price

        return round(total_cost, 2)

    def split_budget(self):
        # split money among the 2 registered users
        self.last_index = self.get_active_index()
        spending = [[self.USERS[0], 0], [self.USERS[1], 0]]
        spending[0][1] += self.calculate_sum_filter(filters=[["paid for", "Both"], ["paid by", self.USERS[0]]]) / 2
        spending[0][1] += self.calculate_sum_filter(filters=[["paid for", self.USERS[1]], ["paid by", self.USERS[0]]])
        spending[1][1] += self.calculate_sum_filter(filters=[["paid for", "Both"], ["paid by", self.USERS[1]]]) / 2
        spending[1][1] += self.calculate_sum_filter(filters=[["paid for", self.USERS[0]], ["paid by", self.USERS[1]]])
        return spending
