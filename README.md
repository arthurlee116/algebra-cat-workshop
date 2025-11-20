# 七年级整式练习平台

为上海七年级学生量身定制的整式加减、乘除、因式分解在线练习站。项目包含 **React 19 + Next.js App Router** 前端、**FastAPI + SQLite** 后端，并在后端集成 SymPy 判分与 Volcengine Ark 图片生成工具。

## 快速预览
- 登录凭证：中文名 + 英文名 + 班级。
- 练习页：自选题型/难度，自动生成题目，3 次作答机会，实时积分变化，右侧展示最近 5 道题便于回顾。
- 我的猫：根据积分展示四个阶段的猫咪，使用积分在商店购买 8 种食品并触发动画。
- 静态资源：`frontend/public/images` 下的猫咪与食物图片均由 Ark 模型生成。

## 项目结构
```
backend/   FastAPI 服务、题目生成、数据库、Ark 调用工具
frontend/  Next.js 16 (React 19) + Tailwind CSS v4 应用，使用 App Router
public/images/   Ark 生成的猫咪与食品静态图
```

## 后端运行步骤
1. 创建虚拟环境并安装依赖：
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. 配置环境变量：在 `backend/.env` 中写入
   ```env
   ARK_API_KEY=请填写自己的ArkKey
   DATABASE_URL=sqlite:///./data.db  # 可选，默认即为该值
   ```
   > Ark key 仅用于 `backend/ark_client.py` 提供的重试式生成函数，逻辑中不会将 key 写死。
3. 初始化数据库：首次运行时 FastAPI 会自动建表并创建 `backend/data.db`。
4. 启动服务：
   ```bash
   cd /Users/arthur/math
   uvicorn backend.main:app --reload
   ```
   FastAPI 默认开放在 `http://127.0.0.1:8000`，可在 `http://127.0.0.1:8000/docs` 查看 API。

5. 测试后端：
   ```bash
   pytest backend/tests -q
   ```
   - `test_questions_batch.py`: 批量生成端点测试
   - `test_recent_questions.py`: 最近题目端点测试 (empty history, 1 question, limit 5/6 ordered desc, invalid user 404)，测试自动切换到内存 SQLite，互不污染


### 主要接口
- `POST /api/login`
- `POST /api/generate_question`
- `GET /api/users/{userId}/recent_questions`
- `POST /api/check_answer`
- `POST /api/buy_food`
- `POST /api/questions/batch` (new): Generate 1-20 questions in batch. Request: `{ "count": int (1-20), "difficulty"?: "basic"|"intermediate"|"advanced" }`. Response: `{ "questions": [{ "questionId": str, "topic": str, "difficultyLevel": str, "expressionText": str, "expressionLatex": str, "difficultyScore": int, "solutionExpression": str }] }`. Reuses existing generator, no DB persistence/user required.
- `GET /api/foods`
- `GET /api/users/{userId}/summary`

题目逻辑、难度评估与计分规则的核心代码分别位于：
- `backend/question_generator.py` (批量生成复用 `generate_question`)
- `backend/services.py` (新增 `generate_batch_questions`)
- `backend/main.py` (SymPy 判分、尝试次数限制、新增 `/api/questions/batch` 路由)

前端新增 `frontend/src/hooks/useBatchQuestions.ts` hook 消费批量接口，含 TS 类型和使用示例。

## 前端运行步骤
1. 安装依赖：
   ```bash
   cd frontend
   npm install
   ```
2. 配置 API 地址（默认对接本地 8000 端口）。如果后端地址不同，设置环境变量：
   ```bash
   echo 'NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000' > .env.local
   ```
3. 运行开发服务器：
   ```bash
   npm run dev
   ```
   前端默认在 `http://localhost:3000`。

## 图片生成说明
- `public/images/cat-stage-*.png` 与 `public/images/food-*.png` 均使用 `doubao-seedream-4-0-250828` 模型生成，生成命令通过终端 `curl` + `ARK_API_KEY` 调用，不在源码中出现。
- 后端提供的 `generate_image` 函数（见 `backend/ark_client.py`）实现了带重试的 Ark API 封装，方便后续需要时复用；函数通过环境变量读取 key，避免硬编码。

## 其他说明
- 评分规则：低/中/高难度分别为 +1/+3/+5，错误均为 −1；`services.SCORE_RULES` 中集中管理并添加注释。
- 难度区间：0–33、34–66、67–100，对应题目生成函数内部的 `DIFFICULTY_RANGES`，并在 `compute_difficulty` 中基于次数/项数/系数综合打分。
- App Router 与 Tailwind CSS：前端在 `src/app` 下组织登录、练习、猫咪页面，并通过 `globals.css` 引入 Tailwind v4。
- 最近题目展示：`frontend/src/hooks/useRecentQuestions.ts` 提供数据获取；`frontend/src/components/Questions/RecentQuestions.tsx` 在练习页右侧展示 5 条最近题，自动随最新出题刷新。
- 持久化：SQLite 位于 `backend/data.db`，若需要重置可删除该文件后重新启动后端。
