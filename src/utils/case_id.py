from datetime import datetime
import streamlit as st

def generate_case_id():
    today_str = datetime.now().strftime("%Y%m%d")
    todays_cases = [
        cid for cid in st.session_state.generated_case_ids
        if cid.startswith(today_str)
    ]
    next_number = len(todays_cases) + 1
    case_id = f"{today_str}-{next_number:03d}"
    st.session_state.generated_case_ids.append(case_id)
    return case_id
