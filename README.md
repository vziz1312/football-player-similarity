# Football Player Similarity

A football scouting project that compares players based on their statistics and finds players with similar profiles. The project uses Python and API-Football to collect player data. Currently, it focuses on La Liga players and uses statistics such as goals per 90, assists per 90, shots per 90, passes per 90, key passes per 90, dribbles per 90, duels per 90 and duels won per 90. The statistics are converted into numerical vectors, normalized and compared using cosine similarity. A higher similarity value means that the two players have more similar statistical profiles. The project is still under development, with the goal of building a more complete football scouting system with better data, position-based comparisons and eventually machine learning.

**Understanding similarity scores**

The similarity score is calculated using cosine similarity between player-stat vectors. It measures how closely two players' statistical profiles align across the selected features. A higher score indicates greater similarity in those statistical dimensions, but it does **not** mean the players are that percentage identical in playing style or overall ability. Results also depend on the selected statistics, playing time, and available data.

## Current Limitations

The experimental Transfermarkt-based model compares players using recent appearances, goals, assists, penalty goals, height and preferred foot. It filters players by broad position and ranks candidates using a distance-based similarity score.

This version has several limitations:
- Limited recent data for some players can make rankings unreliable.
- Goals and assists do not fully capture a player's playing style or tactical role.
- Height and preferred foot provide only limited information about how a player plays.
- Similarity scores are relative mathematical measures, not probabilities or percentages of playing-style similarity.
- The model has not yet been validated against expert scouting assessments.

Future improvements will focus on better feature normalization, richer performance data and position-specific comparisons.

## Technologies

Python, Requests, API-Football, Git and GitHub.

## Setup

Clone the repository and install the required packages:

    git clone https://github.com/vziz1312/football-player-similarity.git
    cd football-player-similarity
    pip install requests python-dotenv

Create a `.env` file in the project folder and add your API key:

    API_KEY=your_api_key_here

Then run:

    python main.py

## Author

Mohamed Aziz Mghirbi

GitHub: https://github.com/vziz1312
