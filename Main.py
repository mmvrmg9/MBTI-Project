import csv
import os
import re
import time

import ollama

# Match a tag from `ollama list` on your machine (e.g. llama3.2, llama3.1:8b).
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

def _extract_reply_text(response) -> tuple[str | None, str | None]:
    """
    Read assistant text from an Ollama chat response (dict or ChatResponse).

    Some reasoning models put text in `thinking` and leave `content` empty;
    we use `thinking` only as a fallback when `content` is blank.

    Returns:
        (text, None) on success, or (None, error_message) if nothing usable.
    """
    msg = None
    if isinstance(response, dict):
        msg = response.get("message")
    elif hasattr(response, "get"):
        msg = response.get("message")
    else:
        msg = getattr(response, "message", None)

    if msg is None:
        return None, "Invalid response from Ollama (missing message)."

    def _field(m, key: str):
        if isinstance(m, dict):
            return m.get(key)
        return getattr(m, key, None)

    content = _field(msg, "content")
    thinking = _field(msg, "thinking")

    text = content.strip() if isinstance(content, str) else ""
    if not text and isinstance(thinking, str) and thinking.strip():
        text = thinking.strip()

    if not text:
        return None, "Ollama returned an empty response."
    return text, None

def _nomination_user_message(agent: "PersonalityAgent", panel: list["PersonalityAgent"]) -> str:
    """
    Build the user prompt for one isolated nomination turn.

    The model must pick someone else on the panel and end with a machine-readable
    NOMINEE line so we can log rows to CSV reliably.
    """
    others = [p.name for p in panel if p.name != agent.name]
    others_str = ", ".join(others)
    return (
        f"{agent.name}, in exactly two sentences nominate exactly one crisis leader, "
        f"chosen only from: {others_str}. You cannot nominate yourself. "
        f"In those two sentences, explain briefly and state your confidence as a percent. "
        f"After that, add one final line by itself, exactly: NOMINEE: FullName "
        f"(where FullName is one of: {others_str})."
    )

def _parse_nominee(reply: str, valid_names: list[str]) -> str:
    """
    Read the nominee from the last matching 'NOMINEE: ...' line; fall back to fuzzy match.
    Returns the canonical panel name or an empty string if parsing fails.
    """
    valid_lower = {n.lower(): n for n in valid_names}
    for line in reversed(reply.strip().splitlines()):
        m = re.match(r"NOMINEE:\s*(.+)$", line.strip(), re.IGNORECASE)
        if not m:
            continue
        raw = m.group(1).strip().strip('"').strip("'")
        key = raw.lower()
        if key in valid_lower:
            return valid_lower[key]
        for low, canonical in valid_lower.items():
            if low in key or key in low:
                return canonical
    return ""

def _csv_person_label(panel: list["PersonalityAgent"], name: str) -> str:
    """
    Format a panel member for CSV: 'Name (MBTI)'. Unknown names pass through unchanged.
    """
    for member in panel:
        if member.name == name:
            return f"{member.name} ({member.mbti})"
    return name

class PersonalityAgent:
    def __init__(self, name, mbti, traits, color_code):
        self.name = name
        self.mbti = mbti
        self.traits = traits
        self.color = color_code

    def generate_reply(self, chat_history):
        """
        Call Ollama with a strict in-character system prompt and the user message(s).

        Returns:
            (reply_text, None) when the model returns a non-empty string.
            (None, error_message) on HTTP/API errors, malformed responses, or empty output.
        """
        system_prompt = (
            f"You are {self.name}, an {self.mbti}. {self.traits}. "
            f"Follow the user instructions exactly. "
            f"Use at most two sentences for your reasoning (no bullet points), "
            f"then the required final NOMINEE line on its own line—nothing after it."
        )

        try:
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *chat_history,
                ],
                # Room for two sentences plus a NOMINEE line.
                options={"num_predict": 280},
            )
            return _extract_reply_text(response)
        except Exception as e:
            return None, f"Error connecting to Ollama: {e}"

