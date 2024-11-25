import streamlit as st
import sql

data = sql.Contacts.get_contacts_as_dataframe()
if not data.empty:
    data.columns = ["Имя", "email", "Телефон", "ДР", "Хобби", "Доп инфо", "Последнее взаимодействие", "Круг"]
st.write(data)


@st.dialog("Добавление контакта")
def add_contact():
    c_list = sql.Contacts.get_contacts_list()
    circle_name = st.selectbox("Круг", sql.Circles.get_circles_list(), index=None)
    contact_name = st.text_input("Имя контакта")
    email = st.text_input("email")
    phone = st.text_input("Номер телефона")
    hobbies = st.text_input("Хобби")
    birthday = st.date_input("День рождения")
    last_interaction = st.date_input("Дата последнего взаимодействия")
    additional = st.text_area("Доп. инфо")
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
                                     birthday=birthday,
                                     last_interaction=last_interaction,
                                     hobbies=hobbies,
                                     additional=additional)
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
        birthday = contact_data["birthday"][0]
        hobbies = contact_data["hobbies"][0]
        additional = contact_data["additional"][0]
        last_interaction = contact_data["last_interaction"][0]
        circle_name = contact_data["circle_name"][0]

        new_name = st.text_input("Имя", name)
        new_email = st.text_input("email", email)
        new_phone = st.text_input("Телефон", phone)
        new_birthday = st.date_input("День рождения", birthday)
        new_hobbies = st.text_input("Хобби", hobbies)
        new_additional = st.text_area("Доп. инфо", additional)
        new_interaction = st.date_input("Дата взаимодействия", last_interaction)
        new_circle_name = st.selectbox("Круг", sql.Circles.get_circles_list())

        name_changed = new_name != name
        email_changed = new_email != email
        phone_changed = new_phone != phone
        interaction_changed = new_interaction != last_interaction
        circle_changed = new_circle_name != circle_name
        birthday_changed = new_birthday != birthday
        hobbies_changed = new_hobbies != hobbies
        additional_changed = new_additional != additional

        something_changed = any([name_changed, email_changed, phone_changed, interaction_changed, circle_changed,
                                 birthday_changed, hobbies_changed, additional_changed])

        if st.button("Редактировать контакт", disabled=not something_changed):
            sql.Contacts.edit_contact(name, new_circle_name,
                                      contact_name=new_name,
                                      email=new_email,
                                      phone=new_phone,
                                      last_interaction=new_interaction,
                                      birthday=new_birthday,
                                      additional=new_additional,
                                      hobbies=new_hobbies)
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
