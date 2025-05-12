# filename: app.py
import streamlit as st
import pandas as pd
import datetime
from collections import defaultdict
import uuid # For unique component IDs
import random # Added for optional shuffle in placeholder

# --- Helper Functions ---

def time_to_minutes(time_obj):
    """Converts a datetime.time object to minutes since midnight."""
    if time_obj is None:
        return 0
    return time_obj.hour * 60 + time_obj.minute

def minutes_to_time(total_minutes):
    """Converts total minutes since midnight back to a datetime.time object."""
    hours, minutes = divmod(total_minutes, 60)
    # Ensure hours and minutes are within valid range for datetime.time
    hours = max(0, min(23, hours))
    minutes = max(0, min(59, minutes))
    return datetime.time(hours, minutes)


def format_time_slot(start_minute, duration_minute):
    """Formats a time slot string (e.g., '08:00-08:50')."""
    end_minute = start_minute + duration_minute
    start_h, start_m = divmod(start_minute, 60)
    end_h, end_m = divmod(end_minute, 60)
    return f"{start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}"

def parse_time_slot(time_slot_str):
    """Parses a time slot string 'HH:MM-HH:MM' into start and end minutes."""
    try:
        start_str, end_str = time_slot_str.split('-')
        start_h, start_m = map(int, start_str.split(':'))
        end_h, end_m = map(int, end_str.split(':'))
        start_minute = start_h * 60 + start_m
        end_minute = end_h * 60 + end_m
        return start_minute, end_minute
    except Exception:
        return None, None # Handle parsing errors


