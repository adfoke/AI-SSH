from dataclasses import dataclass
from typing import Callable
import time

import paramiko


@dataclass
class SSHResult:
    exit_code: int
    output: str


def run_command(
    hostname: str,
    port: int,
    username: str,
    auth_type: str,
    key_path: str | None,
    password: str | None,
    command: str,
    on_output: Callable[[str], None] | None = None,
) -> SSHResult:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if auth_type == "key":
        if not key_path:
            raise ValueError("key_path is required for key-based authentication")
        client.connect(hostname=hostname, port=port, username=username, key_filename=key_path)
    elif auth_type == "password":
        if not password:
            raise ValueError("password is required for password authentication")
        client.connect(hostname=hostname, port=port, username=username, password=password)
    else:
        raise ValueError("Unsupported authentication type")

    channel = client.get_transport().open_session()
    channel.exec_command(command)

    output_chunks: list[str] = []
    while True:
        has_data = False
        if channel.recv_ready():
            data = channel.recv(4096).decode()
            output_chunks.append(data)
            has_data = True
            if on_output:
                on_output("".join(output_chunks))
        if channel.recv_stderr_ready():
            data = channel.recv_stderr(4096).decode()
            output_chunks.append(data)
            has_data = True
            if on_output:
                on_output("".join(output_chunks))
        if channel.exit_status_ready() and not has_data:
            break
        if not has_data:
            time.sleep(0.1)

    exit_code = channel.recv_exit_status()
    client.close()
    output = "".join(output_chunks)
    return SSHResult(exit_code=exit_code, output=output)
