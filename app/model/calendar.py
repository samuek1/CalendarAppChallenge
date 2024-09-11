from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import List, Dict, Optional
from app.services.util import generate_unique_id, reminder_not_found_error, slot_not_available_error, \
    date_lower_than_today_error, event_not_found_error

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Reminder:
    EMAIL = 'email'
    SYSTEM = 'system'

    date_time: datetime
    type: str = EMAIL

    def __str__(self) -> str:
        return f"Reminder on {self.date_time} of type {self.type}"



from dataclasses import dataclass, field
from datetime import date, time
from app.services.util import generate_unique_id, reminder_not_found_error

@dataclass
class Event:
    title: str
    description: str
    date_: date
    start_at: time
    end_at: time
    id: str = field(default_factory=generate_unique_id)
    reminders: list[Reminder] = field(default_factory=list)

    def add_reminder(self, date_time: datetime, type_: str = Reminder.EMAIL):
        reminder = Reminder(date_time=date_time, type=type_)
        self.reminders.append(reminder)

    def delete_reminder(self, reminder_index: int):
        if 0 <= reminder_index < len(self.reminders):
            self.reminders.pop(reminder_index)
        else:
            reminder_not_found_error()

    def __str__(self) -> str:
        return f"ID: {self.id}\nEvent title: {self.title}\nDescription: {self.description}\nTime: {self.start_at} - {self.end_at}"


from datetime import time
from app.services.util import slot_not_available_error, event_not_found_error

class Day:
    def __init__(self, date_):
        self.date_ = date_
        self.slots = {}
        self._init_slots()

    def _init_slots(self):
        # Inicializa slots con intervalos de 15 minutos.
        for hour in range(24):
            for minute in range(0, 60, 15):
                self.slots[time(hour, minute)] = None

    def add_event(self, event_id: str, start_at: time, end_at: time):
        for slot_time in self.slots:
            if start_at <= slot_time < end_at:
                if self.slots[slot_time] is not None:
                    slot_not_available_error()
                self.slots[slot_time] = event_id

    def delete_event(self, event_id: str):
        deleted = False
        for slot, saved_id in self.slots.items():
            if saved_id == event_id:
                self.slots[slot] = None
                deleted = True
        if not deleted:
            event_not_found_error()

    def update_event(self, event_id: str, start_at: time, end_at: time):
        for slot in self.slots:
            if self.slots[slot] == event_id:
                self.slots[slot] = None

        for slot in self.slots:
            if start_at <= slot < end_at:
                if self.slots[slot]:
                    slot_not_available_error()
                else:
                    self.slots[slot] = event_id


from datetime import date, time, datetime
from app.services.util import event_not_found_error, date_lower_than_today_error


class Calendar:
    def __init__(self):
        self.days = {}
        self.events = {}

    def add_event(self, title: str, description: str, date_: date, start_at: time, end_at: time) -> str:
        if date_ < datetime.now().date():
            date_lower_than_today_error()

        if date_ not in self.days:
            self.days[date_] = Day(date_)

        event = Event(title=title, description=description, date_=date_, start_at=start_at, end_at=end_at)
        self.days[date_].add_event(event.id, start_at, end_at)
        self.events[event.id] = event
        return event.id

    def update_event(self, event_id: str, title: str, description: str, date_: date, start_at: time, end_at: time):
        event = self.events.get(event_id)
        if not event:
            event_not_found_error()

        is_new_date = False
        if event.date_ != date_:
            self.delete_event(event_id)
            event = Event(title=title, description=description, date_=date_, start_at=start_at, end_at=end_at)
            event.id = event_id
            self.events[event_id] = event
            is_new_date = True
            if date_ not in self.days:
                self.days[date_] = Day(date_)
            self.days[date_].add_event(event_id, start_at, end_at)
        else:
            event.title = title
            event.description = description
            event.start_at = start_at
            event.end_at = end_at

        for day in self.days.values():
            if not is_new_date and event_id in day.slots.values():
                day.delete_event(event.id)
                day.update_event(event.id, start_at, end_at)

    def delete_event(self, event_id: str):
        if event_id not in self.events:
            event_not_found_error()

        event = self.events.pop(event_id)
        for day in self.days.values():
            if event_id in day.slots.values():
                day.delete_event(event_id)
                break

    def find_events(self, start_at: date, end_at: date) -> dict[date, list[Event]]:
        events = {}
        for event in self.events.values():
            if start_at <= event.date_ <= end_at:
                if event.date_ not in events:
                    events[event.date_] = []
                events[event.date_].append(event)
        return events

    def add_reminder(self, event_id: str, date_time: datetime, type_: str = Reminder.EMAIL):
        event = self.events.get(event_id)
        if not event:
            event_not_found_error()

        event.add_reminder(date_time, type_)

    def delete_reminder(self, event_id: str, reminder_index: int):
        event = self.events.get(event_id)
        if not event:
            event_not_found_error()

        event.delete_reminder(reminder_index)

    def list_reminders(self, event_id: str) -> list[Reminder]:
        event = self.events.get(event_id)
        if not event:
            event_not_found_error()

        return event.reminders

    def find_available_slots(self, date_: date) -> list[time]:
        if date_ not in self.days:
            return [time(hour, minute) for hour in range(24) for minute in range(0, 60, 15)]

        day = self.days[date_]
        return [slot for slot, event_id in day.slots.items() if event_id is None]
