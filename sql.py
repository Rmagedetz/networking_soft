import pandas as pd
from sqlalchemy import Column, Integer, String, Date, Float, create_engine, ForeignKey, func, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, aliased
from sqlalchemy.exc import IntegrityError
from contextlib import contextmanager
from connections import sql_connection_string

engine = create_engine(sql_connection_string)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_list(cls, field_name):
    with session_scope() as session:
        field = getattr(cls, field_name)
        results = session.query(field).all()
        result_list = [getattr(result, field_name) for result in results]
    return result_list


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)

    @classmethod
    def get_user_list(cls):
        return get_list(cls, "user_name")

    @classmethod
    def check_user_password(cls, username):
        with session_scope() as session:
            result = session.query(cls.password).filter(cls.user_name == username).first()
            return result[0] if result else None


class Circles(Base):
    __tablename__ = "circles"
    circle_id = Column(Integer, primary_key=True)
    circle_name = Column(String(100), nullable=False)
    interaction_frequency = Column(Integer, nullable=False)

    contacts = relationship("Contacts", back_populates="circle")

    @classmethod
    def get_circles_list(cls):
        return get_list(cls, "circle_name")

    @classmethod
    def get_circles_as_dataframe_simple(cls):
        with session_scope() as session:
            result = session.query(
                cls.circle_name,
                cls.interaction_frequency
            ).all()
        df = pd.DataFrame(result)
        df.index += 1
        return df

    @classmethod
    def get_circles_as_dataframe(cls):
        with session_scope() as session:
            result = session.query(
                cls.circle_name,
                cls.interaction_frequency,
                func.count(Contacts.contact_id).label("contact_count")
            ).outerjoin(Contacts, Contacts.circle_id == cls.circle_id).group_by(cls.circle_name,
                                                                                cls.interaction_frequency)

            result_data = result.all()

            df = pd.DataFrame(result_data, columns=["circle_name", "interaction_frequency", "contact_count"])
            df.index += 1

        return df

    @classmethod
    def add_circle(cls, **parameters):
        with session_scope() as session:
            add = cls(**parameters)
            session.add(add)
            session.commit()

    @classmethod
    def edit_circle(cls, old_name, **parameters):
        with session_scope() as session:
            record = session.query(cls).filter_by(circle_name=old_name).first()
            for field, value in parameters.items():
                if hasattr(record, field):
                    setattr(record, field, value)

    @classmethod
    def delete_circle(cls, circle_name):
        with session_scope() as session:
            contact = session.query(cls).filter_by(circle_name=circle_name).first()
            session.delete(contact)


class Contacts(Base):
    __tablename__ = "contacts"
    contact_id = Column(Integer, primary_key=True)
    contact_name = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(50))
    last_interaction = Column(Date)
    circle_id = Column(Integer, ForeignKey("circles.circle_id"), nullable=False)

    # Relationship with Circles
    circle = relationship("Circles", back_populates="contacts")

    @classmethod
    def get_contacts_list(cls):
        return get_list(cls, "contact_name")

    @classmethod
    def add_contact(cls, circle_name, **parameters):
        with session_scope() as session:
            circle = session.query(Circles).filter(Circles.circle_name == circle_name).first()
            try:
                add = cls(circle_id=circle.circle_id, **parameters)
                session.add(add)
            except:
                pass

    @classmethod
    def edit_contact(cls, old_name, circle_name, **parameters):
        with session_scope() as session:
            record = session.query(cls).filter_by(contact_name=old_name).first()
            circle = session.query(Circles).filter(Circles.circle_name == circle_name).first()
            record.circle_id = circle.circle_id
            for field, value in parameters.items():
                if hasattr(record, field):
                    setattr(record, field, value)

    @classmethod
    def get_contacts_as_dataframe(cls):
        with session_scope() as session:
            contacts = (
                session.query(cls.contact_name, cls.email, cls.phone, cls.last_interaction, Circles.circle_name)
                .join(Circles, cls.circle_id == Circles.circle_id)
                .all()
            )

            df = pd.DataFrame(contacts)
            df.index += 1
        return df

    @classmethod
    def delete_contact(cls, contact_name):
        with session_scope() as session:
            contact = session.query(cls).filter_by(contact_name=contact_name).first()
            session.delete(contact)

    @classmethod
    def get_contact_by_name(cls, contact_name):
        with session_scope() as session:
            contact = session.query(cls).filter(cls.contact_name == contact_name).first()
            return contact.contact_id


