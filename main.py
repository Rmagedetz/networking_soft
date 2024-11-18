import streamlit as st
import sql

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


def login():
    with st.form("login_form", clear_on_submit=True):
        st.title("Вход в приложение")
        user_input = st.text_input("Введите логин")
        password_input = st.text_input("Введите пароль", type="password")
        submit = st.form_submit_button("Войти")

        if submit:
            if user_input in sql.User.get_user_list():
                if password_input == sql.User.check_user_password(user_input):
                    st.session_state.logged_in = True
                    st.session_state.user = user_input
                    st.rerun()
                else:
                    st.error("Неверный логин или пароль")
            else:
                st.error("Неверный логин или пароль")


def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None
    st.rerun()


login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Выйти", icon=":material/logout:")

main_page = st.Page("pages/main_page.py", title="Главная", icon=":material/home:", default=True)
circles_page = st.Page("pages/circles_page.py", title="Круги", icon=":material/settings_accessibility:")
contacts_page = st.Page("pages/contacts_page.py", title="Контакты", icon=":material/contacts:")
tasks_page = st.Page("pages/tasks.py", title="Задачи", icon=":material/add_task:")
connections_page = st.Page("pages/connections.py", title="Связи", icon=":material/share:")
interactions_page = st.Page("pages/interactions_page.py", title="Взаимодействия", icon=":material/handshake:")

if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Логин": [logout_page],
            "Страницы": [main_page, circles_page, contacts_page, tasks_page, connections_page, interactions_page]
        }
    )
else:
    pg = st.navigation([login_page])

pg.run()
