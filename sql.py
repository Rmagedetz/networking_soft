import pandas as pd
from sqlalchemy import Column, Integer, String, Date, Float, create_engine, ForeignKey, func, Boolean, case
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

    @classmethod
    def get_user_id_by_name(cls, user_name):
        with session_scope() as session:
            user = session.query(cls).filter_by(user_name=user_name).first()
            if user:
                return user.user_id
            else:
                return None


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

    @classmethod
    def get_circle_stats(cls):
        with session_scope() as session:
            subquery_max_date = session.query(
                Contacts.circle_id,
                func.max(Contacts.last_interaction).label("last_interaction_date")
            ).group_by(Contacts.circle_id).subquery()

            result = session.query(
                Circles.circle_name,
                func.count(Contacts.contact_id).label("interaction_count"),
                subquery_max_date.c.last_interaction_date,
                func.group_concat(
                    case(
                        (Contacts.last_interaction == subquery_max_date.c.last_interaction_date, Contacts.contact_name),
                        else_=""
                    )
                ).label("last_interaction_contacts")
            ).join(
                Contacts, Contacts.circle_id == Circles.circle_id
            ).join(
                subquery_max_date, subquery_max_date.c.circle_id == Circles.circle_id
            ).group_by(
                Circles.circle_name, subquery_max_date.c.last_interaction_date
            ).all()

        df = pd.DataFrame(result, columns=["circle_name", "interaction_count", "last_interaction_date",
                                           "last_interaction_contacts"])

        df['last_interaction_contacts'] = df['last_interaction_contacts'].apply(
            lambda x: ', '.join([contact.strip() for contact in x.split(',') if contact.strip() != '']) if x else ''
        )

        df.index += 1
        return df


