import streamlit as st
import sql

data = sql.Contacts.get_contacts_as_dataframe()
if not data.empty:
    data.columns = ["Имя", "email", "Телефон", "Последнее взаимодействие", "Круг"]
st.write(data)


@st.dialog("Добавление контакта")
def add_contact():
    c_list = sql.Contacts.get_contacts_list()
    circle_name = st.selectbox("Круг", sql.Circles.get_circles_list(), index=None)
    contact_name = st.text_input("Имя контакта")
    email = st.text_input("email")
    phone = st.text_input("Номер телефона")
    last_interaction = st.date_input("Дата последнего взаимодействия")
    if st.button("Добавить"):
        if circle_name is None:
            st.error("Выберите круг")
        elif contact_name == "":
            st.error("Введите имя контакта")
        elif contact_name in c_list:
            st.error("Контакт с таким именем уже существует в базе")
        else:
            sql.Contacts.add_contact(circle_name,
                                     contact_name=contact_name,
                                     email=email,
                                     phone=phone,
                                     last_interaction=last_interaction)
            st.rerun()


@st.dialog("Редактирование контакта")
def edit_contact():
    contacts = sql.Contacts.get_contacts_as_dataframe()
    c_list = contacts["contact_name"].tolist()
    contact_name = st.selectbox("Контакт", c_list, index=None)
    if contact_name:
        contact_data = contacts[contacts["contact_name"] == contact_name].reset_index()
        name = contact_data["contact_name"][0]
        email = contact_data["email"][0]
        phone = contact_data["phone"][0]
        last_interaction = contact_data["last_interaction"][0]
        circle_name = contact_data["circle_name"][0]

        new_name = st.text_input("Имя", name)
        new_email = st.text_input("email", email)
        new_phone = st.text_input("Телефон", phone)
        new_interaction = st.date_input("Дата взаимодействия", last_interaction)
        new_circle_name = st.selectbox("Круг", sql.Circles.get_circles_list())

        name_changed = new_name != name
        email_changed = new_email != email
        phone_changed = new_phone != phone
        interaction_changed = new_interaction != last_interaction
        circle_changed = new_circle_name != circle_name

        something_changed = any([name_changed, email_changed, phone_changed, interaction_changed, circle_changed])

        if st.button("Редактировать контакт", disabled=not something_changed):
            sql.Contacts.edit_contact(name, new_circle_name,
                                      contact_name=new_name,
                                      email=new_email,
                                      phone=new_phone,
                                      last_interaction=new_interaction)
            st.rerun()


@st.dialog("Удаление контакта")
def delete_contact():
    name = st.selectbox("Контакт", sql.Contacts.get_contacts_list(), index=None)
    if name:
        if st.button("Удалить контакт"):
            sql.Contacts.delete_contact(name)
            st.rerun()


col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        if st.button("Добавить контакт", use_container_width=True):
            add_contact()
        if st.button("Редактировать контакт", use_container_width=True):
            edit_contact()
        if st.button("Удалить контакт", use_container_width=True):
            delete_contact()
