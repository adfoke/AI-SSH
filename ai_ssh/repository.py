from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .crypto import decrypt_value, encrypt_value
from .models import AuditLog, Credential, Host


def get_hosts(session: Session) -> List[Host]:
    return list(session.execute(select(Host).order_by(Host.id)).scalars())


def get_host_by_id(session: Session, host_id: int) -> Optional[Host]:
    return session.get(Host, host_id)


def create_host(
    session: Session,
    alias: str,
    hostname: str,
    port: int,
    username: str,
    auth_type: str,
    key_path: Optional[str],
    password: Optional[str],
) -> Host:
    host = Host(
        alias=alias,
        hostname=hostname,
        port=port,
        username=username,
        auth_type=auth_type,
    )
    session.add(host)
    session.flush()

    credential = Credential(
        host_id=host.id,
        auth_type=auth_type,
        encrypted_key_path=encrypt_value(key_path) if auth_type == "key" else None,
        encrypted_password=encrypt_value(password) if auth_type == "password" else None,
    )
    session.add(credential)
    session.commit()
    session.refresh(host)
    return host


def get_credentials(session: Session, host_id: int) -> Optional[Credential]:
    return session.execute(
        select(Credential).where(Credential.host_id == host_id)
    ).scalar_one_or_none()


def decrypt_credentials(credential: Credential) -> tuple[str | None, str | None]:
    key_path = decrypt_value(credential.encrypted_key_path)
    password = decrypt_value(credential.encrypted_password)
    return key_path, password


def delete_host(session: Session, host_id: int) -> None:
    host = session.get(Host, host_id)
    if not host:
        return
    session.delete(host)
    session.commit()


def create_audit_log(
    session: Session,
    host_id: int,
    user_query: str,
    ai_command: str,
    exit_code: int,
    output: str,
) -> AuditLog:
    log = AuditLog(
        host_id=host_id,
        user_query=user_query,
        ai_command=ai_command,
        exit_code=exit_code,
        output=output,
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log