# --- Placeholder Scheduling Logic ---
# !!! IMPORTANT: Replace this with a real implementation using OR-Tools or similar !!!
@st.cache_data # Cache the output based on inputs
def generate_schedule_from_components(class_components, classrooms, labs, working_days, start_time_obj, end_time_obj):
    """
    Generates a routine using a very basic, non-optimized placeholder algorithm.
    This logic does NOT prevent conflicts and is for demonstration only.
    It assigns tasks sequentially without considering resource (room, section) availability over time.
    """
    st.warning("⚠️ Using **PLACEHOLDER** scheduling logic. This is NOT optimized, does not prevent conflicts, and will likely result in an impractical routine. It is intended only to demonstrate the UI and data flow. Replace with a real solver (e.g., OR-Tools) for practical use.")

    if not class_components or not working_days:
        st.error("Cannot generate schedule: Missing class components or working days.")
        return pd.DataFrame() # Return empty DataFrame on error/missing data

    # Validate if rooms are available if needed
    needs_theory_room = any(c['class_type'] == "Theory" for c in class_components)
    needs_lab_room_any = any(c['class_type'] == "Lab" and c.get('assigned_room') == "Any Available Lab" for c in class_components)

    if needs_theory_room and not classrooms:
        st.error("Cannot schedule: Theory components exist, but no Classrooms are defined in the sidebar.")
        return pd.DataFrame()

    if needs_lab_room_any and not labs:
        st.error("Cannot schedule: Lab components need 'Any Available Lab', but no general Lab rooms are defined in the sidebar.")
        return pd.DataFrame()

    schedule_entries = []
    start_minutes_val = time_to_minutes(start_time_obj)
    end_minutes_val = time_to_minutes(end_time_obj)

    # Prepare tasks to schedule: each session for each section of each component
    tasks_to_schedule = []
    for comp in class_components:
        for section in comp['sections']:
            for session_num in range(comp['sessions_per_week']):
                 tasks_to_schedule.append({
                    'course_code': comp['course_code'],
                    'component_title': comp['component_title'],
                    'semester': comp['semester'],
                    'section': section,
                    'class_type': comp['class_type'],
                    'duration_minutes': comp['duration_minutes'],
                    'assigned_room': comp.get('assigned_room'), # Can be specific lab name or "Any Available Lab" or None (for theory)
                    'task_id': f"{comp['id']}_{section}_{session_num}" # Unique ID for this specific task instance
                 })

    # --- Start of Naive Placeholder Assignment Logic ---
    # This is where a real solver would use optimization algorithms.
    # The current logic assigns tasks in the order they appear in the tasks_to_schedule list.
    # It tries to place a task on the first available working day, starting at the last assigned time + buffer.
    # It does NOT check for conflicts (e.g., two classes in the same room or for the same section at the same time).

    # Shuffle tasks to make the naive assignment slightly less predictable (still bad)
    random.shuffle(tasks_to_schedule)

    current_slot_time_per_day = {day: start_minutes_val for day in working_days}
    day_index_counter = {day: 0 for day in working_days} # To cycle through rooms/days somewhat

    for task in tasks_to_schedule:
        assigned = False
        # Naively try to place the task on the next working day in sequence
        for _ in range(len(working_days)): # Try all days once per task
             # Get the next day index using a counter for variation
            day_idx = day_index_counter[working_days[0]] % len(working_days)
            current_day = working_days[day_idx]
            day_index_counter[working_days[0]] += 1 # Increment counter for next task

            slot_start = current_slot_time_per_day[current_day]
            slot_end = slot_start + task['duration_minutes']

            # Check if it fits within the daily time frame
            if slot_end <= end_minutes_val:
                # Determine room based on type and user input
                room_to_use = None
                if task['class_type'] == "Theory":
                    if classrooms:
                        # Naively pick a classroom round-robin style (doesn't check availability)
                        room_to_use = classrooms[day_index_counter[current_day] % len(classrooms)] # Use a per-day counter for rooms
                    # else: Error should be caught before generate
                elif task['class_type'] == "Lab":
                    if task['assigned_room'] and task['assigned_room'] != "Any Available Lab":
                        room_to_use = task['assigned_room'] # Use specifically assigned lab
                    elif labs:
                         # Naively pick a lab round-robin style if "Any Available Lab" (doesn't check availability)
                        room_to_use = labs[day_index_counter[current_day] % len(labs)] # Use a per-day counter for labs
                    # else: Error should be caught before generate

                if room_to_use:
                     # In the placeholder, we *do not* check for conflicts (room, section, etc.) at slot_start.
                     # A real solver would have complex constraint checking here.

                    schedule_entries.append({
                        'Day': current_day,
                        'Time Slot': format_time_slot(slot_start, task['duration_minutes']),
                        'Start_Minute': slot_start,
                        'End_Minute': slot_end,
                        'Semester': task['semester'],
                        'Section': task['section'],
                        'Course Code': task['course_code'],
                        'Component Title': task['component_title'],
                        'Room/Lab': room_to_use,
                        'Type': task['class_type'],
                        'Component_ID': task['task_id'] # Keep a unique ID for sorting/debugging
                    })
                    # Move the start time for the next item scheduled on this specific day
                    current_slot_time_per_day[current_day] = slot_end + 5 # Add 5 min buffer
                    assigned = True
                    break # Move to the next task in tasks_to_schedule

            # If the task didn't fit in the current day's slot, the loop continues to try the next day...
            # If it tries all days and doesn't fit within the remaining time window of any day, it won't be scheduled.
            # Reset time for the day if it goes beyond end_time - simplistic overflow handling
            if slot_end > end_minutes_val:
                 current_slot_time_per_day[current_day] = start_minutes_val # Reset day's start time for future tasks

        if not assigned:
             # This task couldn't be placed within the time frame on any working day using this naive logic
            st.warning(f"Could not place task: {task['component_title']} ({task['course_code']}) for Section {task['section']}. Consider adjusting time window or number of sessions.")
            # In a real solver, this would mean no feasible solution or need for backtracking

    # --- End of Naive Placeholder Assignment Logic ---


    if not schedule_entries:
        st.info("Placeholder logic did not generate any schedule entries.")
        return pd.DataFrame()

    # Convert to DataFrame and sort for consistent output
    schedule_df = pd.DataFrame(schedule_entries)
    # Ensure sort order considers the defined working days
    day_order_map = {day: i for i, day in enumerate(working_days)}
    schedule_df['Day_Order'] = schedule_df['Day'].map(day_order_map).fillna(len(day_order_map))
    schedule_df = schedule_df.sort_values(by=['Semester', 'Day_Order', 'Start_Minute', 'Section', 'Course Code']).reset_index(drop=True)
    schedule_df = schedule_df.drop(columns=['Day_Order'], errors='ignore') # Drop helper column

    return schedule_df

# --- End Placeholder Logic ---


# --- Initialize Session State ---
if 'semesters' not in st.session_state: st.session_state.semesters = []
if 'sections' not in st.session_state: st.session_state.sections = {}
if 'class_components' not in st.session_state: st.session_state.class_components = []
if 'classrooms' not in st.session_state: st.session_state.classrooms = []
if 'labs' not in st.session_state: st.session_state.labs = []
if 'schedule_df' not in st.session_state: st.session_state.schedule_df = None
if 'working_days_config' not in st.session_state: st.session_state.working_days_config = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
if 'start_time_config' not in st.session_state: st.session_state.start_time_config = datetime.time(8, 0)
if 'end_time_config' not in st.session_state: st.session_state.end_time_config = datetime.time(17, 0)

