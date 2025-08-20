from sqlalchemy import select, update as sa_update, delete as sa_delete

class CRUDMixin:
    @classmethod
    def create(cls, session, **kwargs):
        obj = cls(**kwargs)
        session.add(obj)
        return obj

    @classmethod
    def read_all(cls, session):
        return session.scalars(select(cls)).all()

    @classmethod
    def read_one(cls, session, **filters):
        stmt = select(cls).filter_by(**filters)
        return session.scalars(stmt).first()

    @classmethod
    def update(cls, session, filters: dict, values: dict):
        stmt = sa_update(cls).where(
            *[getattr(cls, k) == v for k, v in filters.items()]
        ).values(**values)
        session.execute(stmt)

    @classmethod
    def delete(cls, session, **filters):
        stmt = sa_delete(cls).where(
            *[getattr(cls, k) == v for k, v in filters.items()]
        )
        session.execute(stmt)
