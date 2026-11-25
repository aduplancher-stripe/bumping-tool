# Bump Reminder

A desktop reminder app for Jira issues, Slack conversations, and support cases.

## Features

- Add items with a name, URL, and reminder interval
- Reminder intervals from 0.1 to 48 hours
- Persistent storage in `~/.bump-reminder.json`
- Live countdown for every item
- Pop-up notifications when an item is due
- Open links directly from the app or pop-up
- Mark an item bumped or snooze it by 15 minutes

## Run from source

```bash
python3 -m pip install -r requirements.txt
python3 bump_reminder.py
```

## Build a standalone executable

```bash
python3 build_executable.py
```

The executable is written to `dist/BumpReminder` on macOS/Linux or `dist/BumpReminder.exe` on Windows.

## Example

1. Enter `JIRA-1234` in the Name field.
2. Enter the Jira URL.
3. Leave the interval at `48` hours or enter another value.
4. Select **Add**.
5. When it becomes due, a pop-up appears.
