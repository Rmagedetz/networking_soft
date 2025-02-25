import streamlit as st
import sql

data = sql.Interaction.get_as_dataframe()
data.columns = ["ID", "Пользователь", "Контакт", "Дата", "Тип контакта", "Описание"]
st.write(data)


@st.dialog("Добавить взаимодействие")
def add_interaction():
    username = st.session_state.user
    contact = st.selectbox("Контакт", sql.Contacts.get_contacts_list())
    interaction_type = st.text_input("Взаимодействие")
    text = st.text_area("Описание")
    if st.button("Добавить", key="add"):
        sql.Interaction.add_interaction(
            user_name=username,
            contact_name=contact,
            interaction_type=interaction_type,
            notes=text,
        )
        st.rerun()


@st.dialog("Редактировать взаимодействие")
def edit_interaction():
    username = st.session_state.user
    int_data = sql.Interaction.get_as_dataframe()
    int_data = int_data[int_data["user_name"] == username]
    int_list = int_data["id"].tolist()
    int_id = st.selectbox("ID", int_list)
    if int_id:
        int_data = int_data[int_data["id"] == int_id].reset_index()
        contact_name = int_data["contact_name"][0]
        interaction_date = int_data["interaction_date"][0]
        interaction_type = int_data["interaction_type"][0]
        notes = int_data["notes"][0]

        c_list = sql.Contacts.get_contacts_list()
        new_contact_name = st.selectbox("Контакт", c_list, index=c_list.index(contact_name))
        new_date = st.date_input("Дата выполнения", value=interaction_date)
        new_interaction_type = st.text_input("Взаимодействие", interaction_type)
        new_notes = st.text_area("Описание", notes)

        contact_changed = new_contact_name != contact_name
        date_changed = new_date != interaction_date
        int_changed = new_interaction_type != interaction_type
        notes_changed = new_notes != notes

        something_changed = any([contact_changed, date_changed, int_changed, notes_changed])

        if st.button("Редактировать взаимодействие", disabled=not something_changed, key="sd"):
            sql.Interaction.edit_interaction(int_id, new_contact_name,
                                             interaction_type=new_interaction_type,
                                             notes=new_notes,
                                             interaction_date=new_date
                                             )
            st.rerun()


@st.dialog("Удалить взаимодействие")
def delete_interaction():
    username = st.session_state.user
    int_data = sql.Interaction.get_as_dataframe()
    int_data = int_data[int_data["user_name"] == username]
    int_list = int_data["id"].tolist()
    int_id = st.selectbox("ID", int_list)
    if int_id:
        int_data = int_data[int_data["id"] == int_id].reset_index()
        contact_name = int_data["contact_name"][0]
        interaction_date = int_data["interaction_date"][0]
        interaction_type = int_data["interaction_type"][0]
        notes = int_data["notes"][0]

        st.write(contact_name)
        st.write(interaction_date)
        st.write(interaction_type)
        st.write(notes)

        if st.button("Удалить", key="del"):
            sql.Interaction.delete_interaction(int_id)
            st.rerun()


col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        if st.button("Добавить взаимодействие", use_container_width=True):
            add_interaction()
        if st.button("Редактировать взаимодействие", use_container_width=True):
            edit_interaction()
        if st.button("Удалить взаимодействие", use_container_width=True):
            delete_interaction()
