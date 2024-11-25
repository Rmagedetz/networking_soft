import streamlit as st
import sql

data = sql.ImportantDates.get_important_dates_dataframe()
st.write(data)


@st.dialog("Добавить дату")
def add_date():
    contact_selector = st.selectbox("Контакт", sql.Contacts.get_contacts_list())
    date = st.date_input("Дата")
    desc = st.text_input("Расшифровка")

    if st.button("Добавить", key="add_date_accept"):
        sql.ImportantDates.add_date_for_contact(contact_name=contact_selector,
                                                date=date,
                                                description=desc)
        st.rerun()

if st.button("Добавить дату"):
    add_date()
