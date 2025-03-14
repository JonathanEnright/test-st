import streamlit as st

st.title("Hello World from streamlit!")

my_db_name = st.secrets("DB_USERNAME")

st.write(my_db_name)

st.balloons()
