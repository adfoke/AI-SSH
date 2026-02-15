from sqlalchemy import inspect, text

from .crypto import encrypt_value
from .db import Base, SessionLocal, engine
from .models import Credential


def migrate_credentials() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "hosts" not in tables:
        return

    columns = {col["name"] for col in inspector.get_columns("hosts")}
    if "key_path" not in columns:
        return

    with SessionLocal() as session:
        rows = session.execute(
            text("SELECT id, auth_type, key_path FROM hosts WHERE key_path IS NOT NULL AND key_path != ''")
        ).fetchall()
        for row in rows:
            exists = session.query(Credential).filter(Credential.host_id == row.id).first()
            if exists:
                continue
            credential = Credential(
                host_id=row.id,
                auth_type=row.auth_type,
                encrypted_key_path=encrypt_value(row.key_path),
                encrypted_password=None,
            )
            session.add(credential)
        if rows:
            session.execute(text("UPDATE hosts SET key_path = NULL"))
        session.commit()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    migrate_credentials()
