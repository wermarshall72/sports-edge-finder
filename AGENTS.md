# AGENTS.md — Sportsbook Edge Finder & ROI Tracker

## 1. Project Overview & Goal
We are building a **100% local, zero-cost Python web application** that launches in Google Chrome: an **NFL & College Football Automated Sportsbook "Edge Finder" + Bet & ROI Tracker**, designed for finding mathematical +EV (Positive Expected Value) plays against my regional sportsbook (**BetSaracen**).

## 2. Environment & Strict Technical Constraints
- **Hardware/OS:** MacBook (Apple Silicon / macOS) using `zsh`.
- **Python Manager:** `uv` installed and configured with **Python 3.12**.
- **Zero Paid APIs:** Do **not** use the Gemini API or any paid LLM calls inside the application code. All math, simulations, data fetching, and tracking must run 100% locally in Python for $0.
- **Frontend Framework:** **Streamlit** (100% Python, dark-mode dashboard running in Google Chrome, launched via a custom `zsh` alias `edge-finder`).
- **Database:** Local `sqlite3` file (`bets_tracker.db`) for permanent storage on my hard drive.
- **Version Control:** Git + GitHub for backing up progress after every milestone.

## 3. Core Architecture (Modular Design)
To keep code clean and easy to understand, we will split the app into logical files rather than one giant script:
- `app.py` — The main Chrome dashboard layout and tabs (Streamlit UI).
- `simulator.py` — The 10,000-game Monte Carlo math engine (`NumPy` / `SciPy`).
- `database.py` — The SQLite database setup and functions for logging/updating bets.
- `data_fetcher.py` — Scripts to pull free consensus odds and NFL/CFB team efficiency stats.

### Module Specifications:
- **Module A: Live Odds & BetSaracen Line Comparison**
  * Pull upcoming NFL and CFB matchups and consensus lines using free public endpoints (e.g., ESPN public scoreboard JSON API or The Odds API free 500-credit tier) with local caching.
  * Provide an editable table in Chrome where I can view the national consensus spread/total and type/adjust my **BetSaracen Line & Odds** right next to it to immediately highlight slow-moving regional lines.
- **Module B: 10,000-Game Monte Carlo Simulation Engine**
  * Support both **NFL** (~13.5 pt standard deviation, key number awareness around 3, 6, 7, 10) and **College Football** (~17.5 pt standard deviation).
  * Calculate baseline projected scores from 2026 team efficiency stats and run 10,000 simulated games locally using `NumPy`.
  * Output: Simulated Cover %, Implied Breakeven % (accounting for -110 vig or custom odds), Mathematical **Edge %**, **+EV %**, fractional **Kelly Criterion** recommended bet size, and an interactive `Plotly` distribution histogram.
- **Module C: Persistent Bet & ROI Tracker (SQLite)**
  * Log bets directly from a simulation or manually (Date, League, Matchup, Bet Type, BetSaracen Line, Odds, Stake $, Simulated Edge %, and Status: Pending / Won / Lost / Push).
  * **Portfolio & ROI Analytics Tab:** Display Starting Bankroll, Current Bankroll, Net Profit/Loss ($), overall **ROI %**, ATS Win Rate (NFL vs. CFB), a cumulative bankroll growth chart, and Model Calibration (comparing actual win rates of +5% edge bets vs. +2% edge bets).

## 4. Collaboration & Teaching Rules (CRITICAL)
I have **no prior coding experience**. You are both my software architect and my teacher. Follow these rules strictly in every response:
1. **Explain Simply & Clearly:** Whenever we write code or run a terminal command, explain *what* it is doing and *why* it works in plain English using everyday analogies (avoid unexplained jargon).
2. **Break Down the Math & Logic:** When we build the Monte Carlo engine, Kelly Criterion, or SQLite database, walk me through the logic behind the scenes so I genuinely understand how the math and data flow work.
3. **Concrete, Step-by-Step Terminal Commands:** Give me exact, copy-pasteable terminal commands one small step at a time. Never dump 5 giant files at once—let's build and test incrementally so I can see each piece working in Chrome.
4. **Context Management:** At the end of each completed Phase, provide an updated `## 5. Project Status & Phase Roadmap` section that I can paste back into my local `AGENTS.md` file before starting a fresh chat for the next phase.

## 5. Project Status & Phase Roadmap
- [ ] **Phase 1: Foundation, Monte Carlo Engine & Bet Tracker UI** — Create `~/sports-edge-finder` with `uv`, install packages, build `database.py` (SQLite) and `simulator.py` (NumPy 10,000-game engine), and launch `app.py` in Chrome with manual team score inputs and the full Bet/ROI Tracker tab.
- [ ] **Phase 2: Automated Team Stats Engine** — Build `data_fetcher.py` to pull real 2026 NFL & CFB offensive/defensive efficiency stats so the model automatically projects team scores for any matchup.
- [ ] **Phase 3: Live Consensus Odds & BetSaracen Comparison Board** — Connect free live scoreboard/odds feeds and build the side-by-side BetSaracen comparison table to automatically flag +EV discrepancies across the full weekend slate.
- [ ] **Phase 4: Shell Shortcut & GitHub Backup** — Set up the global `edge-finder` terminal command in `~/.zshrc` and push the clean repository to GitHub.
