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
