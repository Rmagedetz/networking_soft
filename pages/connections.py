import streamlit as st
import sql


@st.dialog("Добавление связи")
def add_connection():
    cont1 = st.session_state.contact_1
    c_list = sql.Contacts.get_contacts_list()
    c_list.remove(cont1)
    cont2 = st.selectbox("name1", c_list, key="c2", index=None)
    desc = st.text_input("desc")
    if st.button("add"):
        sql.Connections.add_connection(cont1, cont2, desc)
        st.rerun()


contact = st.selectbox("Контакт", sql.Contacts.get_contacts_list(), index=None)
if contact:
    connections = sql.Connections.get_connections_for_contact(contact)
    if not connections.empty:
        st.write(connections)
    if st.button("Добавить связь", key="Conn"):
        st.session_state.contact_1 = contact
        add_connection()
# data = sql.Connections.get_connections_as_dataframe()
# st.write(data)
# cont1 = st.selectbox("name1", sql.Contacts.get_contacts_list(), key="c1", index=None)
# cont2 = st.selectbox("name1", sql.Contacts.get_contacts_list(), key="c2", index=None)
# desc = st.text_input("desc")

# if cont1:
#     data = sql.Connections.get_connections_for_contact(cont1)
#     st.write(data)