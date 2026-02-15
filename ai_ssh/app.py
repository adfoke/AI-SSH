import threading

import streamlit as st

from .db import Base, SessionLocal, engine
from .migrate import migrate_credentials
from .models import AuditLog
from .openrouter_client import generate_command, select_target_alias
from .repository import (
    create_audit_log,
    create_host,
    delete_host,
    decrypt_credentials,
    get_credentials,
    get_host_by_id,
    get_hosts,
)
from .schema import CommandValidationError, parse_command_payload
from .security import classify_command
from .ssh_client import run_command
from .utils import find_host_alias


st.set_page_config(page_title="AI-SSH", layout="wide")

Base.metadata.create_all(bind=engine)
migrate_credentials()

st.title("AI-SSH 智能运维")

with st.sidebar:
    st.header("服务器管理")
    with st.form("add_host"):
        alias = st.text_input("别名")
        hostname = st.text_input("IP/域名")
        port = st.number_input("端口", min_value=1, max_value=65535, value=22)
        username = st.text_input("用户名")
        auth_type = st.selectbox("认证方式", ["key", "password"], index=0)
        key_path = st.text_input("私钥路径")
        password = st.text_input("密码", type="password")
        submitted = st.form_submit_button("添加")

    if submitted:
        if not (alias and hostname and username):
            st.error("请填写所有必填字段")
        elif auth_type == "key" and not key_path:
            st.error("请选择 key 认证并填写私钥路径")
        elif auth_type == "password" and not password:
            st.error("请选择 password 认证并填写密码")
        else:
            with SessionLocal() as session:
                create_host(session, alias, hostname, port, username, auth_type, key_path, password)
            st.success("服务器已添加")

    with st.expander("服务器列表", expanded=True):
        with SessionLocal() as session:
            hosts = get_hosts(session)
        if not hosts:
            st.info("暂无服务器")
        for host in hosts:
            col1, col2 = st.columns([3, 1])
            col1.write(f"{host.alias} ({host.hostname}:{host.port})")
            if col2.button("删除", key=f"delete_{host.id}"):
                with SessionLocal() as session:
                    delete_host(session, host.id)
                st.experimental_rerun()


st.subheader("对话即运维")

with st.container():
    host_options = {}
    alias_map = {}
    with SessionLocal() as session:
        for host in get_hosts(session):
            label = f"{host.alias} ({host.hostname})"
            host_options[label] = host.id
            alias_map[host.alias] = host.id

    if not host_options:
        st.warning("请先在左侧添加服务器")
        st.stop()

    selected_host_label = st.selectbox("选择服务器（可自动匹配）", list(host_options.keys()))
    selected_host_id = host_options[selected_host_label]

    user_query = st.text_input("输入你的运维需求")
    execute = st.button("生成并执行")

    if execute and user_query:
        matched_alias = find_host_alias(user_query, list(alias_map.keys()))
        if not matched_alias:
            try:
                with st.spinner("AI 正在匹配目标服务器..."):
                    matched_alias = select_target_alias(user_query, list(alias_map.keys()))
            except Exception:
                matched_alias = None
        resolved_host_id = alias_map.get(matched_alias, selected_host_id)

        with SessionLocal() as session:
            host = get_host_by_id(session, resolved_host_id)
            credential = get_credentials(session, resolved_host_id)

        if not host or not credential:
            st.error("未找到服务器或凭据")
            st.stop()

        if matched_alias and matched_alias != host.alias:
            st.info(f"自动匹配到服务器：{host.alias}")

        try:
            with st.spinner("AI 正在生成命令..."):
                ai_result = generate_command(user_query, host.alias)
        except Exception as exc:
            st.error(f"AI 生成失败：{exc}")
            with SessionLocal() as session:
                create_audit_log(session, host.id, user_query, "", 1, f"AI 生成失败：{exc}")
            st.stop()

        try:
            payload = parse_command_payload(ai_result)
        except CommandValidationError as exc:
            st.error(f"AI 输出格式错误：{exc}")
            with SessionLocal() as session:
                create_audit_log(session, host.id, user_query, str(ai_result), 1, f"AI 输出格式错误：{exc}")
            st.stop()

        command = payload.cmd
        risk_label = classify_command(command, payload.risk)

        st.code(command, language="bash")

        if risk_label == "risky":
            st.warning("检测到风险命令，请确认后再执行")
            confirm = st.checkbox("我已知晓风险并确认执行")
            if not confirm:
                st.stop()

        output_area = st.empty()
        output_area.text("开始执行...")

        try:
            key_path, password = decrypt_credentials(credential)
        except Exception as exc:
            st.error(f"凭据解密失败：{exc}")
            with SessionLocal() as session:
                create_audit_log(session, host.id, user_query, command, 1, f"凭据解密失败：{exc}")
            st.stop()

        def worker():
            try:
                result = run_command(
                    host.hostname,
                    host.port,
                    host.username,
                    host.auth_type,
                    key_path,
                    password,
                    command,
                    on_output=output_area.text,
                )
            except Exception as exc:
                with SessionLocal() as session:
                    create_audit_log(session, host.id, user_query, command, 1, f"执行失败：{exc}")
                output_area.text(f"执行失败：{exc}")
                return
            with SessionLocal() as session:
                create_audit_log(session, host.id, user_query, command, result.exit_code, result.output)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

with st.expander("审计日志", expanded=False):
    with SessionLocal() as session:
        logs = session.query(AuditLog).order_by(AuditLog.executed_at.desc()).limit(20).all()
    for log in logs:
        st.write(f"[{log.executed_at}] {log.user_query} -> {log.ai_command} (exit {log.exit_code})")
        st.code(log.output or "", language="bash")