class Task(Base):
    __tablename__ = "tasks"
    task_id = Column(Integer, primary_key=True)
    task_name = Column(String(100), nullable=False)
    description = Column(String(255))
    creator_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    executor_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.contact_id"), nullable=False)
    created_at = Column(Date, default=func.current_date())
    due_date = Column(Date)
    done = Column(Boolean)

    # Relationships with Users and Contacts
    creator = relationship("User", foreign_keys=[creator_id])
    executor = relationship("User", foreign_keys=[executor_id])
    contact = relationship("Contacts")

    @classmethod
    def add_task(cls, creator_name, executor_name, contact_name, task_name, description, due_date, done=False):
        with session_scope() as session:
            creator = session.query(User).filter(User.user_name == creator_name).first()
            executor = session.query(User).filter(User.user_name == executor_name).first()
            contact = session.query(Contacts).filter(Contacts.contact_name == contact_name).first()
            if not creator or not executor or not contact:
                raise ValueError("Creator, Executor or Contact not found")

            task = cls(
                task_name=task_name,
                description=description,
                creator_id=creator.user_id,
                executor_id=executor.user_id,
                contact_id=contact.contact_id,
                due_date=due_date,
                done=done
            )
            session.add(task)
            session.commit()

    @classmethod
    def edit_task(cls, task_id, **parameters):
        with session_scope() as session:
            task = session.query(cls).filter_by(task_id=task_id).first()
            if not task:
                raise ValueError(f"Task with id {task_id} not found")

            for field, value in parameters.items():
                if hasattr(task, field):
                    setattr(task, field, value)
            session.commit()

    @classmethod
    def get_tasks_as_dataframe(cls):
        with session_scope() as session:
            creator = aliased(User, name="creator")
            executor = aliased(User, name="executor")

            tasks = session.query(
                cls.task_id,
                cls.task_name,
                cls.description,
                creator.user_name.label("creator_name"),
                executor.user_name.label("executor_name"),
                cls.created_at,
                cls.due_date,
                Contacts.contact_name.label("contact_name"),
                cls.done
            ).join(creator, cls.creator_id == creator.user_id) \
                .join(executor, cls.executor_id == executor.user_id) \
                .join(Contacts, cls.contact_id == Contacts.contact_id) \
                .all()

            df = pd.DataFrame(tasks,
                              columns=["id", "task_name", "description", "creator_name", "executor_name", "created_at",
                                       "due_date", "contact_name", "done"])
            df.index += 1
        return df

    @classmethod
    def get_incomplete_tasks_by_executor(cls, executor_name):
        with session_scope() as session:
            executor = session.query(User).filter(User.user_name == executor_name).first()
            if not executor:
                raise ValueError(f"User with name '{executor_name}' not found")

            tasks = session.query(
                cls.task_id,
                cls.task_name,
                cls.description,
                cls.due_date,
                Contacts.contact_name.label("contact_name")
            ).join(User, cls.executor_id == executor.user_id) \
                .join(Contacts, cls.contact_id == Contacts.contact_id) \
                .filter(cls.executor_id == executor.user_id, cls.done == False) \
                .all()

            df = pd.DataFrame(tasks,
                              columns=["id", "task_name", "description", "due_date", "contact_name"])
            df.index += 1
        return df

    @classmethod
    def get_incomplete_tasks_by_creator(cls, creator_name):
        with session_scope() as session:
            creator = session.query(User).filter(User.user_name == creator_name).first()
            if not creator:
                raise ValueError(f"User with name '{creator_name}' not found")

            tasks = session.query(
                cls.task_id,
                cls.task_name,
                cls.description,
                cls.due_date,
                Contacts.contact_name.label("contact_name")
            ).join(User, cls.creator_id == creator.user_id) \
                .join(Contacts, cls.contact_id == Contacts.contact_id) \
                .filter(cls.creator_id == creator.user_id, cls.done == False) \
                .all()

            df = pd.DataFrame(tasks,
                              columns=["id", "task_name", "description", "due_date", "contact_name"])
            df.index += 1
        return df

    @classmethod
    def delete_task(cls, task_id):
        with session_scope() as session:
            task = session.query(cls).filter_by(task_id=task_id).first()
            if task:
                session.delete(task)
                session.commit()


