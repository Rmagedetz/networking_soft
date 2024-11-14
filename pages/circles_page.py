import streamlit as st
import sql

data = sql.Circles.get_circles_as_dataframe()
data.columns = ["Круг", "Частота взаимодействия (дн.)", "Контактов в круге"]
st.write(data)


@st.dialog("Добавление круга")
def add_circle():
    circle_name = st.text_input("Название")
    circle_freq = st.number_input("Частота взаимодействий (дн)", min_value=0, step=1)
    if st.button("Добавить круг", key="add_circle_accept"):
        if circle_name in sql.Circles.get_circles_list():
            st.error("Круг с таким названием уже создан")
        else:
            sql.Circles.add_circle(circle_name=circle_name,
                                   interaction_frequency=circle_freq)
            st.rerun()


@st.dialog("Редактирование кругов")
def edit_circle():
    circles = sql.Circles.get_circles_as_dataframe_simple()
    c_list = circles["circle_name"].tolist()
    circle_name = st.selectbox("Круг", circles, index=None)
    if circle_name:
        new_name = st.text_input("Название круга", circle_name)
        value = circles[circles["circle_name"] == circle_name].reset_index()["interaction_frequency"][0]
        new_freq = st.number_input("Частота взаимодействий", value=value, step=1, min_value=0)
        name_changed = new_name != circle_name
        freq_changed = new_freq != value
        if st.button("Изменить", disabled=not (name_changed or freq_changed)):
            if name_changed and new_name in c_list:
                st.error("Круг с таким именем уже существует")
            else:
                sql.Circles.edit_circle(circle_name,
                                        circle_name=new_name,
                                        interaction_frequency=new_freq)
                st.rerun()


@st.dialog("Удаление круга")
def delete_circle():
    circle = st.selectbox("Круг", sql.Circles.get_circles_list(), index=None)
    if circle:
        if st.button("Удалить круг", key="circle_delete_accept"):
            try:
                sql.Circles.delete_circle(circle)
            except:
                st.error("Круг нельзя удалить пока в нем есть контакты")
            else:
                st.rerun()


col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        if st.button("Добавить круг", key="add_circle", use_container_width=True):
            add_circle()
        if st.button("Редактировать круг", key="edit_circle", use_container_width=True):
            edit_circle()
        if st.button("Удалить круг", key="delete_circle", use_container_width=True):
            delete_circle()
