"""
Participant Management and Roster Administration Page.
Allows registering, searching, editing, deleting, and CSV batch importing of students.
Strictly stores identity metadata only: NO facial embeddings or raw photos.
"""

import io
import pandas as pd
import streamlit as st
from modules.database import (
    add_participant, list_participants, get_participant,
    update_participant, delete_participant
)
from modules.demo_data import seed_sample_participants_if_empty
from modules.ui_common import apply_theme, render_page_header

st.set_page_config(page_title="Participants - Classroom Agent", page_icon="👥", layout="wide")
apply_theme()

render_page_header(
    title="Participant Management & Roster",
    subtitle="Manage registered course attendees for attendance mapping. Does not store biometric templates."
)

tab_roster, tab_add, tab_import = st.tabs(["📋 Participant Roster", "➕ Register New Participant", "📥 Batch Import Roster (CSV)"])

# ---------------- TAB 1: ROSTER VIEW & SEARCH ----------------
with tab_roster:
    col_search, col_act = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Participants", placeholder="Search by ID, name, email or course...")
    with col_act:
        st.write("")
        st.write("")
        if st.button("👥 Populate 8 Sample Students", use_container_width=True):
            seed_sample_participants_if_empty()
            st.success("Sample students populated!")
            st.rerun()

    participants = list_participants(search_query=search_query)

    if not participants:
        st.info("No participants found. Add students using the 'Register New Participant' or 'Batch Import' tabs.")
    else:
        df = pd.DataFrame(participants)
        df = df[["participant_id", "display_name", "email", "course", "created_at"]]
        df.columns = ["Participant ID", "Full Name", "Email", "Course / Department", "Registered Date"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("#### ✏️ Edit or Remove Participant")
        sel_id = st.selectbox("Select Participant ID to edit or delete:", [p["participant_id"] for p in participants])
        selected_p = get_participant(sel_id)

        if selected_p:
            with st.form(key="edit_p_form"):
                e_col1, e_col2 = st.columns(2)
                with e_col1:
                    e_name = st.text_input("Display Name", value=selected_p["display_name"])
                    e_email = st.text_input("Email", value=selected_p["email"] or "")
                with e_col2:
                    e_course = st.text_input("Course", value=selected_p["course"] or "")
                
                f_col1, f_col2 = st.columns([1, 1])
                with f_col1:
                    btn_save = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
                with f_col2:
                    btn_del = st.form_submit_button("🗑️ Delete Participant", use_container_width=True)

                if btn_save:
                    update_participant(sel_id, e_name, e_email, e_course)
                    st.success(f"Updated participant {sel_id} successfully!")
                    st.rerun()
                elif btn_del:
                    delete_participant(sel_id)
                    st.warning(f"Deleted participant {sel_id}.")
                    st.rerun()


# ---------------- TAB 2: REGISTER SINGLE PARTICIPANT ----------------
with tab_add:
    st.subheader("Add Individual Student")
    with st.form(key="add_participant_form", clear_on_submit=True):
        col_id, col_name = st.columns(2)
        with col_id:
            new_id = st.text_input("Participant ID *", placeholder="e.g. STU109").strip()
            new_email = st.text_input("Email Address", placeholder="e.g. student@college.edu").strip()
        with col_name:
            new_name = st.text_input("Display / Full Name *", placeholder="e.g. Maya Krishnan").strip()
            new_course = st.text_input("Course / Department", placeholder="e.g. Computer Science").strip()

        submit_add = st.form_submit_button("➕ Register Participant", type="primary")

        if submit_add:
            if not new_id or not new_name:
                st.error("Participant ID and Display Name are mandatory fields.")
            else:
                success = add_participant(new_id, new_name, new_email, new_course)
                if success:
                    st.success(f"Participant '{new_name}' ({new_id}) registered successfully!")
                    st.rerun()
                else:
                    st.error(f"Participant ID '{new_id}' already exists in database. Please choose a unique ID.")


# ---------------- TAB 3: BATCH IMPORT CSV ----------------
with tab_import:
    st.subheader("Import Roster from CSV File")
    st.markdown("""
    Upload a CSV file with the following column headers:  
    `participant_id`, `display_name`, `email`, `course`
    """)

    # Downloadable CSV template
    sample_csv_template = "participant_id,display_name,email,course\nSTU201,Rajesh Kumar,rajesh.k@college.edu,Data Science\nSTU202,Priya Nair,priya.n@college.edu,Data Science\n"
    st.download_button(
        label="📄 Download CSV Template",
        data=sample_csv_template,
        file_name="roster_template.csv",
        mime="text/csv"
    )

    uploaded_file = st.file_uploader("Upload Roster CSV", type=["csv"])

    if uploaded_file is not None:
        try:
            csv_df = pd.read_csv(uploaded_file)
            st.write("##### File Preview:")
            st.dataframe(csv_df.head(10), use_container_width=True)

            required_cols = {"participant_id", "display_name"}
            if not required_cols.issubset(set(csv_df.columns)):
                st.error(f"CSV missing mandatory columns: {required_cols - set(csv_df.columns)}")
            else:
                if st.button("🚀 Import All Rows", type="primary"):
                    imported_count = 0
                    duplicate_count = 0
                    for _, row in csv_df.iterrows():
                        pid = str(row["participant_id"]).strip()
                        name = str(row["display_name"]).strip()
                        email = str(row.get("email", "")).strip() if pd.notna(row.get("email")) else ""
                        course = str(row.get("course", "")).strip() if pd.notna(row.get("course")) else ""

                        if pid and name:
                            if add_participant(pid, name, email, course):
                                imported_count += 1
                            else:
                                duplicate_count += 1

                    st.success(f"Successfully imported {imported_count} participant(s)! (Skipped {duplicate_count} existing IDs)")
                    st.rerun()

        except Exception as ex:
            st.error(f"Failed to parse CSV file: {str(ex)}")
