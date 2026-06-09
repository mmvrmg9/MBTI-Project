# MBTI Crisis Panel Simulation

Five AI agents with different MBTI personality types each nominate a crisis leader from the panel. Results are logged to CSV and can be visualized as a bar chart.

## What it does

1. **`Main.py`** — Runs a simulation where each agent (in character) nominates one other panel member as crisis leader. Each agent gets an isolated prompt turn via Ollama. Outputs **`Most Nominated.csv`**.
2. **`Nominate_plot.py`** — Reads the CSV and saves **`nomination_frequency.png`**, a bar chart of how often each person was nominated.

## Panel

| Name   | MBTI  | Focus |
|--------|-------|-------|
| Arthur | ISTJ (Logistician) | Practical, methodical, duty-bound; values structure, honesty, and reliable crisis leadership ([profile](https://www.16personalities.com/istj-personality)) |
| Luna   | ENFP (Campaigner) | Enthusiastic, empathetic free spirit; values connection, morale, and shared vision ([profile](https://www.16personalities.com/enfp-personality)) |
| Victor | ENTJ  | Market dominance, ROI, growth |
| Mira   | INFJ  | Ethics, long-term alignment, human cost |
| Diego  | ESTP  | Negotiation, reading the room, practical fixes |

## Requirements

- **Python 3.10+**
- **[Ollama](https://ollama.com)** running locally with the `llama3` model (or another model you configure)

### Install Python packages

```powershell
pip install ollama matplotlib
```

### Set up Ollama

1. Install and start Ollama (open the Ollama app or run `ollama serve`).
2. Pull the model:

```powershell
ollama pull llama3
```

3. Confirm it is available:

```powershell
ollama list
```

## Usage

Run from this folder (`MBTI Project`):

```powershell
# 1. Run the simulation (writes Most Nominated.csv)
python Main.py

# 2. Plot nomination counts (writes nomination_frequency.png)
python Nominate_plot.py
```

In Cursor/VS Code you can also right-click either file and choose **Run Python File**.

## Output

### `Most Nominated.csv`

| Column         | Description |
|----------------|-------------|
| `run`          | Simulation round (1–10 by default) |
| `nominated`    | Who was nominated, e.g. `Victor (ENTJ)` |
| `nominated_by` | Who made the nomination |
| `answer`       | Full model response |

### `nomination_frequency.png`

Bar chart of total nominations per panel member, sorted highest to lowest.

## Configuration

In **`Main.py`**:

| Setting        | Default   | How to change |
|----------------|-----------|---------------|
| Model          | `llama3`  | Set env var `OLLAMA_MODEL` or edit `OLLAMA_MODEL` in the script |
| Number of runs | `10`      | Change `NUM_RUNS` |
| Delay between calls | `1` second | Edit `time.sleep(1)` in the loop |

Example — use a different Ollama model:

```powershell
$env:OLLAMA_MODEL = "llama3.2"
python Main.py
```

## How nominations are parsed

Each agent is asked to end their reply with a line like:

```
NOMINEE: Victor
```

The script reads that line to fill the `nominated` column. If parsing fails, you will see a warning and that row’s `nominated` field stays blank (the full `answer` is still saved).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Error connecting to Ollama` | Start Ollama (`ollama serve` or the Ollama app), then run `ollama list` |
| Model not found | Run `ollama pull llama3` (or pull the model set in `OLLAMA_MODEL`) |
| `[WARN] Could not parse NOMINEE: line` | Model did not follow the format; check `answer` in the CSV |
| `CSV not found` (plot script) | Run `Main.py` first to generate `Most Nominated.csv` |
| `Install matplotlib first` | Run `pip install matplotlib` |

## File overview

```
MBTI Project/
├── Main.py                  # Simulation (Ollama)
├── Nominate_plot.py         # Bar chart from CSV
├── Most Nominated.csv       # Generated results
├── nomination_frequency.png # Generated chart
└── README.md
```
