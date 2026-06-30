import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import os

from db import (
    init_db, seed_initial_data, get_papers, get_topics, update_topic_status,
    add_study_log, get_study_logs, get_daily_hours, add_mock_test, get_mock_tests,
    get_progress_summary, calculate_streak, init_monsoon_test_series, seed_monsoon_tests, get_monsoon_tests, update_monsoon_test
)

st.set_page_config(page_title="CGPSC Mains Tracker", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A5F; margin-bottom: 0.5rem; }
    .stProgress > div > div > div > div { background-color: #48BB78; }
</style>
""", unsafe_allow_html=True)

init_db()
seed_status = seed_initial_data()
init_monsoon_test_series()
seed_monsoon_tests()

st.sidebar.title("🎯 CGPSC Mains Tracker")
nav = st.sidebar.radio("Navigate", ["Dashboard", "Syllabus Tracker", "Daily Study Log", "Mock Tests & Answer Writing", "Monsoon Test Series 2026", "Analytics", "Settings"])

if nav == "Dashboard":
    st.markdown('<p class="main-header">📊 CGPSC Mains Dashboard</p>', unsafe_allow_html=True)
    progress = get_progress_summary()
    streak = calculate_streak()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Syllabus Progress", f"{progress['overall_progress']}%")
    col2.metric("Study Streak", f"{streak} days 🔥")
    col3.metric("Topics Completed", f"{progress['completed_topics']}/{progress['total_topics']}")
    
    st.subheader("Paper-wise Progress")
    for p in progress['paper_progress']:
        st.progress(p['progress']/100, text=f"{p['paper']}: {p['progress']}%")
    
    st.subheader("Quick Log Study Session")
    with st.form("quicklog"):
        papers = get_papers()
        pmap = {p['name']: p['id'] for p in papers}
        pname = st.selectbox("Paper", list(pmap.keys()))
        hrs = st.number_input("Hours", 0.5, 10.0, 2.0)
        topic = st.text_input("Topic")
        if st.form_submit_button("Log Session"):
            add_study_log(date.today(), pmap[pname], hrs, topic)
            st.success("Logged!")
            st.rerun()

if nav == "Syllabus Tracker":
    st.markdown('<p class="main-header">📚 Syllabus Tracker</p>', unsafe_allow_html=True)
    papers = get_papers()
    pname = st.selectbox("Paper", [p['name'] for p in papers])
    pid = next(p['id'] for p in papers if p['name'] == pname)
    tdf = get_topics(pid)
    if not tdf.empty:
        st.data_editor(tdf[['section','topic','status','confidence','notes']], use_container_width=True)

if nav == "Daily Study Log":
    st.markdown('<p class="main-header">📝 Daily Study Log</p>', unsafe_allow_html=True)
    with st.form("log"):
        d = st.date_input("Date", date.today())
        papers = get_papers()
        pmap = {p['name']:p['id'] for p in papers}
        pn = st.selectbox("Paper", list(pmap))
        h = st.slider("Hours", 0.25, 8.0, 2.0)
        t = st.text_input("Topic studied")
        if st.form_submit_button("Save Log"):
            add_study_log(d, pmap[pn], h, t)
            st.success("Saved!")

if nav == "Mock Tests & Answer Writing":
    st.markdown('<p class="main-header">📋 Mock Tests</p>', unsafe_allow_html=True)
    with st.form("mock"):
        d = st.date_input("Date")
        papers = get_papers()
        pmap = {p['name']:p['id'] for p in papers}
        pn = st.selectbox("Paper", list(pmap))
        sc = st.number_input("Score", 0, 200, 120)
        if st.form_submit_button("Save"):
            add_mock_test(d, pmap[pn], "Mock Test", sc)
            st.success("Saved!")

if nav == "Monsoon Test Series 2026":
    st.markdown('<p class="main-header">📝 Monsoon Test Series 2026</p>', unsafe_allow_html=True)
    st.markdown("Track all 32 tests from Delhi IAS Monsoon Mains Test Series")
    
    df = get_monsoon_tests()
    attempted = len(df[df['status'] == 'Attempted'])
    total_hrs = df['hours_studied'].sum()
    avg_sc = df[df['score'].notna()]['score'].mean() if not df[df['score'].notna()].empty else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Attempted", f"{attempted}/32")
    c2.metric("Hours Studied", f"{total_hrs:.1f} hrs")
    c3.metric("Avg Score", f"{avg_sc:.1f}" if avg_sc > 0 else "N/A")
    c4.metric("Completion", f"{round(attempted/32*100)}%")
    
    st.subheader("Update Progress (Hours + Score + Remarks)")
    
    edit_df = st.data_editor(
        df[['test_no', 'subject', 'scheduled_date', 'status', 'hours_studied', 'score', 'remarks']],
        column_config={
            "status": st.column_config.SelectboxColumn("Status", options=["Not Attempted", "Attempted"]),
            "hours_studied": st.column_config.NumberColumn("Hours Studied", step=0.5),
            "score": st.column_config.NumberColumn("Score"),
            "remarks": st.column_config.TextColumn("Remarks / Weak Areas")
        },
        hide_index=True,
        use_container_width=True
    )
    
    if st.button("Save Changes"):
        for idx, row in edit_df.iterrows():
            update_monsoon_test(
                int(row['test_no']),
                status=row['status'],
                hours_studied=row['hours_studied'],
                score=row['score'] if pd.notna(row['score']) else None,
                remarks=row['remarks'] if pd.notna(row['remarks']) else ""
            )
        st.success("Saved!")
        st.rerun()

if nav == "Analytics":
    st.info("Analytics will be improved in next update.")

if nav == "Settings":
    st.warning("v0.2 - Monsoon Test Series feature added")