# --- Streamlit UI ---
st.set_page_config(layout="wide", page_title="University Routine Generator")
st.title("🎓 University Routine Generator")
st.caption(f"Current Date: {datetime.datetime.now().strftime('%A, %B %d, %Y, %I:%M %p')}.")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ General Configuration")
    all_days_ordered = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    # Use session state value if available, otherwise default
    default_sidebar_days = st.session_state.working_days_config if st.session_state.working_days_config else ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    st.session_state.working_days_config = st.multiselect("Working Days", all_days_ordered, default=default_sidebar_days)
    st.session_state.start_time_config = st.time_input("University Start Time", value=st.session_state.start_time_config)
    st.session_state.end_time_config = st.time_input("University End Time", value=st.session_state.end_time_config, help="You can input times like 17:10, 18:05, etc.")

    st.subheader("Manage Rooms")
    with st.form("add_classroom_form_sidebar", clear_on_submit=True):
        new_classrooms_str = st.text_input("Add Classroom Names (comma-separated)", placeholder="e.g., C101,C102")
        if st.form_submit_button("Add Classrooms"):
            if new_classrooms_str:
                added_count = 0
                for r in [r.strip() for r in new_classrooms_str.split(',') if r.strip()]:
                    if r and r not in st.session_state.classrooms: # Added check for non-empty string after strip
                        st.session_state.classrooms.append(r); added_count += 1
                if added_count: st.success(f"Added {added_count} classroom(s).")
                else: st.info("No new unique classrooms entered.")
                st.session_state.schedule_df = None # Invalidate schedule
                st.rerun()
            else: st.warning("Enter classroom names.")
    st.write("Classrooms:", ", ".join(st.session_state.classrooms) or "None")

    if st.session_state.classrooms:
        with st.form("remove_classroom_form_sidebar", clear_on_submit=True):
             room_to_remove = st.selectbox("Remove Classroom", ["Select..."] + st.session_state.classrooms, key="remove_classroom_select")
             if st.form_submit_button(f"Remove Selected Classroom"):
                if room_to_remove != "Select...":
                    st.session_state.classrooms.remove(room_to_remove)
                    # Note: Removing rooms here doesn't automatically update component assignments.
                    # A real app might add validation or update logic.
                    st.success(f"Removed classroom: {room_to_remove}")
                    st.session_state.schedule_df = None # Invalidate schedule
                    st.rerun()
                else:
                    st.info("Select a classroom to remove.")


    st.markdown("---") # Separator

    with st.form("add_lab_form_sidebar", clear_on_submit=True):
        new_labs_str = st.text_input("Add Lab Names (comma-separated)", placeholder="e.g., L501,L502")
        if st.form_submit_button("Add Labs"):
            if new_labs_str:
                added_count = 0
                for l_room in [l.strip() for l in new_labs_str.split(',') if l.strip()]:
                    if l_room and l_room not in st.session_state.labs: # Added check for non-empty string after strip
                        st.session_state.labs.append(l_room); added_count += 1
                if added_count: st.success(f"Added {added_count} lab(s).")
                else: st.info("No new unique labs entered.")
                st.session_state.schedule_df = None # Invalidate schedule
                st.rerun()
            else: st.warning("Enter lab names.")
    st.write("Labs:", ", ".join(st.session_state.labs) or "None")

    if st.session_state.labs:
         with st.form("remove_lab_form_sidebar", clear_on_submit=True):
             lab_to_remove = st.selectbox("Remove Lab", ["Select..."] + st.session_state.labs, key="remove_lab_select")
             if st.form_submit_button(f"Remove Selected Lab"):
                if lab_to_remove != "Select...":
                    st.session_state.labs.remove(lab_to_remove)
                    # Invalidate schedule, maybe warn user if components were assigned to this lab
                    st.success(f"Removed lab: {lab_to_remove}")
                    st.session_state.schedule_df = None # Invalidate schedule
                    st.rerun()
                else:
                    st.info("Select a lab to remove.")


    st.divider()
    if st.button("Clear All Input Data", type="secondary", help="Resets semesters, sections, class components, rooms, and the generated schedule."):
        st.session_state.semesters.clear() # Use .clear() or reassign = []
        st.session_state.sections.clear() # Use .clear()
        st.session_state.class_components.clear() # Use .clear()
        st.session_state.classrooms.clear() # Use .clear()
        st.session_state.labs.clear() # Use .clear()
        st.session_state.schedule_df = None
        st.success("All user-input data cleared.")
        st.rerun()

