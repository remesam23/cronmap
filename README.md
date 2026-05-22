# cronmap

> Visualize your crontab as a weekly schedule in the terminal.

---

## Installation

```bash
pip install cronmap
```

Or install from source:

```bash
git clone https://github.com/yourname/cronmap.git && cd cronmap && pip install .
```

---

## Usage

Pipe your crontab directly into `cronmap`:

```bash
crontab -l | cronmap
```

Or pass a crontab file explicitly:

```bash
cronmap --file /etc/cron.d/myjobs
```

**Example output:**

```
         Mon   Tue   Wed   Thu   Fri   Sat   Sun
00:00     *                       *
06:00     *     *     *     *     *
12:30           *           *
23:00     *     *     *     *     *     *     *
```

### Options

| Flag | Description |
|------|-------------|
| `--file <path>` | Path to a crontab file |
| `--color` | Enable colored output |
| `--compact` | Show only hours with scheduled jobs |
| `--help` | Show help message |

---

## Requirements

- Python 3.8+
- Terminal with UTF-8 support

---

## License

MIT © 2024 yourname