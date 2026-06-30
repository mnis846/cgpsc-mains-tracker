# 🎯 CGPSC Mains Tracker

A powerful, local-first webapp to track your **CGPSC Mains preparation** — syllabus progress, daily study logs, mock tests, weak areas, and analytics.

Built specifically for serious CGPSC aspirants who want data-driven, consistent preparation.

## Features (v0.1 MVP)

- **📊 Dashboard**: Overall progress, current streak, weekly hours, quick log, recent activity, paper-wise progress bars
- **📚 Syllabus Tracker**: 
  - Pre-loaded with structured CGPSC Mains 7 papers + key topics/sections
  - Editable status (Not Started → In Progress → Completed → Revised)
  - Confidence slider (1-5) per topic
  - Notes field for resources or key points
  - Add your own custom topics
- **📝 Daily Study Log**: Log hours, topic, mood/energy, takeaways, tags. Builds your streak automatically.
- **📋 Mock Tests & Answer Writing**: Log full mocks, sectional tests, PYQs, answer writing practice with score, feedback & weak areas.
- **📈 Analytics**: Time distribution by paper, study consistency, recurring weak areas from mocks, confidence distribution.
- **Local SQLite DB**: Everything stored in one `cgpsc_mains_tracker.db` file. Easy to backup.

## Tech Stack

- **Python + Streamlit** (beautiful interactive UI)
- **SQLite** (zero-config local database)
- **Pandas + Plotly** (analytics & charts)

## Setup & Run (on your laptop)

1. Clone or download this folder.
2. Create virtual environment.
3. `pip install -r requirements.txt`
4. `streamlit run app.py`

## Future Roadmap

- Spaced repetition revision system
- AI Study Planner using Ollama
- Integration with your cgpsc-reader
- PDF export reports

**Made for focused preparation.** Keep showing up!