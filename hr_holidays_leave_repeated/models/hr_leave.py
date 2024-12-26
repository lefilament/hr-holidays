# Copyright 2016-2019 Onestein (<https://www.onestein.eu>)
# Copyright 2024- Le Filament (https://le-filament.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta
from pytz import utc

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrLeave(models.Model):
    _inherit = "hr.leave"

    repeat_every = fields.Selection(
        [
            ("workday", "Every workday"),
            ("week", "Every week"),
            ("biweek", "Every two weeks"),
            ("month", "Every four weeks"),
        ]
    )
    repeat_mode = fields.Selection(
        [("times", "Number of Times"), ("date", "End Date")], default="times"
    )
    holiday_type_repeat = fields.Boolean(related="holiday_status_id.repeat")
    repeat_limit = fields.Integer(default=1, string="Repeat # times")
    repeat_end_date = fields.Date(default=lambda self: fields.Date.today())

    @api.model
    def _update_repeated_workday_dates(self, resource_calendar, from_dt, to_dt, days):
        user = self.env.user
        from_dt = fields.Datetime.context_timestamp(user, from_dt)
        to_dt = fields.Datetime.context_timestamp(user, to_dt)
        work_hours = resource_calendar.get_work_hours_count(
            from_dt, to_dt, compute_leaves=False
        )
        while work_hours:
            from_dt = from_dt + relativedelta(days=days)
            to_dt = to_dt + relativedelta(days=days)

            new_work_hours = resource_calendar.get_work_hours_count(
                from_dt, to_dt, compute_leaves=True
            )
            if new_work_hours and work_hours <= new_work_hours:
                break

        return from_dt.astimezone(utc).replace(tzinfo=None), to_dt.astimezone(
            utc
        ).replace(tzinfo=None)

    @api.model
    def _get_repeated_vals_dict(self):
        return {
            "workday": {
                "days": 1,
                "user_error_msg": _(
                    "The repetition is based on workdays: the duration of "
                    "the leave request must not exceed 1 day."
                ),
            },
            "week": {
                "days": 7,
                "user_error_msg": _(
                    "The repetition is every week: the duration of the "
                    "leave request must not exceed 1 week."
                ),
            },
            "biweek": {
                "days": 14,
                "user_error_msg": _(
                    "The repetition is every two weeks: the duration of the "
                    "leave request must not exceed 2 weeks."
                ),
            },
            "month": {
                "days": 28,
                "user_error_msg": _(
                    "The repetition is every four weeks: the duration of the "
                    "leave request must not exceed 28 days."
                ),
            },
        }

    @api.model
    def _update_repeated_leave_vals(self, leave, resource_calendar):
        vals_dict = self._get_repeated_vals_dict()
        param_dict = vals_dict[leave.repeat_every]
        from_dt = fields.Datetime.from_string(leave.date_from)
        to_dt = fields.Datetime.from_string(leave.date_to)

        if (to_dt - from_dt).days > param_dict["days"]:
            raise UserError(param_dict["user_error_msg"])

        from_dt, to_dt = self._update_repeated_workday_dates(
            resource_calendar, from_dt, to_dt, param_dict["days"]
        )

        return {
            "employee_ids": [(6, 0, leave.employee_ids.ids)],
            "date_from": from_dt,
            "date_to": to_dt,
            "multi_employee": leave.multi_employee,
        }

    @api.model
    def create_repeated_handler(self, leave, resource_calendar):
        def _check_repeating(count, leave):
            repeat_mode = leave.repeat_mode
            if repeat_mode == "times" and count < leave.repeat_limit:
                return True
            repeat_end_date = leave.repeat_end_date
            if repeat_mode == "date" and leave.date_to <= repeat_end_date:
                return True
            return False

        count = 1
        vals = self._update_repeated_leave_vals(leave, resource_calendar)
        while _check_repeating(count, leave):
            leave = leave.with_context(skip_create_handler=True).copy(vals)
            count += 1
            vals = self._update_repeated_leave_vals(leave, resource_calendar)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        skip_create_handler = self.env.context.get("skip_create_handler")
        if skip_create_handler:
            return res
        for leave in res.filtered(
            lambda leave: leave.repeat_every
            and leave.repeat_mode
            and leave.holiday_type == "employee"
        ):
            employees = leave.employee_ids
            resource_calendars = employees.mapped("resource_calendar_id")
            if len(resource_calendars) == 1:
                self.create_repeated_handler(leave, resource_calendars[0])
            elif len(resource_calendars) == 0:
                raise ValidationError(
                    _(
                        "Please define resource calendar on employee(s) in order "
                        "to compute repeated leaves."
                    )
                )
            else:
                raise ValidationError(
                    _(
                        "Creating leaves for multiple employees with different "
                        "resource calendar is not supported."
                    )
                )
        return res

    @api.constrains("repeat_mode", "repeat_limit", "repeat_end_date")
    def _check_repeat_limit(self):
        for record in self:
            if record.repeat_mode == "times" and record.repeat_limit < 0:
                raise ValidationError(_("Please set a positive amount of repetitions."))
            if (
                record.repeat_mode == "date"
                and record.repeat_end_date < fields.Date.today()
            ):
                raise ValidationError(_("The Repeat End Date cannot be in the past"))