# --- Main Area Tabs ---
tab1, tab2, tab3 = st.tabs(["📚 Semesters & Sections", "➕ Add Class Component", "📅 Generate Routine"])

with tab1:
    st.header("Semesters and Sections")
    col1_sem, col2_sec = st.columns(2)
    with col1_sem:
        with st.form("add_semester_form_tab1", clear_on_submit=True):
            new_semester = st.text_input("Semester Name/Number*", placeholder="e.g., Fall 2025")
            if st.form_submit_button("Add Semester"):
                if new_semester and new_semester not in st.session_state.semesters:
                    st.session_state.semesters.append(new_semester)
                    st.session_state.sections[new_semester] = [] # Initialize sections for new semester
                    st.success(f"Added Semester: {new_semester}")
                    st.session_state.schedule_df = None # Invalidate schedule
                    st.rerun()
                elif not new_semester: st.warning("Enter semester name.")
                else: st.warning(f"Semester '{new_semester}' already added.")

        st.subheader("Manage Semesters")
        if st.session_state.semesters:
             with st.form("remove_semester_form_tab1", clear_on_submit=True):
                 sem_to_remove = st.selectbox("Select Semester to Remove", ["Select..."] + st.session_state.semesters, key="remove_sem_select")
                 if st.form_submit_button(f"Remove Selected Semester"):
                    if sem_to_remove != "Select...":
                        st.session_state.semesters.remove(sem_to_remove)
                        removed_sections = st.session_state.sections.pop(sem_to_remove, []) # Remove sections, default to empty list if none
                        if removed_sections:
                            st.info(f"Removed sections associated with {sem_to_remove}: {', '.join(removed_sections)}")
                        else:
                             st.info(f"No sections were associated with {sem_to_remove}.")

                        # Remove components associated with this semester
                        initial_comp_count = len(st.session_state.class_components)
                        st.session_state.class_components = [
                            comp for comp in st.session_state.class_components if comp['semester'] != sem_to_remove
                        ]
                        removed_comp_count = initial_comp_count - len(st.session_state.class_components)
                        if removed_comp_count > 0:
                             st.warning(f"Removed {removed_comp_count} class component(s) associated with {sem_to_remove}.")

                        st.success(f"Removed Semester: {sem_to_remove}")
                        st.session_state.schedule_df = None # Invalidate schedule
                        st.rerun()
                    else:
                        st.info("Select a semester to remove.")
        else:
            st.info("No semesters to manage.")


    with col2_sec:
        if st.session_state.semesters:
            with st.form("add_section_form_tab1", clear_on_submit=True):
                # Use a key dependent on the semesters list to ensure uniqueness when semesters change
                sel_sem_for_sec = st.selectbox("Select Semester*", st.session_state.semesters, key=f"add_sec_sel_sem_{'_'.join(st.session_state.semesters)}")
                new_sec_name = st.text_input(f"Add Section(s) to {sel_sem_for_sec} (comma-separated)*", placeholder="e.g., A, B1", key=f"new_sec_input_{sel_sem_for_sec}")
                if st.form_submit_button("Add Section"):
                    if sel_sem_for_sec and new_sec_name:
                        sections_to_add = [s.strip() for s in new_sec_name.split(',') if s.strip()]
                        if sections_to_add:
                             added_count = 0
                             for sec in sections_to_add:
                                if sec and sec not in st.session_state.sections.get(sel_sem_for_sec, []): # Check for non-empty section name
                                    st.session_state.sections.setdefault(sel_sem_for_sec, []).append(sec)
                                    added_count += 1
                             if added_count > 0:
                                st.success(f"Added {added_count} section(s) to {sel_sem_for_sec}.")
                                st.session_state.sections[sel_sem_for_sec].sort() # Keep sections sorted
                                st.session_state.schedule_df = None # Invalidate schedule
                                st.rerun()
                             else: st.info(f"No new unique sections entered for {sel_sem_for_sec}.")
                        else: st.warning("Enter section name(s).")
                    elif not new_sec_name: st.warning("Enter section name(s).")
        else:
            st.info("Add a semester first to be able to add sections.")

        st.subheader("Manage Sections")
        if any(st.session_state.sections.values()):
             # Use a key dependent on the sections structure to ensure uniqueness
             sections_structure_key = "_".join([f"{s}:{','.join(secs)}" for s, secs in st.session_state.sections.items()])
             sem_for_sec_remove = st.selectbox("Select Semester to manage sections", ["Select..."] + st.session_state.semesters, key=f"manage_sec_sel_sem_{sections_structure_key}")

             if sem_for_sec_remove != "Select..." and st.session_state.sections.get(sem_for_sec_remove):
                 current_sections = st.session_state.sections[sem_for_sec_remove]
                 with st.form(f"remove_section_form_tab1_{sem_for_sec_remove}", clear_on_submit=True):
                      secs_to_remove = st.multiselect(f"Select Section(s) to Remove from {sem_for_sec_remove}", current_sections, key=f"remove_sec_multi_{sem_for_sec_remove}_{sections_structure_key}")
                      if st.form_submit_button(f"Remove Selected Section(s) from {sem_for_sec_remove}"):
                          if secs_to_remove:
                              removed_count = 0
                              components_to_keep = []
                              removed_comp_count = 0

                              for sec_to_remove in secs_to_remove:
                                  if sec_to_remove in st.session_state.sections[sem_for_sec_remove]:
                                      st.session_state.sections[sem_for_sec_remove].remove(sec_to_remove)
                                      removed_count += 1

                              # Process components: remove the section from their list, remove component if list becomes empty
                              initial_comp_count = len(st.session_state.class_components)
                              processed_components = []
                              for comp in st.session_state.class_components:
                                   # Check if component belongs to the semester where sections were removed
                                   if comp['semester'] == sem_for_sec_remove:
                                       # Remove the selected sections from this component's sections list
                                       updated_sections = [sec for sec in comp['sections'] if sec not in secs_to_remove]
                                       if updated_sections:
                                           comp['sections'] = updated_sections
                                           processed_components.append(comp)
                                       else:
                                            # Component sections list became empty after removal
                                            st.warning(f"Removed component '{comp['component_title']}' ({comp['course_code']}) as all its assigned sections ({comp['sections']}) from {sem_for_sec_remove} were removed.")
                                            removed_comp_count += 1 # Count components removed this way
                                   else:
                                       # Component belongs to a different semester, keep it as is
                                       processed_components.append(comp)

                              st.session_state.class_components = processed_components


                              if removed_count > 0:
                                  st.success(f"Removed {removed_count} section(s) from {sem_for_sec_remove}.")
                                  if removed_comp_count > 0:
                                        st.warning(f"Also automatically removed {removed_comp_count} class component(s) that no longer had assigned sections in {sem_for_sec_remove}.")

                                  st.session_state.schedule_df = None # Invalidate schedule
                                  st.rerun()
                              else:
                                  st.info("No selected sections were found to remove from this semester.")
                          else:
                              st.info("Select sections to remove.")

        else:
             st.info("No sections defined to manage.")


    st.subheader("Current Sections per Semester:")
    # Display sections grouped by semester
    if any(st.session_state.sections.values()):
        for semester, sections in st.session_state.sections.items():
            st.write(f"**{semester}:** {', '.join(sections) or 'No sections defined'}")
    else:
        st.info("No sections defined.")

