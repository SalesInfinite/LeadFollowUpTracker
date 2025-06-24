# lead_followup_app.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# ---------- CONFIG ----------
DB_FILE = "leads.csv"
TOUCHES = ["First Touch", "Second Touch", "Third Touch", "Fourth Touch", "Fifth Touch"]

# ---------- INIT DB ----------
def init_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["Name", "Created Date"] + TOUCHES + ["Touch Status", "Lead Status", "Date Sold"])
        df.to_csv(DB_FILE, index=False)

def load_db():
    df = pd.read_csv(DB_FILE, parse_dates=["Created Date"] + TOUCHES + ["Date Sold"], dayfirst=True)
    df["Touch Status"] = df["Touch Status"].fillna("")
    return df

def save_db(df):
    df.to_csv(DB_FILE, index=False)

# ---------- ADD LEAD ----------
def add_lead(name, created_date=None):
    today = created_date if created_date else datetime.today().date()
    touches = []
    i = 0
    while len(touches) < 5:
        day = today + timedelta(days=i)
        if day.weekday() != 6:  # Skip Sundays (weekday() == 6)
            touches.append(day)
        i += 1

    new_lead = {
        "Name": name,
        "Created Date": today,
        "First Touch": touches[0],
        "Second Touch": touches[1],
        "Third Touch": touches[2],
        "Fourth Touch": touches[3],
        "Fifth Touch": touches[4],
        "Touch Status": "",
        "Lead Status": "Active",
        "Date Sold": pd.NaT
    }
    df = load_db()
    df = pd.concat([df, pd.DataFrame([new_lead])], ignore_index=True)
    save_db(df)

# ---------- FILTER TODAY ----------
def get_todays_followups():
    df = load_db()
    today = datetime.today().date()
    followups = []

    for _, row in df.iterrows():
        if row.get("Lead Status", "Active") != "Active":
            continue

        completed_touches = str(row.get("Touch Status", ""))

        for touch in TOUCHES:
            if pd.to_datetime(row[touch]).date() == today and touch not in completed_touches:
                followups.append({
                    "Name": row["Name"],
                    "Touch": touch
                })
    return followups

# ---------- MARK TOUCH DONE ----------
def mark_touch_done(name, touch):
    df = load_db()
    idx = df[df["Name"] == name].index[0]
    existing = df.at[idx, "Touch Status"]
    safe_status = "" if pd.isna(existing) else str(existing)
    df.at[idx, "Touch Status"] = safe_status + touch + ";"
    save_db(df)

# ---------- MARK AS SOLD/DEAD ----------
def update_lead_status(name, status):
    df = load_db()
    idx = df[df["Name"] == name].index[0]
    df.at[idx, "Lead Status"] = status
    if status == "Sold":
        df.at[idx, "Date Sold"] = datetime.today().date()
    save_db(df)

# ---------- FLUSH DATABASE ----------
def flush_db():
    if os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["Name", "Created Date"] + TOUCHES + ["Touch Status", "Lead Status", "Date Sold"])
        save_db(df)

# ---------- STREAMLIT UI ----------
init_db()
st.title("🔁 5-Day Lead Follow-Up Tool")

st.subheader("➕ Add New Lead")
with st.form("add_lead_form"):
    name = st.text_input("Name")
    retro_date = st.date_input("Date Lead Came In", value=datetime.today())
    if st.form_submit_button("Add Lead"):
        if name:
            add_lead(name, retro_date)
            st.success(f"Lead '{name}' added successfully!")
        else:
            st.error("Please fill in the name.")

with st.expander("🧹 Admin Tools"):
    confirm_flush = st.checkbox("Confirm flush of all leads")
    if st.button("Flush All Leads", type="secondary", help="This will delete all lead data permanently.") and confirm_flush:
        flush_db()
        st.warning("All leads have been flushed.")

st.subheader("📅 Today's Follow-Ups")
todays_tasks = get_todays_followups()
if not todays_tasks:
    st.info("No follow-ups for today! 💆‍♂️")
else:
    for task in todays_tasks:
        with st.expander(f"{task['Touch']} - {task['Name']}"):
            if st.button(f"Mark {task['Touch']} done for {task['Name']}"):
                mark_touch_done(task['Name'], task['Touch'])
                st.success(f"{task['Touch']} marked as done for {task['Name']}")
                st.rerun()
            if st.button(f"Mark as Sold - {task['Name']}"):
                update_lead_status(task['Name'], "Sold")
                st.success(f"Lead '{task['Name']}' marked as Sold.")
                st.rerun()
            if st.button(f"Mark as Dead - {task['Name']}"):
                update_lead_status(task['Name'], "Dead")
                st.success(f"Lead '{task['Name']}' marked as Dead.")
                st.rerun()

st.subheader("📋 All Leads")
all_data = load_db()
st.dataframe(all_data)
