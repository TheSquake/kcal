# kcal

Non-interactive CLI for managing local iCalendar (`.ics`) files. Designed for scripting and AI agent integration — no GUI, no server, just direct `.ics` file manipulation.

## Install

```
pip install kcal-cli
```

Or with uv:

```
uv tool install kcal-cli
```

## Usage

All commands require `-f <path>` pointing to your `.ics` file.

### List events

```
kcal -f ~/calendar.ics list
kcal -f ~/calendar.ics list --date 2026-06-25
```

### Add a timed event

```
kcal -f ~/calendar.ics add "Meeting" -s "2026-06-26 09:00" -e "2026-06-26 10:00"
```

### Add an all-day event

```
kcal -f ~/calendar.ics add "Holiday" -s "2026-07-04" --allday
```

For multi-day events, set `--end` to the day after the last day (iCal convention):

```
kcal -f ~/calendar.ics add "Conference" -s "2026-08-01" -e "2026-08-04" --allday
```

### Edit an event

```
kcal -f ~/calendar.ics edit 1cc4704e --summary "New title"
kcal -f ~/calendar.ics edit 1cc4704e --start "2026-06-26 10:00" --end "2026-06-26 11:00"
kcal -f ~/calendar.ics edit 1cc4704e --start "2026-06-26" --allday
```

### Delete an event

```
kcal -f ~/calendar.ics delete 1cc4704e
```

UID prefix matching — only the first few characters of the event UID are needed.

## Options

| Flag | Description |
|------|-------------|
| `-f`, `--file` | Path to `.ics` file (required) |
| `-s`, `--start` | Start date/time (`YYYY-MM-DD HH:MM` or `YYYY-MM-DD`) |
| `-e`, `--end` | End date/time (optional for all-day events) |
| `--allday` | Create/convert to all-day event (uses `VALUE=DATE`) |
| `-d`, `--description` | Event description |
| `-l`, `--location` | Event location |

## Notes

- Creates the `.ics` file if it doesn't exist
- All-day events use proper `VALUE=DATE` entries (not midnight-to-midnight)
- Works with KOrganizer, GNOME Calendar, Thunderbird, or any iCal-compatible app
- If your calendar app is open, you may need to refresh to see changes

## License

MIT
# kcal
