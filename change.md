# 修复建议清单（审计整改建议）

以下建议依据根目录 README 要求与当前代码差异整理，确保项目严格符合 README 规范。

## 1. 数据库设计与 README SQL 对齐
**问题**：README 中 `hosts` 表包含 `key_path`，当前实现已移除并改为 `credentials` 表。

**建议修复**：
- 方案 A（推荐）：更新根 README SQL，明确 `credentials` 表为真实设计来源，并补充迁移说明。
- 方案 B（严格按现文档）：恢复 `hosts.key_path` 字段，并确保与 `credentials` 一致性（不推荐，安全性下降）。

## 2. 数据库层约束缺失
**问题**：README SQL 使用 `CHECK(auth_type IN ('key','password'))`，当前 ORM 未实现该约束。

**建议修复**：
- 在 `models.py` 增加 `CheckConstraint`，并在 `Base.metadata.create_all` 后执行迁移（或使用 Alembic）。

## 3. 自动目标匹配未实现
**问题**：README 流程描述 AI 会识别目标并自动匹配 SQLite 中别名；当前 UI 需用户手动选择主机。

**建议修复**：
- 方案 A：在用户输入时匹配别名（简单关键词匹配）。
- 方案 B：将可选主机别名作为上下文发给 AI，让 AI 输出目标别名，并在本地做校验与匹配。
- 若保留“手动选择”，需在 README 明确说明。

## 4. 根 README 配置说明不完整
**问题**：当前实现新增 `CREDENTIALS_ENCRYPT_KEY`，但根 README 未说明。

**建议修复**：
- 更新根 README 的环境变量说明，明确 `.env` 包含 `OPENROUTER_API_KEY` 与 `CREDENTIALS_ENCRYPT_KEY`。
- 增加 Fernet key 生成示例。

---

## 建议整改优先级
1) 数据库设计对齐（文档与实现一致）
2) 数据库约束补齐
3) 自动目标匹配实现或修订文档
4) 根 README 环境变量补充

## 验收要点
- README 与数据库 schema 严格一致
- auth_type 在 DB 层有约束
- 目标匹配流程与 README 描述一致
- 根 README 配置说明完整
