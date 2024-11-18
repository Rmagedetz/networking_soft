import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sql


def get_today_tasks():
    today = datetime.today().date()
    tasks_df = sql.Task.get_tasks_as_dataframe()
    return tasks_df[tasks_df['due_date'] == today]


def get_upcoming_tasks():
    today = datetime.today().date()
    upcoming_tasks_df = sql.Task.get_tasks_as_dataframe()
    upcoming_tasks_df = upcoming_tasks_df[upcoming_tasks_df['due_date'] > today]
    return upcoming_tasks_df


def get_circle_stats():
    return sql.Circles.get_circle_stats()


def get_contacts_to_follow_up():
    contacts_df = sql.Contacts.get_contacts_as_dataframe()
    today = pd.to_datetime('today').date()
    contacts_df['last_interaction'] = pd.to_datetime(contacts_df['last_interaction']).dt.date
    return contacts_df[contacts_df['last_interaction'] < (today - timedelta(days=30))]


def get_circles_to_follow_up():
    circles_df = sql.Circles.get_circles_as_dataframe()
    today = pd.to_datetime('today').date()
    circles_to_follow_up = []

    for index, row in circles_df.iterrows():
        circle_name = row['circle_name']
        interaction_frequency = row['interaction_frequency']

        contacts_df = sql.Contacts.get_contacts_as_dataframe()
        contacts_in_circle = contacts_df[contacts_df['circle_name'] == circle_name]

        max_last_interaction = contacts_in_circle['last_interaction'].max()

        if pd.isna(max_last_interaction):
            circles_to_follow_up.append({
                "circle_name": circle_name,
                "last_interaction": None
            })
        else:
            if pd.to_datetime(max_last_interaction).date() < (today - timedelta(days=interaction_frequency)):
                circles_to_follow_up.append({
                    "circle_name": circle_name,
                    "last_interaction": max_last_interaction
                })

    return pd.DataFrame(circles_to_follow_up)


st.title("Главная страница для пользователя")

st.header("Задачи на сегодня")
today_tasks = get_today_tasks()
if not today_tasks.empty:
    today_tasks.columns = ["ID", "Задача", "Описание", "Создатель", "Исполнитель", "Дата создания", "Дата выполнения",
                           "Связаный контакт", "Статус"]
    st.write(today_tasks)
else:
    st.write("На сегодня нет задач.")

# Задачи на ближайший месяц
st.header("Задачи на ближайший месяц")
upcoming_tasks = get_upcoming_tasks()
if not upcoming_tasks.empty:
    upcoming_tasks.columns = ["ID", "Задача", "Описание", "Создатель", "Исполнитель", "Дата создания",
                              "Дата выполнения",
                              "Связаный контакт", "Статус"]
    st.write(upcoming_tasks)
else:
    st.write("Нет задач на ближайший месяц.")

# Статистика по взаимодействиям с кругами
st.header("Статистика по взаимодействиям с кругами")
circle_stats = get_circle_stats()
if not circle_stats.empty:
    circle_stats.columns = ["Круг", "Взаимодействий", "Дата последнего взаимодействия", "Контакты"]
    st.write(circle_stats)
else:
    st.write("Нет данных о кругах.")

# Контакты для follow-up
try:
    follow_up_contacts = get_contacts_to_follow_up()
    st.header("Контакты, с которыми давно не было взаимодействий")
    if not follow_up_contacts.empty:
        info = follow_up_contacts[['contact_name', 'last_interaction']].reset_index(drop=True)
        info.index += 1
        info.columns = ["Контакт", "Дата последнего взаимодействия"]
        st.write(info)
    else:
        st.write("Все контакты были недавно обновлены.")
except:
    pass

try:
    follow_up_circles = get_circles_to_follow_up()
    st.header("Круги, с которыми давно не было взаимодействий")
    if not follow_up_circles.empty:
        follow_up_circles.columns = ["Круг", "Дата последнего взаимодействия"]
        st.write(follow_up_circles)
    else:
        st.write("Все круги имеют недавние взаимодействия.")
except:
    pass
