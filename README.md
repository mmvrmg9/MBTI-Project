# MBTI Crisis Panel Simulation

Five AI agents with different MBTI personality types each nominate a crisis leader from the panel, reasoning in character under a specific crisis scenario. Results are logged to CSV and can be visualised as a bar chart.

## What it does

1. **`agents.py`** — Defines `PersonalityAgent`, all five personality trait profiles, the five crisis `SCENARIOS`, and shared helper functions. Import from here; no simulation runs on import.
2. **`simulate.py`** — Runs the nomination simulation. Prompts for a scenario (or accepts CLI flags), loops through each agent per run, writes one CSV per scenario, and prints a leaderboard summary at the end.
3. **`Nominate_plot.py`** — Reads a results CSV and saves **`nomination_frequency.png`**, a bar chart of how often each person was nominated.

## Panel

| Name   | MBTI  | Focus |
|--------|-------|-------|
| Arthur | ISTJ (Logistician) | Practical, methodical, duty-bound; values structure, honesty, and reliable crisis leadership ([profile](https://www.16personalities.com/istj-personality)) |
| Luna   | ENFP (Campaigner) | Enthusiastic, empathetic free spirit; values connection, morale, and shared vision ([profile](https://www.16personalities.com/enfp-personality)) |
| Victor | ENTJ (Commander) | Bold, decisive natural leader; values strategic vision, rational drive, and achieving ambitious goals ([profile](https://www.16personalities.com/entj-personality)) |
| Mira   | INFJ (Advocate) | Quiet visionary; values integrity, empathy, and being a principled force for good ([profile](https://www.16personalities.com/infj-personality)) |
| Diego  | ESTP (Entrepreneur) | Energetic, perceptive, action-first; reads the room instantly and thrives in fast-moving situations ([profile](https://www.16personalities.com/estp-personality)) |

## Crisis scenarios

| Key | Name | Summary |
|-----|------|---------|
| `financial_collapse` | Financial Collapse | Accounting fraud discovered; stock halt and insolvency risk imminent |
| `pr_disaster` | PR Disaster | Viral video of misconduct; press calling for comment |
| `natural_disaster` | Natural Disaster | Earthquake hits main office; staff safety unknown, systems offline |
| `cyber_attack` | Cyber Attack | Ransomware has encrypted production systems; 24-hour payment deadline |
| `leadership_vacuum` | Leadership Vacuum | CEO and two board members resign; board meeting tomorrow, no succession plan |

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

```powershell
# Interactive scenario menu (prompts you to choose)
python simulate.py

# Run a single named scenario
python simulate.py --scenario cyber_attack

# Run all five scenarios back-to-back
python simulate.py --all

# Override runs or model
python simulate.py --all --runs 20 --model llama3.2

# Plot results for a specific scenario CSV
python Nominate_plot.py
```

You can also set defaults via environment variables:

```powershell
$env:OLLAMA_MODEL = "llama3.2"
$env:NUM_RUNS     = "20"
python simulate.py --all
```

## Output

### `Most Nominated_<scenario_key>.csv`

One file is written per scenario, e.g. `Most Nominated_cyber_attack.csv`.

| Column         | Description |
|----------------|-------------|
| `run`          | Simulation round (1–N) |
| `scenario`     | Scenario key, e.g. `cyber_attack` |
| `nominated`    | Who was nominated, e.g. `Victor (ENTJ)` |
| `nominated_by` | Who made the nomination, e.g. `Arthur (ISTJ)` |
| `answer`       | Full model response including reasoning |

### Terminal leaderboard

At the end of each scenario a ranked tally is printed directly to the terminal, so you can see who "won" without opening the CSV.

### `nomination_frequency.png`

Bar chart of total nominations per panel member, sorted highest to lowest.

## Configuration

| Setting | Default | How to change |
|---------|---------|---------------|
| Model | `llama3` | `--model` flag or `OLLAMA_MODEL` env var |
| Runs per scenario | `10` | `--runs` flag or `NUM_RUNS` env var |
| Delay between calls | 1 second | Edit `time.sleep(1)` in `simulate.py` |
| Add a scenario | — | Append a tuple to `SCENARIOS` in `agents.py` |
| Add an agent | — | Add a trait constant and a `PersonalityAgent` entry in `agents.py` |

## How nominations are parsed

Each agent is instructed to end its reply with:

```
NOMINEE: Victor
```

`parse_nominee()` in `agents.py` reads the last matching line and falls back to a fuzzy name match. If parsing fails, a `[WARN]` is printed and the `nominated` field in the CSV is left blank (the full `answer` is always saved).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Error connecting to Ollama` | Start Ollama (`ollama serve` or the app), then run `ollama list` |
| Model not found | `ollama pull llama3` (or pull the model set in `--model`) |
| `[WARN] Could not parse NOMINEE` | Model ignored the format; check `answer` in the CSV |
| `CSV not found` (plot script) | Run `simulate.py` first to generate a results CSV |
| `Install matplotlib first` | `pip install matplotlib` |

## File overview

```
MBTI Project/
├── agents.py                          # Personality profiles, SCENARIOS, helpers
├── simulate.py                        # Simulation loop (replaces Main.py)
├── Nominate_plot.py                   # Bar chart from CSV
├── Most Nominated_<scenario>.csv      # Generated results (one per scenario)
├── nomination_frequency.png           # Generated chart
└── README.md
```