with tab2:
    st.header("➕ Add Class Component")
    if not st.session_state.semesters:
        st.warning("Add at least one semester in 'Semesters & Sections' tab first.")
    else:
        with st.form("add_class_component_form_tab2", clear_on_submit=True):
            st.subheader("Component Details")
            cc_code = st.text_input("Course Code*", placeholder="e.g., CSE101")
            cc_title = st.text_input("Component Title*", placeholder="e.g., Intro to Programming Lecture / IP Lab Group A")

            # Key depends on available semesters
            cc_semester = st.selectbox("Semester*", st.session_state.semesters, key=f"cc_sem_key_tab2_{'_'.join(st.session_state.semesters)}")

            sections_for_sem = st.session_state.sections.get(cc_semester, [])
            if not sections_for_sem:
                st.warning(f"No sections defined for semester '{cc_semester}'. Add them in Tab 1.")
                # Key depends on selected semester and whether it's disabled
                cc_sections = st.multiselect("Applicable Section(s)*", [], disabled=True, key=f"cc_sec_multi_dis_key_tab2_{cc_semester}")
            else:
                # Key depends on selected semester and available sections
                cc_sections = st.multiselect("Applicable Section(s)*", sections_for_sem, default=sections_for_sem, key=f"cc_sec_multi_ena_key_tab2_{cc_semester}_{'_'.join(sections_for_sem)}")

            # Key depends on component type
            cc_type = st.radio("Class Type*", ["Theory", "Lab"], key="cc_type_radio_tab2", horizontal=True)

            assigned_room_option = None # Initialize outside the if blocks

            if cc_type == "Lab":
                # Key depends on number of labs and component type
                lab_options = ["Any Available Lab"] + st.session_state.labs
                if not st.session_state.labs:
                   st.info("💡 Add specific lab rooms in the sidebar if needed, otherwise 'Any Available Lab' will be used by the generator.")
                   # If no labs are defined, force "Any Available Lab" selection visually and in state
                   assigned_room_option = st.selectbox("Assign Specific Lab Room (Optional)", ["Any Available Lab"], key=f"cc_lab_assign_key_tab2_disabled_{cc_type}", disabled=True, help="Add labs in sidebar to enable selection.")
                   assigned_room_option = "Any Available Lab" # Ensure value is set
                else:
                    # Labs are defined, show the enabled selectbox
                    assigned_room_option = st.selectbox("Assign Specific Lab Room (Optional)", lab_options, key=f"cc_lab_assign_key_tab2_enabled_{len(st.session_state.labs)}_{cc_type}")

            # For Theory, assigned_room_option remains None, which the generator knows means "Any Classroom"

            col_sessions, col_duration = st.columns(2)
            with col_sessions:
                cc_sessions_per_week = st.number_input("Sessions/Week*", min_value=1, value=1, step=1, key="cc_sessions_key_tab2")
            with col_duration:
                cc_duration_minutes = st.number_input("Duration/Session (min)*", min_value=10, value=50, step=5, key="cc_duration_key_tab2") # Min duration reasonable

            st.caption("* Required field")
            if st.form_submit_button("Add Class Component"):
                err = False
                if not cc_code: st.error("Course Code required."); err=True
                if not cc_title: st.error("Component Title required."); err=True
                if not cc_semester: st.error("Semester required."); err=True
                if not cc_sections: st.error("Select at least one section."); err=True
                 # Check if Labs are needed and none defined (and "Any Available Lab" was the only choice)
                if cc_type == "Lab" and assigned_room_option == "Any Available Lab" and not st.session_state.labs:
                    # This is a potential issue for the solver, warn but allow adding.
                    st.warning("You selected 'Any Available Lab' but no labs are defined in the sidebar. This component might not be scheduled properly by the placeholder.")

                if not err:
                    component_id = str(uuid.uuid4())
                    st.session_state.class_components.append({
                        "id": component_id, "course_code": cc_code, "component_title": cc_title,
                        "semester": cc_semester, "sections": cc_sections, "class_type": cc_type,
                        "sessions_per_week": cc_sessions_per_week, "duration_minutes": cc_duration_minutes,
                        "assigned_room": assigned_room_option if cc_type == "Lab" else None
                    })
                    st.success(f"Added: {cc_title} ({cc_code}) for {cc_semester} sections {', '.join(cc_sections)}")
                    st.session_state.schedule_df = None # Invalidate schedule
                    st.rerun() # Rerun to clear form and update display

    st.divider()
    st.subheader("Current Class Components List")
    if st.session_state.class_components:
        # Use .copy() to avoid SettingWithCopyWarning when modifying the DataFrame for display
        df_components = pd.DataFrame(st.session_state.class_components).copy()
        display_cols = ['course_code', 'component_title', 'semester', 'sections', 'class_type', 'sessions_per_week', 'duration_minutes', 'assigned_room']
        df_components_display = df_components[[col for col in display_cols if col in df_components.columns]].copy() # Ensure we work on a copy

        # Use .loc to modify the 'sections' column safely
        if 'sections' in df_components_display.columns:
             df_components_display.loc[:, 'sections'] = df_components_display['sections'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
        # Replace None in assigned_room with a user-friendly string for display
        if 'assigned_room' in df_components_display.columns:
             df_components_display.loc[:, 'assigned_room'] = df_components_display['assigned_room'].fillna('Any Classroom')

        st.dataframe(df_components_display, use_container_width=True, hide_index=True)

        if st.checkbox("Show options to remove components", key="show_remove_comp_cb"):
            if st.session_state.class_components: # Only show if list is not empty
                comp_options_for_removal = {
                    f"{comp['component_title']} ({comp['course_code']}) - {', '.join(comp['sections'])} ({comp['semester']})": comp['id']
                    for comp in st.session_state.class_components
                }
                # Add a placeholder option
                comp_display_name_to_remove = st.selectbox(
                    "Select component to remove",
                    options=["Select component to remove..."] + list(comp_options_for_removal.keys()),
                    key=f"remove_comp_select_key_{len(st.session_state.class_components)}" # Key depends on number of components
                )

                if comp_display_name_to_remove != "Select component to remove...":
                    comp_id_to_remove_val = comp_options_for_removal[comp_display_name_to_remove]
                    # Use a unique key for the button based on the component ID
                    if st.button(f"Confirm Remove: {comp_display_name_to_remove.split(' - ')[0]}", type="primary", key=f"confirm_remove_btn_{comp_id_to_remove_val}"):
                        # Filter out the component with the matching ID
                        st.session_state.class_components = [
                            comp for comp in st.session_state.class_components if comp['id'] != comp_id_to_remove_val
                        ]
                        st.success("Component removed.")
                        st.session_state.schedule_df = None # Invalidate schedule
                        st.rerun() # Rerun to update the list

            else:
                st.info("No components to remove.")

    else: st.info("No class components added yet.")

with tab3:
    st.header("📅 Generate Routine")
    ready_to_generate = True

    # More specific checks for disabling generation button and providing warnings
    warning_messages_for_generation = []
    if not st.session_state.class_components:
        warning_messages_for_generation.append("No Class Components added.")
        ready_to_generate = False
    if not st.session_state.working_days_config:
        warning_messages_for_generation.append("No Working Days selected in sidebar.")
        ready_to_generate = False

    # Check if rooms are needed and available based on *added components*
    needs_theory_room = any(c['class_type'] == "Theory" for c in st.session_state.class_components)
    needs_lab_room_any = any(c['class_type'] == "Lab" and c.get('assigned_room') == "Any Available Lab" for c in st.session_state.class_components)
    # We assume specifically assigned labs exist or will be handled by the user/solver

    if needs_theory_room and not st.session_state.classrooms:
        warning_messages_for_generation.append("Theory components require classrooms, but none defined in sidebar.")
        ready_to_generate = False
    if needs_lab_room_any and not st.session_state.labs:
        warning_messages_for_generation.append("Lab components need 'Any Available Lab', but no general Lab rooms defined in sidebar.")
        ready_to_generate = False
    # Note: If specific labs are assigned, we assume they exist. No check is made if the assigned_room string matches a defined lab.

    if warning_messages_for_generation:
        for msg in warning_messages_for_generation:
            st.warning(msg)
        st.warning("Please resolve the above issues before generating the routine.")


    if st.button("🚀 Create Routine", disabled=not ready_to_generate, type="primary"):
        with st.spinner("⏳ Generating (placeholder logic)..."):
            st.session_state.schedule_df = generate_schedule_from_components(
                st.session_state.class_components, st.session_state.classrooms, st.session_state.labs,
                st.session_state.working_days_config, st.session_state.start_time_config, st.session_state.end_time_config
            )
            if st.session_state.schedule_df is not None and not st.session_state.schedule_df.empty:
                 st.success("✅ Routine Generated (using placeholder logic). Please review carefully for conflicts!")


    st.subheader("Generated Routine Display (Grouped by Semester)")

    if st.session_state.schedule_df is not None and not st.session_state.schedule_df.empty:
        # Use .copy() for the display DataFrame to avoid SettingWithCopyWarning
        df_display = st.session_state.schedule_df.copy()

        # Ensure sorting columns exist
        required_cols = ['Day', 'Start_Minute', 'Semester', 'Section', 'Time Slot']
        if not all(col in df_display.columns for col in required_cols):
             st.error(f"Schedule data missing critical columns for display: {', '.join([col for col in required_cols if col not in df_display.columns])}")
        else:
            # Sort data by Semester, Day, Start Time
            day_order_map = {day: i for i, day in enumerate(st.session_state.working_days_config)}
            df_display['Day_Order'] = df_display['Day'].map(day_order_map).fillna(len(day_order_map))
            df_display = df_display.sort_values(by=['Semester', 'Day_Order', 'Start_Minute', 'Section']).reset_index(drop=True)
            df_display = df_display.drop(columns=['Day_Order'], errors='ignore') # Drop helper column

            # Get unique time slots and sections for table columns/rows
            # Sort time slots chronologically
            unique_time_slots = sorted(df_display['Time Slot'].unique(), key=lambda ts: parse_time_slot(ts)[0])

            # Get all unique sections that appear in the schedule
            all_scheduled_sections = sorted(df_display['Section'].unique())

            # Group by Semester for separate tables
            for semester_val, sem_group in df_display.groupby('Semester', sort=False):
                st.markdown(f"## Semester: {semester_val}") # Use a larger header for Semester

                # Create the table structure for this semester
                # Rows will be (Day, Time Slot), Columns will be Sections
                # We need a list of dicts where keys are 'Day', 'Time Slot', and Section names
                semester_table_data = []

                # Get unique days for this semester's data, sorted by working day order
                unique_days_in_sem = sem_group['Day'].unique()
                sorted_unique_days_in_sem = sorted(unique_days_in_sem, key=lambda day: day_order_map.get(day, len(day_order_map)))


                for day_val in sorted_unique_days_in_sem:
                    # Get unique time slots for this specific day within the semester
                    unique_time_slots_on_day = sorted(sem_group[sem_group['Day'] == day_val]['Time Slot'].unique(), key=lambda ts: parse_time_slot(ts)[0])

                    for time_slot_val in unique_time_slots_on_day:
                         # Create a row for this Day and Time Slot
                         row_data = {'Day': day_val, 'Time Slot': time_slot_val}

                         # Add data for each section
                         for section_val in all_scheduled_sections:
                              # Find the class entry for this specific Day, Time Slot, Semester, and Section
                              class_entry = sem_group[
                                  (sem_group['Day'] == day_val) &
                                  (sem_group['Time Slot'] == time_slot_val) &
                                  (sem_group['Section'] == section_val)
                              ]

                              if not class_entry.empty:
                                  # Assuming only one entry per (Day, Time Slot, Section) - placeholder might violate this!
                                  entry = class_entry.iloc[0]
                                  # Format the cell content
                                  row_data[section_val] = f"{entry['Course Code']} - {entry['Component Title']} ({entry['Room/Lab']})"
                              else:
                                  row_data[section_val] = "" # Empty cell if no class scheduled

                         semester_table_data.append(row_data)

                # Convert to DataFrame for display
                # Ensure columns are in desired order: Day, Time Slot, then Sections alphabetically
                display_cols_sem_table = ['Day', 'Time Slot'] + all_scheduled_sections
                df_semester_table = pd.DataFrame(semester_table_data, columns=display_cols_sem_table)

                st.dataframe(df_semester_table, hide_index=True, use_container_width=True)
                st.markdown("---") # Separator after each semester table


    elif st.session_state.schedule_df is not None:
        st.info("Generated schedule is empty. Please check inputs or placeholder logic.")
    else:
        st.info("Click 'Create Routine' after adding all necessary data. Results appear here.")

    if st.session_state.schedule_df is not None and not st.session_state.schedule_df.empty:
        st.markdown("### Download Full Routine (Flat Table)")
        # Use .copy() for the download DataFrame
        download_df_flat = st.session_state.schedule_df.copy()
        # Consistent sorting for download (same as display sorting)
        required_cols = ['Day', 'Start_Minute', 'Semester', 'Section']
        if all(col in download_df_flat.columns for col in required_cols):
            day_order_map_dl = {day: i for i, day in enumerate(st.session_state.working_days_config)}
            download_df_flat['Day_Order_DL'] = download_df_flat['Day'].map(day_order_map_dl).fillna(len(day_order_map_dl))
            download_df_flat = download_df_flat.sort_values(by=['Semester', 'Day_Order_DL', 'Start_Minute', 'Section'])
            download_df_flat = download_df_flat.drop(columns=['Day_Order_DL'], errors='ignore')
            # Drop internal columns not needed for download
            download_df_flat = download_df_flat.drop(columns=['Component_ID', 'Start_Minute', 'End_Minute'], errors='ignore')
            # Replace None in assigned_room with a user-friendly string for download
            if 'Room/Lab' in download_df_flat.columns:
                 download_df_flat.loc[:, 'Room/Lab'] = download_df_flat['Room/Lab'].fillna('Any Classroom')


            @st.cache_data # Cache the CSV conversion
            def convert_df_to_csv(df_to_convert_csv):
               return df_to_convert_csv.to_csv(index=False).encode('utf-8')

            csv_data_download = convert_df_to_csv(download_df_flat)
            st.download_button(label="Download Routine as CSV", data=csv_data_download,
                             file_name=f'university_routine_{datetime.date.today().strftime("%Y%m%d_%H%M%S")}.csv',
                             mime='text/csv')
        else:
             st.warning("Cannot generate download file: Schedule data is incomplete.")
