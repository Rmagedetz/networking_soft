import streamlit as st
import sql
import datetime

username = st.session_state.user

tasks_in, tasks_out = st.tabs(["Входящие", "Исходящие"])

with tasks_in:
    data = sql.Task.get_incomplete_tasks_by_executor(username)
    if not data.empty:
        original_done = data['done'].copy()
        editor = st.data_editor(data,
                                column_config={"id": st.column_config.Column("ID", disabled=True),
                                               "task_name": st.column_config.Column("Задача", disabled=True),
                                               "description": st.column_config.Column("Описание", disabled=True),
                                               "due_date": st.column_config.DateColumn("Дата", disabled=True,
                                                                                       format="DD.MM.YYYY"),
                                               "contact_name": st.column_config.Column("Контакт", disabled=True),
                                               "creator_name": st.column_config.Column("Создатель", disabled=True),
                                               "done": st.column_config.CheckboxColumn("Выполнена")}, key="in")
        if not data.equals(editor):
            changed_rows = editor[editor['done'] != original_done]
            done = changed_rows[['id', 'done']]
            for _, task in done.iterrows():
                sql.Task.edit_task(task["id"], done=int(task["done"]))
                st.rerun()
with tasks_out:
    data = sql.Task.get_incomplete_tasks_by_creator(username)
    if not data.empty:
        original_done = data['done'].copy()
        editor = st.data_editor(data,
                                column_config={"id": st.column_config.Column("ID", disabled=True),
                                               "task_name": st.column_config.Column("Задача", disabled=True),
                                               "description": st.column_config.Column("Описание", disabled=True),
                                               "due_date": st.column_config.DateColumn("Дата", disabled=True,
                                                                                       format="DD.MM.YYYY"),
                                               "contact_name": st.column_config.Column("Контакт", disabled=True),
                                               "executor_name": st.column_config.Column("Исполнитель", disabled=True),
                                               "done": st.column_config.CheckboxColumn("Выполнена")}, key="out")
        if not data.equals(editor):
            changed_rows = editor[editor['done'] != original_done]
            done = changed_rows[['id', 'done']]
            for _, task in done.iterrows():
                sql.Task.edit_task(task["id"], done=int(task["done"]))
                st.rerun()


@st.dialog("Создание задачи")
def add_task():
    creator_name = username
    executor_name = st.selectbox("Исполнитель", sql.User.get_user_list(), index=None)
    contact_name = st.selectbox("Связанный контакт", sql.Contacts.get_contacts_list(), index=None)
    task_name = st.text_input("Название задачи")
    description = st.text_area("Описание задачи")
    today = datetime.date.today()
    date = st.date_input("Дата выполнения", min_value=today, value=None)

    if st.button("Добавить задачу"):
        if not executor_name:
            st.error("Выберите исполнителя")
        elif not contact_name:
            st.error("Выерите связанный контакт")
        elif task_name == "":
            st.error("Введите название задачи")
        elif not date:
            st.error("Введите дату исполения задачи")

        else:
            sql.Task.add_task(creator_name, executor_name, contact_name, task_name, description, date)
            st.rerun()


@st.dialog("Редактировать задачу")
def edit_task():
    tasks = sql.Task.get_incomplete_tasks_by_creator(username)
    ids = tasks["id"].tolist()
    id_selected = st.selectbox("ID задачи", ids, index=None)
    if id_selected:
        task_data = tasks[tasks["id"] == id_selected].reset_index(drop=True)

        task_name = task_data["task_name"][0]
        description = task_data["description"][0]
        due_date = task_data["due_date"][0]
        contact_name = task_data["contact_name"][0]
        executor_name = task_data["executor_name"][0]

        new_name = st.text_input("Название задачи", task_name)
        new_description = st.text_area("Описание", description)
        new_date = st.date_input("Дата выполнения", value=due_date)
        c_list = sql.Contacts.get_contacts_list()
        new_contact_name = st.selectbox("Контакт", c_list, index=c_list.index(contact_name))
        ex_list = sql.User.get_user_list()
        new_executor_name = st.selectbox("Исполнитель", ex_list, index=ex_list.index(executor_name))

        if new_contact_name:
            idx = sql.Contacts.get_contact_by_name(new_contact_name)

        if new_executor_name:
            exec_idx = sql.User.get_user_id_by_name(new_executor_name)

        name_changed = new_name != task_name
        desc_changed = new_description != description
        date_changed = new_date != due_date
        contact_changed = new_contact_name != contact_name
        executor_changed = new_executor_name != executor_name

        something_changed = any([name_changed, desc_changed, date_changed, contact_changed, executor_changed])

        if st.button("Редактировать задачу", disabled=not something_changed):
            sql.Task.edit_task(id_selected,
                               task_name=new_name,
                               description=new_description,
                               due_date=new_date,
                               contact_id=idx,
                               executor_id=exec_idx)
            st.rerun()


@st.dialog("Удалить задачу")
def delete_task():
    tasks = sql.Task.get_incomplete_tasks_by_creator(username)
    ids = tasks["id"].tolist()
    id_selected = st.selectbox("ID задачи", ids, index=None)
    if id_selected:
        task_data = tasks[tasks["id"] == id_selected].reset_index(drop=True)

        task_name = task_data["task_name"][0]
        description = task_data["description"][0]
        due_date = task_data["due_date"][0]
        contact_name = task_data["contact_name"][0]

        st.write(task_name)
        st.write(description)
        st.write(due_date)
        st.write(contact_name)

        if st.button("Удалить задачу"):
            sql.Task.delete_task(id_selected)
            st.rerun()


col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        if st.button("Создать задачу", key="add_task", use_container_width=True):
            add_task()
        if st.button("Редактировать задачу", key="edit_task", use_container_width=True):
            edit_task()
        if st.button("Удалить задачу", key="delete_task", use_container_width=True):
            delete_task()