class Contacts(Base):
    __tablename__ = "contacts"
    contact_id = Column(Integer, primary_key=True)
    contact_name = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(50))
    hobbies = Column(String(200))
    additional = Column(String(500))
    birthday = Column(Date)
    last_interaction = Column(Date)
    circle_id = Column(Integer, ForeignKey("circles.circle_id"), nullable=False)

    circle = relationship("Circles", back_populates="contacts")
    important_dates = relationship("ImportantDates", back_populates="contact", cascade="all, delete-orphan")

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
                session.query(cls.contact_name, cls.email, cls.phone, cls.birthday,
                              cls.hobbies, cls.additional, cls.last_interaction, Circles.circle_name)
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
                .distinct() \
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

            creator = aliased(User, name="creator")  # Создаем алиас для создателя задачи

            tasks = session.query(
                cls.task_id,
                cls.task_name,
                cls.description,
                cls.due_date,
                Contacts.contact_name.label("contact_name"),
                creator.user_name.label("creator_name"),  # Имя создателя задачи
                cls.done  # Статус выполнения задачи
            ).join(creator, cls.creator_id == creator.user_id) \
                .join(Contacts, cls.contact_id == Contacts.contact_id) \
                .filter(cls.executor_id == executor.user_id) \
                .distinct() \
                .all()

            df = pd.DataFrame(tasks,
                              columns=["id", "task_name", "description", "due_date", "contact_name", "creator_name",
                                       "done"])
            df.index += 1
        return df

    @classmethod
    def get_incomplete_tasks_by_creator(cls, creator_name):
        with session_scope() as session:
            creator = session.query(User).filter(User.user_name == creator_name).first()
            if not creator:
                raise ValueError(f"User with name '{creator_name}' not found")

            executor = aliased(User, name="executor")  # Создаем алиас для исполнителя задачи

            tasks = session.query(
                cls.task_id,
                cls.task_name,
                cls.description,
                cls.due_date,
                Contacts.contact_name.label("contact_name"),
                executor.user_name.label("executor_name"),  # Имя исполнителя задачи
                cls.done  # Статус выполнения задачи
            ).join(executor, cls.executor_id == executor.user_id) \
                .join(Contacts, cls.contact_id == Contacts.contact_id) \
                .filter(cls.creator_id == creator.user_id) \
                .distinct() \
                .all()

            df = pd.DataFrame(tasks,
                              columns=["id", "task_name", "description", "due_date", "contact_name", "executor_name",
                                       "done"])
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
            contact1_alias = aliased(Contacts)
            contact2_alias = aliased(Contacts)

            connections = session.query(
                cls.connection_id,
                contact1_alias.contact_name.label("contact1_name"),
                contact2_alias.contact_name.label("contact2_name"),
                cls.description
            ).join(contact1_alias, cls.cont1_id == contact1_alias.contact_id) \
                .join(contact2_alias, cls.cont2_id == contact2_alias.contact_id).all()

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
            contact = session.query(Contacts).filter(Contacts.contact_name == contact_name).first()

            if not contact:
                return None

            contact1_alias = aliased(Contacts)
            contact2_alias = aliased(Contacts)

            connections = session.query(
                contact1_alias.contact_name.label("Контакт"),
                cls.description.label("Связь")
            ).join(contact1_alias, cls.cont1_id == contact1_alias.contact_id) \
                .join(contact2_alias, cls.cont2_id == contact2_alias.contact_id) \
                .filter(
                (cls.cont1_id == contact.contact_id) | (cls.cont2_id == contact.contact_id),
                cls.cont1_id != cls.cont2_id
            ) \
                .union(
                session.query(
                    contact2_alias.contact_name.label("Контакт"),
                    cls.description.label("Связь")
                ).join(contact1_alias, cls.cont1_id == contact1_alias.contact_id)
                .join(contact2_alias, cls.cont2_id == contact2_alias.contact_id)
                .filter(
                    (cls.cont1_id == contact.contact_id) | (cls.cont2_id == contact.contact_id),
                    cls.cont1_id != cls.cont2_id
                )
            ).all()

            df = pd.DataFrame(connections, columns=["Контакт", "Связь"])

            df = df[df["Контакт"] != contact_name].reset_index(drop=True)
            df.index += 1

        return df


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.contact_id"), nullable=False)
    interaction_date = Column(Date, default=func.current_date())
    interaction_type = Column(String(50), nullable=False)
    notes = Column(String(255))

    user = relationship("User", foreign_keys=[user_id])
    contact = relationship("Contacts", foreign_keys=[contact_id])

    @classmethod
    def get_as_dataframe(cls):
        with session_scope() as session:
            user_alias = aliased(User)
            contact_alias = aliased(Contacts)

            result = session.query(
                Interaction.id,
                user_alias.user_name.label("user_name"),
                contact_alias.contact_name.label("contact_name"),
                Interaction.interaction_date,
                Interaction.interaction_type,
                Interaction.notes
            ).join(
                user_alias, user_alias.user_id == Interaction.user_id
            ).join(
                contact_alias, contact_alias.contact_id == Interaction.contact_id
            ).all()

        df = pd.DataFrame(result,
                          columns=["id", "user_name", "contact_name", "interaction_date", "interaction_type", "notes"])

        df.index += 1
        return df

    @classmethod
    def add_interaction(cls, user_name, contact_name, interaction_type, notes=None, interaction_date=None):
        with session_scope() as session:
            user = session.query(User).filter(User.user_name == user_name).first()
            contact = session.query(Contacts).filter(Contacts.contact_name == contact_name).first()

            if not user:
                return "Пользователь не найден"
            if not contact:
                return "Контакт не найден"

            new_interaction = Interaction(
                user_id=user.user_id,
                contact_id=contact.contact_id,
                interaction_type=interaction_type,
                notes=notes,
                interaction_date=interaction_date or func.current_date()
            )

            try:
                session.add(new_interaction)
                contact.last_interaction = interaction_date or func.current_date()
                session.commit()
            except IntegrityError as e:
                session.rollback()

    @classmethod
    def delete_interaction(cls, int_id):
        with session_scope() as session:
            interaction = session.query(cls).filter_by(id=int_id).first()
            if interaction:
                session.delete(interaction)
                session.commit()

    @classmethod
    def edit_interaction(cls, int_id, contact, **parameters):
        with session_scope() as session:
            record = session.query(cls).filter_by(id=int_id).first()
            contact_name = session.query(Contacts).filter(Contacts.contact_name == contact).first()
            record.contact_id = contact_name.contact_id
            for field, value in parameters.items():
                if hasattr(record, field):
                    setattr(record, field, value)


class ImportantDates(Base):
    __tablename__ = "important_dates"

    date_id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.contact_id"), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String(200), nullable=False)

    contact = relationship("Contacts", back_populates="important_dates")

    @classmethod
    def get_important_dates_dataframe(cls):
        with session_scope() as session:
            results = session.query(
                Contacts.contact_name,
                cls.date,
                cls.description
            ).join(Contacts, cls.contact_id == Contacts.contact_id).all()

            df = pd.DataFrame(results, columns=["Имя контакта", "Дата", "Описание"])
            return df

    @classmethod
    def add_date_for_contact(cls, contact_name, **parameters):
        with session_scope() as session:
            contact = session.query(Contacts).filter(Contacts.contact_name == contact_name).first()
            try:
                add = cls(contact_id=contact.contact_id, **parameters)
                session.add(add)
            except:
                pass


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
