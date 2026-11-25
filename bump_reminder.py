import json
import sys
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox

DEFAULT_INTERVAL_HOURS = 48
DATA_FILE = Path.home() / ".bump-reminder.json"


def format_duration(seconds):
    if seconds < 0:
        seconds = 0
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    if days:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m"


class ReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bump Reminder")
        self.root.geometry("760x480")
        self.items = {}
        self.load()

        title = ttk.Label(root, text="Items to bump", font=("TkDefaultFont", 14, "bold"))
        title.pack(anchor="w", padx=12, pady=(12, 6))

        columns = ("name", "url", "interval", "remaining")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", height=12)
        headings = {
            "name": "Name",
            "url": "URL",
            "interval": "Interval",
            "remaining": "Time left",
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=170 if column != "url" else 300, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=12)

        entry_frame = ttk.Frame(root)
        entry_frame.pack(fill="x", padx=12, pady=10)

        ttk.Label(entry_frame, text="Name:").grid(row=0, column=0, sticky="w")
        self.name_entry = ttk.Entry(entry_frame, width=18)
        self.name_entry.grid(row=0, column=1, padx=(6, 12))

        ttk.Label(entry_frame, text="URL:").grid(row=0, column=2, sticky="w")
        self.url_entry = ttk.Entry(entry_frame, width=38)
        self.url_entry.grid(row=0, column=3, padx=(6, 12))

        ttk.Label(entry_frame, text="Hours:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.interval_entry = ttk.Entry(entry_frame, width=18)
        self.interval_entry.insert(0, str(DEFAULT_INTERVAL_HOURS))
        self.interval_entry.grid(row=1, column=1, padx=(6, 12), pady=(8, 0))

        ttk.Button(entry_frame, text="Add", command=self.add_item).grid(row=1, column=3, sticky="w", pady=(8, 0))

        action_frame = ttk.Frame(root)
        action_frame.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(action_frame, text="Open selected", command=self.open_selected).pack(side="left")
        ttk.Button(action_frame, text="Mark bumped", command=self.mark_bumped).pack(side="left", padx=6)
        ttk.Button(action_frame, text="Remove", command=self.remove_selected).pack(side="left")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.refresh()
        self.tick()

    def load(self):
        if not DATA_FILE.exists():
            return
        try:
            self.items = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self.items = {}

    def save(self):
        DATA_FILE.write_text(json.dumps(self.items, indent=2), encoding="utf-8")

    def add_item(self):
        name = self.name_entry.get().strip()
        url = self.url_entry.get().strip()
        try:
            interval = float(self.interval_entry.get().strip())
        except ValueError:
            messagebox.showerror("Invalid interval", "Enter a number of hours from 0.1 to 48.")
            return
        if not name or not url:
            messagebox.showerror("Missing information", "Enter both a name and a URL.")
            return
        if interval <= 0 or interval > 48:
            messagebox.showerror("Invalid interval", "The reminder interval must be between 0.1 and 48 hours.")
            return

        item_id = str(datetime.now().timestamp())
        due = datetime.now() + timedelta(hours=interval)
        self.items[item_id] = {
            "name": name,
            "url": url,
            "interval_hours": interval,
            "due": due.isoformat(timespec="seconds"),
            "reminded": False,
        }
        self.save()
        self.name_entry.delete(0, tk.END)
        self.url_entry.delete(0, tk.END)
        self.refresh()

    def selected_id(self):
        selected = self.tree.selection()
        if not selected:
            return None
        return selected[0]

    def open_selected(self):
        item_id = self.selected_id()
        if item_id:
            webbrowser.open(self.items[item_id]["url"])

    def mark_bumped(self):
        item_id = self.selected_id()
        if not item_id:
            return
        item = self.items[item_id]
        interval = item["interval_hours"]
        item["due"] = (datetime.now() + timedelta(hours=interval)).isoformat(timespec="seconds")
        item["reminded"] = False
        self.save()
        self.refresh()

    def remove_selected(self):
        item_id = self.selected_id()
        if not item_id:
            return
        if messagebox.askyesno("Remove item", "Remove this item from the reminder list?"):
            del self.items[item_id]
            self.save()
            self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        now = datetime.now()
        for item_id, item in sorted(self.items.items(), key=lambda pair: pair[1]["due"]):
            try:
                due = datetime.fromisoformat(item["due"])
            except (KeyError, TypeError, ValueError):
                due = now
            remaining = due - now
            remaining_text = format_duration(remaining.total_seconds()) if remaining.total_seconds() > 0 else "DUE NOW"
            self.tree.insert("", "end", iid=item_id, values=(
                item["name"],
                item["url"],
                f'{item["interval_hours"]:g} hours',
                remaining_text,
            ))

    def tick(self):
        now = datetime.now()
        changed = False
        for item_id, item in list(self.items.items()):
            try:
                due = datetime.fromisoformat(item["due"])
            except (KeyError, TypeError, ValueError):
                continue
            if now >= due and not item.get("reminded", False):
                item["reminded"] = True
                changed = True
                remaining = max(0, (due - now).total_seconds())
                self.show_popup(item_id, item, remaining)
        if changed:
            self.save()
        self.refresh()
        self.root.after(1000, self.tick)

    def show_popup(self, item_id, item, remaining):
        popup = tk.Toplevel(self.root)
        popup.title("Time to bump")
        popup.attributes("-topmost", True)
        popup.geometry("520x230")

        ttk.Label(popup, text="Time to bump:", font=("TkDefaultFont", 12, "bold")).pack(pady=(15, 4))
        ttk.Label(popup, text=item["name"], font=("TkDefaultFont", 11)).pack()
        ttk.Label(popup, text=item["url"], foreground="blue").pack(pady=6)

        def open_url():
            webbrowser.open(item["url"])

        buttons = ttk.Frame(popup)
        buttons.pack(pady=12)
        ttk.Button(buttons, text="Open", command=open_url).pack(side="left", padx=5)

        def bumped():
            interval = item["interval_hours"]
            item["due"] = (datetime.now() + timedelta(hours=interval)).isoformat(timespec="seconds")
            item["reminded"] = False
            self.save()
            popup.destroy()
            self.refresh()

        ttk.Button(buttons, text="Mark bumped", command=bumped).pack(side="left", padx=5)
        ttk.Button(buttons, text="Snooze 15 min", command=lambda: self.snooze(item_id, item, 15, popup)).pack(side="left", padx=5)

    def snooze(self, item_id, item, minutes, popup):
        item["due"] = (datetime.now() + timedelta(minutes=minutes)).isoformat(timespec="seconds")
        item["reminded"] = False
        self.save()
        popup.destroy()
        self.refresh()

    def on_close(self):
        self.save()
        self.root.destroy()


def main():
    root = tk.Tk()
    ReminderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
