# Extension Ideas — How to Upgrade Digital Overload AI

## Priority Order

| Priority | Extension | Complexity | Value |
|---|---|---|---|
| 1 | Weekly AFI Trend Report | Low | High |
| 2 | Gmail Deadline Extractor | Medium | High |
| 3 | Google Calendar Import | Medium | High |
| 4 | Mobile PWA | Medium | Medium |
| 5 | ML Recommendation Engine | High | High |
| 6 | Team Overload Mode | High | Medium |

---

## Extension 1 — Weekly AFI Trend Report

**What it adds:**
Save every analysis to SQLite. At end of week show a Plotly line
chart of Overload, AFI, Capacity Fit scores across all 7 days.

**Why it matters:**
A student might score AFI=80 every day for two weeks and not notice.
The trend report makes chronic fragmentation visible.

**How to implement:**

Install:

    pip install sqlalchemy

Create db.py:

    from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
    from sqlalchemy.orm import declarative_base, Session
    from datetime import datetime

    Base = declarative_base()
    engine = create_engine("sqlite:///overload_history.db")

    class AnalysisRecord(Base):
        __tablename__ = "analyses"
        id        = Column(Integer, primary_key=True)
        timestamp = Column(DateTime)
        overload  = Column(Float)
        afi       = Column(Float)
        capacity  = Column(Float)
        action    = Column(String)

    Base.metadata.create_all(engine)

    def save_analysis(overload, afi, capacity, action):
        with Session(engine) as session:
            session.add(AnalysisRecord(
                timestamp=datetime.now(),
                overload=overload,
                afi=afi,
                capacity=capacity,
                action=action
            ))
            session.commit()

Add to app.py after scoring:

    from db import save_analysis
    save_analysis(scores["overload"], scores["afi"],
                  scores["capacity"], action)

---

## Extension 2 — Gmail Deadline Extractor

**What it adds:**
Scan Gmail inbox for emails with deadline keywords and auto-add
them to the task list — no manual typing needed.

**How to implement:**

    def fetch_deadline_emails(service) -> list:
        query = "subject:(deadline OR due OR submit) newer_than:7d"
        results = service.users().messages().list(
            userId="me", q=query, maxResults=10
        ).execute()
        snippets = []
        for msg in results.get("messages", []):
            detail = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata"
            ).execute()
            snippets.append(detail.get("snippet", ""))
        return snippets

---

## Extension 3 — Google Calendar Auto Import

**What it adds:**
Pull today's events directly from Google Calendar and pre-fill
the analysis — no typing needed.

**How to implement:**

    from googleapiclient.discovery import build

    def fetch_todays_events(creds) -> list:
        service = build("calendar", "v3", credentials=creds)
        today_start = datetime.utcnow().replace(hour=0).isoformat() + "Z"
        today_end   = datetime.utcnow().replace(hour=23).isoformat() + "Z"
        events = service.events().list(
            calendarId="primary",
            timeMin=today_start,
            timeMax=today_end,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        return events.get("items", [])

---

## Extension 4 — ML Recommendation Engine

**What it adds:**
Replace the 16-row rule matrix with a trained classifier that
learns from real student feedback over time.

**Phase 1 — Collect feedback:**

    rating = st.slider("Was this recommendation useful?", 1, 5, 3)
    if st.button("Submit Feedback"):
        save_feedback(overload, afi, capacity, action, rating)

**Phase 2 — Train classifier:**

    from sklearn.ensemble import RandomForestClassifier

    df = pd.read_sql("SELECT overload, afi, capacity, action
                      FROM feedback WHERE rating >= 4", engine)

    X = df[["overload", "afi", "capacity"]]
    y = df["action"]

    clf = RandomForestClassifier(n_estimators=100)
    clf.fit(X, y)

**Phase 3 — Replace rule matrix:**

    def get_action(overload, afi, capacity):
        return clf.predict([[overload, afi, capacity]])[0]

Keep rule matrix as fallback when model confidence is low.

---

## Extension 5 — Mobile PWA

**What it adds:**
Students can save the app to phone home screen and get push
alerts when predicted overload crosses threshold.

**manifest.json:**

    {
      "name": "Digital Overload AI",
      "short_name": "OverloadAI",
      "start_url": "/",
      "display": "standalone",
      "background_color": "#0d1117",
      "theme_color": "#1a73e8"
    }

**Notification trigger:**

    if overload > 75:
        send_push_notification(
            title="Overload Alert",
            body=f"Your score is {overload:.0f}. Check your plan."
        )

---

## Extension 6 — Team Overload Mode

**What it adds:**
Each team member submits their individual analysis. Team lead
sees aggregate capacity before assigning new tasks.

**Aggregate logic:**

    team_capacity = sum(m.capacity for m in team) / len(team)

    if team_capacity < 60:
        st.error("Team below 60% capacity.
                  Do not assign new tasks this sprint.")