# financeTracker

> Keep your money data **local** and get the insights you actually care about without battling spreadsheets.

I built this because I wanted a “just‑drag‑in‑your‑bank‑CSV” app that *doesn’t* ask for API keys or a subscription AND the data is stored locally.  

---

## Quickstart

```bash
git clone https://github.com/HamzyP/finance-tracker.git
cd finance-tracker
python main.py      # needs Python 3.10+ and Tk installed
```

*Linux users*: `sudo apt install python3-tk` if you don’t already have Tkinter.

---

## How It Works (30‑second version)

1. **Load CSVs** – Point at your exported statements (multiple files? cool).  
2. **Auto‑categorise** – It gets the store name from your bank’s “Description” field and adds on a category.  
3. **Tweak** – Unknown stores land in the *Add Categories* tab. Two clicks and they’re filed forever.  
4. **Ignore** – Hide boring stuff (salary transfers, CC payments) with the *Manage Ignore List* dialog.  
5. **Explore** – Flip between Summary, Analysis, Details. Double‑click anything to drill down.  
6. **Export** – One button → CSV summary.

All the data lives in CSVs right next to the app in the same folder. No cloud, no database.

---

## What You’ll See

| Tab               | Why It Exists                                               |
|-------------------|-------------------------------------------------------------|
| **Summary**       | Month‑by‑month income, spending, and net.                   |
| **Analysis**      | Trend read‑out + Year / Month / Total buttons.         |
| **Details**       | Raw transactions, filterable + bulk recategorise.           |
| **Add Categories**| Left: un‑grouped stores. Right: your categories.            |
| **View Categories**| Totals, counts, averages — nerd stuff at a glance.         |
| **Settings**      | Font choice, size, Light/Dark. Minimal, but it’s there.     |

---

## File Dump

```
finance-tracker/
├── main.py        # giant Tkinter GUI
├── config.py      # fonts, theme colours, etc.
├── categories.csv # store → category (auto‑written)
├── ignore.csv     # transactions you hid
└── *.csv          # your bank statements
```

---

## Customising (if you’re that person)

Open `config.py` and tweak the `settings` dict — font, theme, heading size.  
Colours live in `theme_settings`. Go nuts.

---

## Roadmap / Pie‑in‑the‑sky

- Export CSV so you can put it in a formatted excel sheet
- Graphs (matplotlib) — bar, line, donut: the whole bakery  
- Budget goals + “you’re over by £X” nags  
- OFX / QIF / JSON import  
- Unit tests + GitHub Actions

PRs welcome. Or fork and do your own thing — it’s your money.

---

### Built With

- Python 3 (stdlib only)
- Tkinter / ttk
