# Football Player Similarity

A football scouting project that compares players based on their statistics and finds players with similar profiles. The project uses Python and API-Football to collect player data. Currently, it focuses on La Liga players and uses statistics such as goals per 90, assists per 90, shots per 90, passes per 90, key passes per 90, dribbles per 90, duels per 90 and duels won per 90. The statistics are converted into numerical vectors, normalized and compared using cosine similarity. A higher similarity value means that the two players have more similar statistical profiles. The project is still under development, with the goal of building a more complete football scouting system with better data, position-based comparisons and eventually machine learning.

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