# Arthur's personality profile (ISTJ / Logistician), based on 16Personalities.
ARTHUR_ISTJ_TRAITS = (
    "As an ISTJ Logistician you are practical, fact-minded, reserved yet willful, "
    "with a rational outlook and methodical purpose in everything you do. You mean "
    "what you say, follow through on commitments, and respect clear structure, "
    "hierarchy, and established procedures—especially in a crisis. You avoid "
    "impulsive decisions, deliberate carefully, and believe there is a right way "
    "to proceed; you value honesty and straightforward communication over "
    "showmanship. You take responsibility for your choices, own mistakes quickly, "
    "and judge leaders by reliability, due diligence, legal compliance, and risk "
    "mitigation rather than charisma. Under pressure you stay grounded and logical, "
    "prioritizing stable systems and orderly execution. You can seem rigid when "
    "others bend rules or shirk duty, but your core gifts are clarity, loyalty, "
    "and dependability. You are wary of picking up others' slack without boundaries, "
    "yet you will shoulder hard obligations when the structure demands it."
)

# Luna's personality profile (ENFP / Campaigner), based on 16Personalities.
LUNA_ENFP_TRAITS = (
    "As an ENFP Campaigner you are enthusiastic, creative, and sociable—a free "
    "spirit who embraces big ideas and actions rooted in hope and goodwill toward "
    "others. You are outgoing, openhearted, and open-minded, with vibrant energy "
    "that can flow in many directions. You care deeply about meaningful emotional "
    "connections, cultural integration, employee morale, and a shared vision that "
    "unites people—not just having a good time. You blend carefree sociability, "
    "sparkling imagination, and contemplative introspection; you believe everyone "
    "and everything is connected, and that how we treat one another really matters. "
    "You look for magic and meaning in everyday life and inspire others with "
    "infectious enthusiasm when an idea captures you. In a crisis you champion "
    "leaders who build genuine rapport, emotional safety, and heartfelt dialogue "
    "so even timid voices feel heard. You can overread others' motives when stressed "
    "and lose consistency once initial inspiration fades, but your imagination, "
    "empathy, warmth, and courage can light up a team when you find a path that "
    "feels right."
)

# --- 1. Setup Agents ---
agents = [
    PersonalityAgent(
        "Arthur",
        "ISTJ",
        ARTHUR_ISTJ_TRAITS,
        "\033[94m",
    ),
    PersonalityAgent(
        "Luna",
        "ENFP",
        LUNA_ENFP_TRAITS,
        "\033[95m",
    ),
    PersonalityAgent(
        "Victor",
        "ENTJ",
        "Focused on market dominance, ROI, and aggressive strategic growth.",
        "\033[91m",
    ),
    PersonalityAgent(
        "Mira",
        "INFJ",
        "Focused on long-term alignment, ethics, and the human cost of big decisions.",
        "\033[96m",
    ),
    PersonalityAgent(
        "Diego",
        "ESTP",
        "Focused on reading the room, fast negotiation, and practical on-the-ground fixes.",
        "\033[92m",
    ),
]

# --- 2. CSV log (same folder as this script) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, "Most Nominated.csv")
PANEL_NAMES = [a.name for a in agents]
NUM_RUNS = 10

print("\033[1m--- SIMULATION STARTING ---\033[0m")
print(f"Logging nominations to: {CSV_PATH}")
print(f"Runs: {NUM_RUNS} (each run = full panel, isolated answers).\n")

# --- 3. Repeat full panel; append rows: run, nominee, nominator, full answer ---
with open(CSV_PATH, "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["run", "nominated", "nominated_by", "answer"])

    for run in range(1, NUM_RUNS + 1):
        print(f"\033[1m===== RUN {run} / {NUM_RUNS} =====\033[0m")

        for agent in agents:
            print(f"--- {agent.name} is typing... ---")
            solo_turn = [{"role": "user", "content": _nomination_user_message(agent, agents)}]

            reply, err = agent.generate_reply(solo_turn)

            if err is not None:
                print(f"ERROR ({agent.name}): {err}\n")
                writer.writerow(
                    [
                        run,
                        "",
                        _csv_person_label(agents, agent.name),
                        f"[error] {err}",
                    ]
                )
                time.sleep(1)
                continue

            nominee = _parse_nominee(reply, [n for n in PANEL_NAMES if n != agent.name])
            nominated_label = _csv_person_label(agents, nominee) if nominee else ""
            nominator_label = _csv_person_label(agents, agent.name)
            writer.writerow([run, nominated_label, nominator_label, reply])

            print(f"{agent.color}\033[1m{agent.name} ({agent.mbti}):\033[0m\n{reply}\033[0m\n")
            if not nominee:
                print("\033[93m[WARN] Could not parse NOMINEE: line; CSV nominated field left blank.\033[0m\n")

            time.sleep(1)

print("\033[1m--- SIMULATION ENDED ---\033[0m")

