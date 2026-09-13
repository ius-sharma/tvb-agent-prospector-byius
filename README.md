# TVB Autonomous Prospecting Agent

An autonomous lead discovery and validation dashboard built for The Venture Build
(TVB) Agentic and Automation Intern screening task.

The app finds and audits technology companies that match TVB's requested profile:

- $1M to $5M USD funding or revenue signal
- Tech-enabled platform or software business
- Minimal or no US presence
- CEO/co-founder contact available
- No generic or guessed emails in the qualified output

## What The Agent Does

The Streamlit app exposes a one-click prospecting run for reviewers. Each run:

1. Generates dynamic search vectors from TVB's target orbits and non-US hubs.
2. Searches the web using the `ddgs` metasearch package.
3. Converts search results into candidate records.
4. Validates each candidate against TVB's screening rules.
5. Separates qualified leads from rejected or needs-review candidates.
6. Displays an audit log with reasons, warnings, generated queries, and source links.
7. Exports the qualified list as CSV.

The reviewed cache in `data/verified_seeds.json` keeps the hosted demo stable. It is
merged after live discoveries so the app remains usable even when a search provider
rate-limits or returns sparse results.

## Verification Approach

The validator uses conservative checks:

- Funding/revenue parsing must land inside the $1M-$5M window.
- Company description or sector must indicate a tech platform.
- US-headquartered companies are rejected.
- Acquired, inactive, or no-longer-standalone companies are rejected when detected.
- Email addresses must be non-generic, syntactically valid, non-disposable, and backed
  by active domain MX records.
- Missing or unverified contact fields stay blank or move the candidate to review.

The app does not claim SMTP inbox-level verification because most mail servers block
that style of probing. The qualified table shows the exact email check status so the
reviewer can see what was validated.

## App Structure

```text
TVB-AGENT/
├── app.py                     # Streamlit dashboard
├── data/
│   └── verified_seeds.json    # Reviewed fallback leads
├── src/
│   ├── discovery.py           # Query generation, live search, candidate pipeline
│   ├── enrichment.py          # Email extraction and MX/domain checks
│   ├── tvb_context.py         # TVB criteria, hubs, and orbits
│   └── validator.py           # Strict qualification rules and audit output
├── .streamlit/
│   └── config.toml            # Streamlit theme and server settings
├── requirements.txt
└── README.md
```

## Local Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`.

## Deployment

Streamlit Community Cloud is the fastest deployment path:

1. Push this repository to a public GitHub repo.
2. Go to `https://share.streamlit.io`.
3. Create a new app from the repo.
4. Select branch `main`.
5. Set main file path to `app.py`.
6. Deploy and copy the public app URL.

No paid API key is required for the default flow.

## Submission Checklist

- Public GitHub repository
- Live hosted Streamlit/Render/Railway/Replit/Vercel link
- README included
- App opens without setup
- Reviewer can trigger a run from the UI
- Qualified lead table contains at least 15 records
- CSV export works
- Google Form submitted before the deadline

Submission form from TVB: `https://forms.gle/b2oekZ6uKex8dsuL7`