class Connections(Base):
    __tablename__ = "connections"

    connection_id = Column(Integer, primary_key=True)
    cont1_id = Column(Integer, ForeignKey("contacts.contact_id"), nullable=False)
    cont2_id = Column(Integer, ForeignKey("contacts.contact_id"), nullable=False)
    description = Column(String(255), nullable=False)

    # Связи с контактами
    contact1 = relationship("Contacts", foreign_keys=[cont1_id])
    contact2 = relationship("Contacts", foreign_keys=[cont2_id])
    @classmethod
    def add_connection(cls, contact1_name, contact2_name, description):
        with session_scope() as session:
            contact1 = session.query(Contacts).filter(Contacts.contact_name == contact1_name).first()
            contact2 = session.query(Contacts).filter(Contacts.contact_name == contact2_name).first()

            if not contact1 or not contact2:
                raise ValueError("Один или оба контакта не найдены")

            connection = cls(
                cont1_id=contact1.contact_id,
                cont2_id=contact2.contact_id,
                description=description
            )
            session.add(connection)
            session.commit()

    @classmethod
    def get_connections_as_dataframe(cls):
        with session_scope() as session:
            # Создаем псевдонимы для таблицы Contacts
            contact1_alias = aliased(Contacts)
            contact2_alias = aliased(Contacts)

            connections = session.query(
                cls.connection_id,
                contact1_alias.contact_name.label("contact1_name"),
                contact2_alias.contact_name.label("contact2_name"),
                cls.description
            ).join(contact1_alias, cls.cont1_id == contact1_alias.contact_id) \
                .join(contact2_alias, cls.cont2_id == contact2_alias.contact_id).all()

            # Преобразуем результат в DataFrame
            df = pd.DataFrame(connections,
                              columns=["connection_id", "contact1_name", "contact2_name", "description"])
            df.index += 1
        return df

    @classmethod
    def delete_connection(cls, connection_id):
        with session_scope() as session:
            connection = session.query(cls).filter_by(connection_id=connection_id).first()
            if connection:
                session.delete(connection)
                session.commit()

    @classmethod
    def get_connections_for_contact(cls, contact_name):
        with session_scope() as session:
            # Получаем контакт по имени
            contact = session.query(Contacts).filter(Contacts.contact_name == contact_name).first()

            if not contact:
                return None  # Если контакт не найден, возвращаем None

            # Создаем псевдонимы для Contacts для использования в join
            contact1_alias = aliased(Contacts)
            contact2_alias = aliased(Contacts)

            # Выполняем запрос для получения всех связей для данного контакта
            connections = session.query(
                # Если контакт является cont1, то возвращаем его имя и имя второго контакта
                contact1_alias.contact_name.label("Контакт"),
                cls.description.label("Связь")
            ).join(contact1_alias, cls.cont1_id == contact1_alias.contact_id) \
                .join(contact2_alias, cls.cont2_id == contact2_alias.contact_id) \
                .filter(
                (cls.cont1_id == contact.contact_id) | (cls.cont2_id == contact.contact_id),
                cls.cont1_id != cls.cont2_id  # Исключаем связи с самим собой
            ) \
                .union(
                session.query(
                    contact2_alias.contact_name.label("Контакт"),
                    cls.description.label("Связь")
                ).join(contact1_alias, cls.cont1_id == contact1_alias.contact_id)
                .join(contact2_alias, cls.cont2_id == contact2_alias.contact_id)
                .filter(
                    (cls.cont1_id == contact.contact_id) | (cls.cont2_id == contact.contact_id),
                    cls.cont1_id != cls.cont2_id  # Исключаем связи с самим собой
                )
            ).all()

            # Преобразуем результат в DataFrame
            df = pd.DataFrame(connections, columns=["Контакт", "Связь"])

            # Исключаем строки, где контакт сам с собой
            df = df[df["Контакт"] != contact_name].reset_index(drop=True)
            df.index += 1

        return df


Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    finally:
        db.close()
