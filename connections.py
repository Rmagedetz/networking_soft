import streamlit as st

sql_connection_string = ("mysql+pymysql://{}:{}@{}:{}/{}".format
                         (st.secrets["database_connection"]["user"],
                          st.secrets["database_connection"]["password"],
                          st.secrets["database_connection"]["host"],
                          st.secrets["database_connection"]["port"],
                          st.secrets["database_connection"]["database_name"]))