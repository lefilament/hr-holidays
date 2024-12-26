# Copyright 2016-2019 Onestein (<https://www.onestein.eu>)
# Copyright 2024- Le Filament (https://le-filament.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

import odoo.tests.common as common
from odoo.exceptions import UserError, ValidationError


class TestHolidaysLeaveRepeated(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.date_start = date(2016, 12, 5)
        cls.date_end = date(2016, 12, 5)

        cls.calendar = cls.env["resource.calendar"].create({"name": "Calendar 1"})

        for i in range(0, 7):
            cls.env["resource.calendar.attendance"].create(
                {
                    "name": "Day " + str(i),
                    "dayofweek": str(i),
                    "hour_from": 8.0,
                    "hour_to": 16.0,
                    "calendar_id": cls.calendar.id,
                }
            )

        cls.employee_1 = cls.env["hr.employee"].create(
            {"name": "Employee 1", "resource_calendar_id": cls.calendar.id}
        )
        cls.employee_2 = cls.env["hr.employee"].create(
            {"name": "Employee 2", "resource_calendar_id": cls.calendar.id}
        )
        cls.employee_3 = cls.env["hr.employee"].create(
            {"name": "Employee 3", "resource_calendar_id": cls.calendar.id}
        )
        cls.employee_4 = cls.env["hr.employee"].create(
            {"name": "Employee 4", "resource_calendar_id": cls.calendar.id}
        )
        cls.employee_5 = cls.env["hr.employee"].create(
            {"name": "Failing Employee", "resource_calendar_id": cls.calendar.id}
        )

        cls.status_1 = cls.env["hr.leave.type"].create(
            {"name": "Repeating Status", "repeat": True}
        )

        cls.leave_1 = cls.env["hr.leave"].create(
            {
                "holiday_status_id": cls.status_1.id,
                "holiday_type": "employee",
                "repeat_every": "workday",
                "repeat_mode": "times",
                "repeat_limit": 5,
                "request_date_from": cls.date_start,
                "request_date_to": cls.date_end,
                "employee_id": cls.employee_1.id,
            }
        )
        cls.leave_2 = cls.env["hr.leave"].create(
            {
                "holiday_status_id": cls.status_1.id,
                "holiday_type": "employee",
                "repeat_every": "week",
                "repeat_mode": "times",
                "repeat_limit": 4,
                "request_date_from": cls.date_start,
                "request_date_to": cls.date_end,
                "employee_id": cls.employee_2.id,
            }
        )
        cls.leave_3 = cls.env["hr.leave"].create(
            {
                "holiday_status_id": cls.status_1.id,
                "holiday_type": "employee",
                "repeat_every": "biweek",
                "repeat_mode": "times",
                "repeat_limit": 3,
                "request_date_from": cls.date_start,
                "request_date_to": cls.date_end,
                "employee_id": cls.employee_3.id,
            }
        )
        cls.leave_4 = cls.env["hr.leave"].create(
            {
                "holiday_status_id": cls.status_1.id,
                "holiday_type": "employee",
                "repeat_every": "month",
                "repeat_mode": "times",
                "repeat_limit": 2,
                "request_date_from": cls.date_start,
                "request_date_to": cls.date_end,
                "employee_id": cls.employee_4.id,
            }
        )

    def test_01_count_repetitions(self):
        leave_1_list = self.env["hr.leave"].search(
            [
                ("holiday_status_id", "=", self.status_1.id),
                ("employee_id", "=", self.employee_1.id),
            ]
        )
        leave_2_list = self.env["hr.leave"].search(
            [
                ("holiday_status_id", "=", self.status_1.id),
                ("employee_id", "=", self.employee_2.id),
            ]
        )
        leave_3_list = self.env["hr.leave"].search(
            [
                ("holiday_status_id", "=", self.status_1.id),
                ("employee_id", "=", self.employee_3.id),
            ]
        )
        leave_4_list = self.env["hr.leave"].search(
            [
                ("holiday_status_id", "=", self.status_1.id),
                ("employee_id", "=", self.employee_4.id),
            ]
        )

        self.assertEqual(len(leave_1_list), 5)
        self.assertEqual(len(leave_2_list), 4)
        self.assertEqual(len(leave_3_list), 3)
        self.assertEqual(len(leave_4_list), 2)

    def test_02_workdays(self):
        for i in range(0, 5):
            check_from = self.date_start + timedelta(days=i)
            check_to = self.date_end + timedelta(days=i)
            leaves = self.env["hr.leave"].search(
                [
                    ("holiday_status_id", "=", self.status_1.id),
                    ("employee_id", "=", self.employee_1.id),
                    ("request_date_from", "=", check_from),
                    ("request_date_to", "=", check_to),
                ]
            )
            self.assertEqual(len(leaves), 1)

    def test_03_weeks(self):
        for i in range(0, 4):
            check_from = self.date_start + timedelta(days=i * 7)
            check_to = self.date_end + timedelta(days=i * 7)
            leaves = self.env["hr.leave"].search(
                [
                    ("holiday_status_id", "=", self.status_1.id),
                    ("employee_id", "=", self.employee_2.id),
                    ("request_date_from", "=", check_from),
                    ("request_date_to", "=", check_to),
                ]
            )
            self.assertEqual(len(leaves), 1)

    def test_04_biweeks(self):
        for i in range(0, 3):
            check_from = self.date_start + timedelta(days=i * 14)
            check_to = self.date_end + timedelta(days=i * 14)
            leaves = self.env["hr.leave"].search(
                [
                    ("holiday_status_id", "=", self.status_1.id),
                    ("employee_id", "=", self.employee_3.id),
                    ("request_date_from", "=", check_from),
                    ("request_date_to", "=", check_to),
                ]
            )
            self.assertEqual(len(leaves), 1)

    def test_05_months(self):
        for i in range(0, 2):
            check_from = self.date_start + timedelta(days=i * 28)
            check_to = self.date_end + timedelta(days=i * 28)
            leaves = self.env["hr.leave"].search(
                [
                    ("holiday_status_id", "=", self.status_1.id),
                    ("employee_id", "=", self.employee_4.id),
                    ("request_date_from", "=", check_from),
                    ("request_date_to", "=", check_to),
                ]
            )
            self.assertEqual(len(leaves), 1)

    def test_06_check_dates(self):
        with self.assertRaises(ValidationError):
            self.env["hr.leave"].create(
                {
                    "holiday_status_id": self.status_1.id,
                    "holiday_type": "employee",
                    "repeat_every": "workday",
                    "repeat_limit": -1,
                    "request_date_from": self.date_start,
                    "request_date_to": self.date_end,
                    "employee_id": self.employee_5.id,
                }
            )

    def test_07_check_dates(self):
        date_start = date(2019, 2, 18)
        date_end = date(2019, 2, 20)
        with self.assertRaises(UserError):
            self.env["hr.leave"].create(
                {
                    "holiday_status_id": self.status_1.id,
                    "holiday_type": "employee",
                    "repeat_every": "workday",
                    "repeat_mode": "times",
                    "repeat_limit": 5,
                    "request_date_from": date_start,
                    "request_date_to": date_end,
                    "employee_id": self.employee_5.id,
                }
            )

    def test_08_workdays_with_weekend(self):
        date_start = date(2019, 3, 1)
        date_end = date(2019, 3, 1)
        self.env["hr.leave"].create(
            {
                "holiday_status_id": self.status_1.id,
                "holiday_type": "employee",
                "repeat_every": "workday",
                "repeat_mode": "times",
                "repeat_limit": 5,
                "request_date_from": date_start,
                "request_date_to": date_end,
                "employee_id": self.employee_1.id,
            }
        )
        for i in range(0, 7):
            datetime_from = date_start + timedelta(days=i)
            datetime_to = date_end + timedelta(days=i)
            leaves = self.env["hr.leave"].search(
                [
                    ("holiday_status_id", "=", self.status_1.id),
                    ("employee_id", "=", self.employee_1.id),
                    ("request_date_from", "=", datetime_from),
                    ("request_date_to", "=", datetime_to),
                ]
            )
            if datetime_from.weekday() < 5:  # is a weekday
                self.assertEqual(len(leaves), 1)
            else:  # is weekend
                self.assertEqual(len(leaves), 0)

    def test_09_check_repeat_end_date(self):
        old_date = date(2019, 3, 18)
        date_start = date(2019, 2, 18)
        date_end = date(2019, 2, 18)
        with self.assertRaises(ValidationError):
            self.env["hr.leave"].create(
                {
                    "holiday_status_id": self.status_1.id,
                    "holiday_type": "employee",
                    "repeat_every": "workday",
                    "repeat_mode": "date",
                    "repeat_end_date": old_date,
                    "request_date_from": date_start,
                    "request_date_to": date_end,
                    "employee_id": self.employee_5.id,
                }
            )

    def test_10_check_different_resource_calendar(self):
        with self.assertRaises(ValidationError):
            calendar2 = self.env["resource.calendar"].create({"name": "Calendar 2"})
            employee_a = self.env["hr.employee"].create(
                {"name": "Employee 8", "resource_calendar_id": self.calendar.id}
            )
            employee_b = self.env["hr.employee"].create(
                {
                    "name": "Employee 9 - different calendar",
                    "resource_calendar_id": calendar2.id,
                }
            )
            self.env["hr.leave"].create(
                {
                    "holiday_status_id": self.status_1.id,
                    "holiday_type": "employee",
                    "repeat_every": "workday",
                    "repeat_mode": "times",
                    "repeat_limit": 5,
                    "request_date_from": self.date_start,
                    "request_date_to": self.date_end,
                    "multi_employee": True,
                    "employee_ids": [(6, False, [employee_a.id, employee_b.id])],
                }
            )

    def test_11_check_no_resource_calendar(self):
        with self.assertRaises(ValidationError):
            employee = self.env["hr.employee"].create(
                {
                    "name": "Employee 10 - no calendar",
                    "resource_calendar_id": False,
                }
            )
            self.env["hr.leave"].create(
                {
                    "holiday_status_id": self.status_1.id,
                    "holiday_type": "employee",
                    "repeat_every": "workday",
                    "repeat_mode": "times",
                    "repeat_limit": 5,
                    "request_date_from": self.date_start,
                    "request_date_to": self.date_end,
                    "multi_employee": True,
                    "employee_id": employee.id,
                }
            )

    def test_12_count_repetitions_multi_employees(self):
        employee_a = self.env["hr.employee"].create(
            {"name": "Employee 6", "resource_calendar_id": self.calendar.id}
        )
        employee_b = self.env["hr.employee"].create(
            {"name": "Employee 7", "resource_calendar_id": self.calendar.id}
        )
        status = self.env["hr.leave.type"].create(
            {
                "name": "Repeating Status - No Allocation",
                "repeat": True,
                "requires_allocation": "no",
            }
        )
        self.env["hr.leave"].create(
            {
                "holiday_status_id": status.id,
                "holiday_type": "employee",
                "repeat_every": "workday",
                "repeat_mode": "times",
                "repeat_limit": 5,
                "request_date_from": self.date_start,
                "request_date_to": self.date_end,
                "employee_id": employee_a.id,
                "employee_ids": [(6, False, [employee_a.id, employee_b.id])],
            }
        )
        leave_list = self.env["hr.leave"].search(
            [
                ("holiday_status_id", "=", status.id),
                ("employee_ids", "in", [employee_a.id, employee_b.id]),
            ]
        )
        self.assertEqual(len(leave_list), 5)
