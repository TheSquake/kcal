#!/usr/bin/env python3
"""kcal - non-interactive CLI for managing a single .ics calendar file."""

import argparse
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

from icalendar import Calendar, Event


def load_calendar(path: Path) -> Calendar:
    if path.exists():
        return Calendar.from_ical(path.read_bytes())
    cal = Calendar()
    cal.add("prodid", "-//kcal//EN")
    cal.add("version", "2.0")
    return cal


def save_calendar(cal: Calendar, path: Path):
    path.write_bytes(cal.to_ical())


def parse_dt(s: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {s!r}")


def parse_date(s: str) -> date:
    for fmt in ("%Y-%m-%d",):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {s!r}")


def cmd_add(args):
    cal = load_calendar(args.file)
    event = Event()
    event.add("uid", str(uuid.uuid4()))
    event.add("summary", args.summary)
    if args.allday:
        start_date = parse_date(args.start)
        event.add("dtstart", start_date)
        if args.end:
            end_date = parse_date(args.end)
        else:
            from datetime import timedelta
            end_date = start_date + timedelta(days=1)
        event.add("dtend", end_date)
    else:
        event.add("dtstart", parse_dt(args.start))
        event.add("dtend", parse_dt(args.end))
    if args.description:
        event.add("description", args.description)
    if args.location:
        event.add("location", args.location)
    cal.add_component(event)
    save_calendar(cal, args.file)
    print(f"Added: {args.summary} (uid: {event['uid']})")


def cmd_list(args):
    cal = load_calendar(args.file)
    events = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        dtstart = component.get("dtstart")
        if dtstart:
            dtstart = dtstart.dt
        events.append((dtstart, component))

    if args.date:
        target = parse_dt(args.date).date()
        filtered = []
        for dt, e in events:
            if dt is None:
                continue
            if isinstance(dt, datetime):
                if dt.date() == target:
                    filtered.append((dt, e))
            elif isinstance(dt, date):
                if dt == target:
                    filtered.append((dt, e))
        events = filtered

    def sort_key(x):
        dt = x[0]
        if dt is None:
            return (0, datetime.min)
        if isinstance(dt, datetime):
            return (1, dt.replace(tzinfo=None) if dt.tzinfo else dt)
        if isinstance(dt, date):
            return (1, datetime(dt.year, dt.month, dt.day))
        return (0, datetime.min)

    events.sort(key=sort_key)

    if not events:
        print("No events found.")
        return

    for dt, e in events:
        uid = str(e.get("uid", "???"))
        summary = str(e.get("summary", "(no title)"))
        is_allday = isinstance(dt, date) and not isinstance(dt, datetime)
        if is_allday:
            start = dt.strftime("%Y-%m-%d") + " (all day)"
            end = ""
        else:
            start = dt.strftime("%Y-%m-%d %H:%M")
            dtend = e.get("dtend")
            end = " - " + dtend.dt.strftime("%H:%M") if dtend else ""
        print(f"  {start}{end}  {summary}  [uid: {uid[:8]}...]")


def cmd_delete(args):
    cal = load_calendar(args.file)
    new_cal = Calendar()
    for k, v in cal.items():
        new_cal.add(k, v)

    found = False
    for component in cal.walk():
        if component.name == "VEVENT":
            uid = str(component.get("uid", ""))
            if uid.startswith(args.uid) or uid == args.uid:
                found = True
                continue
        if component.name != "VCALENDAR":
            new_cal.add_component(component)

    if not found:
        print(f"No event with uid starting with {args.uid!r}", file=sys.stderr)
        sys.exit(1)

    save_calendar(new_cal, args.file)
    print(f"Deleted event {args.uid}")


def cmd_edit(args):
    cal = load_calendar(args.file)
    found = False
    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        uid = str(component.get("uid", ""))
        if not (uid.startswith(args.uid) or uid == args.uid):
            continue
        found = True
        if args.summary:
            del component["summary"]
            component.add("summary", args.summary)
        if args.allday:
            if "dtstart" in component:
                del component["dtstart"]
            if "dtend" in component:
                del component["dtend"]
            start_date = parse_date(args.start) if args.start else None
            if start_date:
                component.add("dtstart", start_date)
                from datetime import timedelta
                end_date = parse_date(args.end) if args.end else start_date + timedelta(days=1)
                component.add("dtend", end_date)
        else:
            if args.start:
                del component["dtstart"]
                component.add("dtstart", parse_dt(args.start))
            if args.end:
                del component["dtend"]
                component.add("dtend", parse_dt(args.end))
        if args.description:
            if "description" in component:
                del component["description"]
            component.add("description", args.description)
        if args.location:
            if "location" in component:
                del component["location"]
            component.add("location", args.location)
        break

    if not found:
        print(f"No event with uid starting with {args.uid!r}", file=sys.stderr)
        sys.exit(1)

    save_calendar(cal, args.file)
    print(f"Updated event {args.uid}")


def main():
    parser = argparse.ArgumentParser(prog="kcal", description="Manage a .ics calendar file")
    parser.add_argument("--file", "-f", type=Path, required=True, help="Path to .ics file")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add an event")
    p_add.add_argument("summary", help="Event title")
    p_add.add_argument("--start", "-s", required=True, help="Start date/time (YYYY-MM-DD HH:MM, or YYYY-MM-DD for all-day)")
    p_add.add_argument("--end", "-e", help="End date/time (optional for all-day events)")
    p_add.add_argument("--allday", action="store_true", help="Create an all-day event (uses DATE values)")
    p_add.add_argument("--description", "-d", help="Description")
    p_add.add_argument("--location", "-l", help="Location")

    p_list = sub.add_parser("list", help="List events")
    p_list.add_argument("--date", help="Filter by date (YYYY-MM-DD)")

    p_del = sub.add_parser("delete", help="Delete an event by UID (prefix match)")
    p_del.add_argument("uid", help="UID or UID prefix")

    p_edit = sub.add_parser("edit", help="Edit an event by UID")
    p_edit.add_argument("uid", help="UID or UID prefix")
    p_edit.add_argument("--summary", help="New title")
    p_edit.add_argument("--start", "-s", help="New start date/time")
    p_edit.add_argument("--end", "-e", help="New end date/time")
    p_edit.add_argument("--allday", action="store_true", help="Convert to an all-day event")
    p_edit.add_argument("--description", "-d", help="New description")
    p_edit.add_argument("--location", "-l", help="New location")

    args = parser.parse_args()
    if args.command == "add" and not args.allday and not args.end:
        parser.error("--end is required for non-allday events")
    {"add": cmd_add, "list": cmd_list, "delete": cmd_delete, "edit": cmd_edit}[args.command](args)


if __name__ == "__main__":
    main()
