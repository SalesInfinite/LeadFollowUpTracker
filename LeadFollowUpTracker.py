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
    return pd.read_csv(DB_FILE, parse_dates=["Created Date"] + TOUCHES + ["Date Sold"], dayfirst=True)

def save_db(df):
    df.to_csv(DB_FILE, index=False)

# ---------- ADD LEAD ----------
def add_lead(name):
    today = datetime.today().date()
    touches = [today + timedelta(days=i) for i in range(5)]
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
        for touch in TOUCHES:
            if pd.to_datetime(row[touch]).date() == today and touch not in str(row["Touch Status"]):
                followups.append({
                    "Name": row["Name"],
                    "Touch": touch
                })
    return followups

# ---------- MARK TOUCH DONE ----------
def mark_touch_done(name, touch):
    df = load_db()
    idx = df[df["Name"] == name].index[0]
    if touch not in str(df.at[idx, "Touch Status"]):
        df.at[idx, "Touch Status"] = str(df.at[idx, "Touch Status"]) + touch + ";"
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
    if st.form_submit_button("Add Lead"):
        if name:
            add_lead(name)
            st.success(f"Lead '{name}' added successfully!")
        else:
            st.error("Please fill in the name.")

if st.button("❌ Flush All Leads", type="primary"):
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
                st.experimental_rerun()
            if st.button(f"Mark as Sold - {task['Name']}"):
                update_lead_status(task['Name'], "Sold")
                st.success(f"Lead '{task['Name']}' marked as Sold.")
                st.experimental_rerun()
            if st.button(f"Mark as Dead - {task['Name']}"):
                update_lead_status(task['Name'], "Dead")
                st.success(f"Lead '{task['Name']}' marked as Dead.")
                st.experimental_rerun()
