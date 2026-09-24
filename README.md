# X-Automation

A LangGraph pipeline for researching AI topics (Claude, ChatGPT, agent skills, MCP, AI automation), with output in
English and Persian. Each run collects from Hacker News, GitHub, Reddit, YouTube, news, web search and Google Trends,
then uses Claude to rank the results into topics. It writes `research/<date>/research.json` for any social platform to use.
Posting to X through Buffer is planned but not built yet.

Setup, commands, architecture and known limits: see [CLAUDE.md](CLAUDE.md). Plan and status: [docs/PLAN.md](docs/PLAN.md).
