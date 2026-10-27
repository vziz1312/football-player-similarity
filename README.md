# Football Player Similarity

A Python football analytics and scouting project that compares players
using statistical profiles. The repository currently contains two related
but separate prototypes: an API-Football-based similarity application and
an experimental Transfermarkt-based scouting model.

## Project Workflows

### 1. API-Football Prototype

The original prototype uses API-Football statistics and a local SQLite
database.

Main files:

- `main.py` — application entry point for comparing player profiles.
- `database.py` — database schema, player data access, and per-90 metrics.
- `similarity.py` — cosine similarity implementation.
- `collect_data.py` — API-Football data collection.
- `test_similarity.py` — tests for cosine similarity.

The prototype uses position-specific statistics. Depending on position,
these can include goals, assists, shots, passes, key passes, dribbles,
duels won, and goalkeeper rating. Player vectors are normalized and
compared using cosine similarity.

The current data-collection code is configured around La Liga
(competition ID 140), season 2023. The workflow still needs a clearly
documented, reproducible data-loading process.

### 2. Hybrid Transfermarkt Scouting Model

The experimental model is implemented in `transfermarkt_scouting_hybrid.py`.

It uses a local `transfermarkt.db` SQLite database containing player
profiles and performance records.

The model works as follows:

1. It searches for a player by name, ignoring differences in capitalization
   and accents.
2. It uses the selected recent seasons (`25/26`, `24/25`, and `23/24`)
   when the target has at least 20 recorded appearances in those seasons.
3. If the target has fewer than 20 recent appearances, it falls back to
   career-wide statistics. The target and candidates are then compared
   using career-wide data.
4. It requires at least 20 appearances per candidate in recent mode, or
   100 appearances per player in career-wide mode.
5. It restricts recommendations to the target's position category.
6. It calculates goals per appearance and assists per appearance, then
   adjusts these rates toward the positional baseline to reduce the
   influence of small samples.
7. It ranks candidates using a distance-based similarity score.

The sample-size adjustment uses 20 prior appearances:

`reliability = appearances / (appearances + 20)`

The adjusted rates combine a player's observed rates with the positional
baseline. The target player is excluded from the baseline and from the
recommendation list.

The similarity score is calculated as:

`similarity = 1 / (1 + Euclidean distance)`

A higher score means the two adjusted statistical vectors are closer.
The score is a ranking measure, **not a probability or a percentage of
overall playing-style similarity**.

Main files:

- `transfermarkt_scouting_hybrid.py` — experimental hybrid model.
- `test_transfermarkt_scouting_hybrid.py` — unit and integration tests.
- `import_transfermarkt.py` — Transfermarkt data import utility.
- `add_appearances.py` — utility for enriching records with appearance data.

## Requirements

- Python 3.10 or newer recommended.
- `requests` and `python-dotenv` for the API-Football workflow.
- `pandas` for the appearance-data utility.

Install the dependencies:

```bash
pip install requests python-dotenv pandas
```

The hybrid model itself uses Python's standard library, including `sqlite3`.

## Configuration and Data

The API-Football workflow uses an API key stored in a local `.env` file:

```dotenv
API_KEY=your_api_key_here
```

Never commit your real API key or `.env` file to GitHub.

The SQLite databases are local data files and are intentionally excluded
from Git by the `.gitignore` rules. They are not included in a fresh clone
of this repository.

Before running a workflow, prepare the corresponding local database and
ensure that it contains the expected tables and records.

The hybrid model expects `transfermarkt.db` beside
`transfermarkt_scouting_hybrid.py`, with `players` and `performances`
tables and a populated `nb_on_pitch` appearance field.

The original application uses `football.db`. Initializing its schema is
not the same as importing player statistics; the required data must also
be available before meaningful comparisons can be performed.

## Running the Models

Run the original API-Football prototype after its database has been
populated:

```bash
python main.py
```

Run the hybrid Transfermarkt model after preparing `transfermarkt.db`:

```bash
python transfermarkt_scouting_hybrid.py
```

The hybrid model asks for a player name and prints ranked candidates
with raw and adjusted goals/assists per appearance.

## Tests

Run the cosine similarity tests:

```bash
python test_similarity.py
```

Run the hybrid model tests:

```bash
python test_transfermarkt_scouting_hybrid.py
```

The hybrid test suite covers name normalization, vector validation,
sample-size adjustment, recent-season selection, position filtering,
and career-wide fallback using temporary SQLite databases.

## Current Limitations

- The hybrid model uses only goals and assists per appearance. It does not
  capture the full playing style, tactical role, defensive contribution,
  passing quality, or off-ball movement of a player.
- Appearance counts and statistics depend on the completeness and
  consistency of the available data.
- The sample-size prior of 20 appearances is a configurable heuristic and
  has not been empirically optimized.
- The model has not yet been validated against expert scouting assessments
  or a formal benchmark.
- The API-Football and Transfermarkt prototypes are separate workflows and
  have not yet been consolidated into a single application.

## Roadmap

- Improve data quality and reproducibility.
- Evaluate similarity rankings against known players and scouting criteria.
- Explore richer, position-specific performance features.
- Consolidate the project structure and remove obsolete experiments safely.
- Improve installation instructions and the user experience.

## Author

Mohamed Aziz Mghirbi

GitHub: https://github.com/vziz1312