import streamlit as st

if 'sidebar_expanded' not in st.session_state:
    st.session_state.sidebar_expanded = True

width = 250 if st.session_state.sidebar_expanded else 80

st.markdown(f"""
<style>
[data-testid="stSidebar"] {{
    min-width: {width}px !important;
    max-width: {width}px !important;
    transition: all 0.3s;
}}
[data-testid="collapsedControl"] {{
    display: none !important;
}}
</style>
""", unsafe_allow_html=True)

if st.sidebar.button("☰ Toggle", key="toggle"):
    st.session_state.sidebar_expanded = not st.session_state.sidebar_expanded
    st.rerun()

if st.session_state.sidebar_expanded:
    st.sidebar.markdown("### Expanded View")
    st.sidebar.button("🗂️ All Articles")
    st.sidebar.button("✔️ Logs")
    st.sidebar.button("⚙️ Admin")
else:
    st.sidebar.button("🗂️")
    st.sidebar.button("✔️")
    st.sidebar.button("⚙️")

st.title("Main Content")
st.write(f"Sidebar is {'Expanded' if st.session_state.sidebar_expanded else 'Collapsed'}")
