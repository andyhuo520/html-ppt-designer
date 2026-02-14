# Skill 撰写完整指南 / How to Write a Skill

## 核心结构

一个完整的 skill 需要 **7 个关键部分**：

```
1. 元信息头（YAML Front Matter）
2. 简介 + 快速开始
3. 核心规则（Critical Rules）
4. 完整工作流程（Workflow）
5. AskUserQuestion 配置模板
6. 脚本/工具说明
7. 示例/参考
```

---

## 1. 元信息头（必须）

```yaml
---
name: skill-name
description: 简短描述，包含触发词。触发词：xxx、xxx、xxx
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---
```

**要点**：
- `name`: 小写 + 连字符
- `description`: 要包含中文触发词，这样用户说中文也能触发
- `allowed-tools`: 限制工具范围，防止误操作

---

## 2. 简介 + 快速开始（30 秒内让 AI 理解）

```markdown
# Skill Name / 中文名

**版本**: 1.0
**更新日期**: 2026-02-09

## Quick Start / 快速开始

**User just asks:**
- "帮我生成一个..."
- "创建..."

**Claude Code will:**
1. 分析输入
2. 调用工具
3. 生成输出
```

**要点**：
- 用最简单的语言描述 "用户说什么" → "AI 做什么"
- 避免冗长的背景介绍

---

## 3. 核心规则（Critical Rules）⭐ 最重要

这是 **控制 AI 行为的关键**，用约束性语言：

```markdown
## Critical Rules

### 1. NEVER skip steps
必须按顺序执行，不能跳过任何步骤。

### 2. ALWAYS use AskUserQuestion
每个决策点必须询问用户，不能擅自决定。

### 3. Output format
输出必须是 [格式]，否则 [后果]。
```

**规则类型**：

| 规则类型 | 示例 |
|---------|------|
| 禁止 | NEVER use xxx, BANNED: xxx |
| 强制 | ALWAYS xxx, MUST xxx |
| 条件 | IF xxx THEN xxx |
| 格式 | Output format: xxx |

---

## 4. 完整工作流程（Workflow）

用 ASCII 图清晰展示流程：

```markdown
## Workflow

```
用户输入
    ↓
[阶段一] 输入处理
  ├── 检测类型
  └── 预处理
    ↓
[阶段二] 分析
  ├── 提取关键信息
  └── 生成方案
    ↓
[阶段三] 确认（AskUserQuestion）
    ↓
[阶段四] 生成
    ↓
[阶段五] 输出
```
```

**要点**：
- 每个阶段有明确的输入/输出
- 用 AskUserQuestion 标注需要用户确认的节点
- 用 `→` 和 `↓` 展示流向

---

## 5. AskUserQuestion 配置模板

这是 **交互式 skill 的核心**：

```markdown
## AskUserQuestion 模板

### 阶段一：风格选择

```json
{
  "questions": [{
    "question": "请选择风格？",
    "header": "风格",
    "multiSelect": false,
    "options": [
      {"label": "选项A", "description": "描述A"},
      {"label": "选项B", "description": "描述B"},
      {"label": "选项C", "description": "描述C"}
    ]
  }]
}
```

### 阶段二：详细配置

```json
{
  "questions": [
    {
      "question": "问题1？",
      "header": "配置1",
      "multiSelect": false,
      "options": [...]
    },
    {
      "question": "问题2？",
      "header": "配置2",
      "multiSelect": true,  // 多选
      "options": [...]
    }
  ]
}
```
```

**要点**：
- `header` 越短越好（显示为标签）
- `multiSelect: false` 用于单选互斥选项
- `multiSelect: true` 用于多选组合
- 每个选项都要有清晰的 `description`

---

## 6. 脚本/工具说明

如果 skill 调用外部脚本：

```markdown
## 脚本系统

### script_name.py

**用途**：一句话说明

**用法**：
```bash
python3 scripts/script_name.py [args]
```

**参数**：
| 参数 | 默认值 | 说明 |
|------|-------|------|
| --arg1 | default | 说明 |

**输出格式**：JSON/文本/文件
```

---

## 7. 示例/参考

```markdown
## 示例

### 输入
```
用户内容...
```

### 输出
```
生成结果...
```

## 参考文件
- `references/example.md` - 示例说明
```

---

## 完整模板

```yaml
---
name: my-skill
description: 这是一个XXX工具。触发词：xxx、xxx、xxx
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# My Skill / 技能名称

**版本**: 1.0
**更新日期**: 2026-02-09

---

## Quick Start

**User asks:**
- "帮我生成..."
- "创建一个..."

**Claude will:**
1. 分析输入
2. 询问用户偏好
3. 生成输出

---

## Critical Rules

### 1. NEVER skip steps
必须按流程执行，不能跳过。

### 2. ALWAYS ask before proceeding
每个决策点使用 AskUserQuestion。

### 3. Output requirements
- 格式：HTML/JSON/Markdown
- 位置：~/Desktop/

---

## Workflow

```
用户输入
    ↓
[阶段一] 输入解析
    ↓
[阶段二] 方案生成
    ↓
[阶段三] 用户确认（AskUserQuestion）
    ↓
[阶段四] 输出生成
    ↓
[阶段五] 保存输出
```

---

## AskUserQuestion 配置

### 阶段三：确认配置

```json
{
  "questions": [{
    "question": "请选择选项？",
    "header": "选项",
    "multiSelect": false,
    "options": [
      {"label": "选项A（推荐）", "description": "说明A"},
      {"label": "选项B", "description": "说明B"}
    ]
  }]
}
```

---

## 脚本说明

### scripts/main_script.py

```bash
python3 scripts/main_script.py --input xxx --output xxx
```

---

## 示例

**输入**: "帮我生成一个技术架构PPT"

**输出**: ~/Desktop/technical-architecture.html
```

---

## 撰写技巧

### 1. 使用约束性语言

| 强度 | 示例 |
|------|------|
| 最高 | NEVER, ALWAYS, MUST, BANNED |
| 高 | REQUIRED, MANDATORY |
| 中 | SHOULD, RECOMMENDED |
| 低 | MAY, OPTIONAL |

### 2. 用表格展示选项

```markdown
| 选项 | 说明 | 推荐场景 |
|------|------|---------|
| A | xxx | xxx |
| B | xxx | xxx |
```

### 3. 用代码块展示格式

```markdown
```json
{"key": "value"}
```
```

### 4. 用 ASCII 图展示流程

```markdown
```
A → B → C
    ↓
    D → E
```
```

### 5. 分层组织内容

```markdown
## 主标题
### 子标题
#### 细节
```

---

## 常见问题

### Q: Skill 太长怎么办？
A: 拆分成多个 skill + 引用外部 reference 文件

### Q: AI 不遵守规则怎么办？
A: 使用更强的约束词（NEVER/ALWAYS），把规则放在最前面

### Q: 如何调试 Skill？
A: 用具体例子测试，观察 AI 是否按预期执行

### Q: 如何更新 Skill？
A: 直接编辑 SKILL.md，无需重启
