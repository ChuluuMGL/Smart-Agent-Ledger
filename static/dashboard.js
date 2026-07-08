    const base = '';
    const storageKey = 'smart-agent-ledger-dashboard-settings';

    // P5: Comprehensive Localization dictionary
    const translations = {
      zh: {
        'brand-text': 'Agent Ledger',
        'collapse-btn-title': '收起侧栏',
        'expand-btn-title': '展开侧栏',
        'nav-overview': '总览',
        'nav-agents': 'Agent',
        'nav-rankings': '排行',
        'nav-trends': '趋势',
        'nav-projects': '项目',
        'nav-sessions': '会话明细',
        'nav-fleet': '团队节点',
        'nav-subscriptions': '订阅额度',
        'nav-settings': '管理',
        'page-title': 'Smart Agent Ledger',
        'page-sub': '多 Agent 用量账本 · 实时仪表盘',
        'label-time': '时间',
        'btn-7d': '7天',
        'btn-30d': '30天',
        'btn-90d': '90天',
        'label-agent': 'Agent',
        'all': '全部',
        'label-data': '数据',
        'btn-token-only': '仅Token',
        'btn-all': '全部',
        'display-toggle-title': '切换显示模式',
        'refresh-btn-title': '刷新数据',
        'sec-agent-list': 'Agent 清单',
        'sec-rankings': '全局排行',
        'h3-agent-rank': 'Agent 综合排行',
        'h3-agent-activity-rank': 'Agent 活动排行',
        'h3-node-activity-rank': '已连接设备排行',
        'h3-project-rank': '项目消耗排行',
        'h3-model-rank': '模型 / Provider 消耗排行',
        'h3-activity-rank': '项目活动排行',
        'sec-trends': '用量趋势',
        'btn-day': '按天',
        'btn-week': '按周',
        'btn-activity': '活动',
        'sec-projects': '项目进度',
        'sec-sessions': '会话明细',
        'admin-sessions-note': '管理员视图 · 用于排查具体会话的 token 消耗。日常关注请看 Agent 和项目。',
        'sec-fleet': '团队节点',
        'sec-subscriptions': '订阅额度',
        'sec-settings': '管理',
        'sett-range': '数据范围',
        'sett-max-records': '最大记录',
        'sett-interval': '刷新间隔',
        'seconds-unit': ' 秒',
        'sett-auto-refresh': '自动刷新',
        'h3-ledger-notes': '账本备注',
        'h3-config-paths': '配置文件',
        'h3-source-notes': '数据源备注',
        'management-diagnostics': '提醒与排错',
        'node-ops-title': '健康检查',
        'node-ops-loading': '正在读取节点状态。',
        'node-ops-healthy': '全部当前可信节点正常。',
        'node-ops-stale': '使用缓存或过期数据：{nodes}',
        'node-ops-unavailable': '不可达节点：{nodes}',
        'node-ops-action-readonly': '推荐改用只读账本服务；shared directory 文件只作为备用同步。',
        'monthly-report-title': '月报导出',
        'monthly-report-desc': '生成当前窗口的 Markdown 月报，文件只保存在本机 reports 目录。',
        'monthly-report-button': '生成月报',
        'monthly-report-running': '正在生成月报…',
        'monthly-report-done': '已生成：',
        'monthly-report-failed': '生成失败：',
        'foot-desc': '本地优先的 AI Agent 用量账本',

        // Dynamic JS Strings
        'syncing-ledger': '正在同步本机 Agent 账本...',
        'reading-sub': '正在读取订阅账本',
        'waiting-token': '等待真实 token 来源',
        'waiting-cost': '等待真实调用成本来源',
        'read-local-records': '读取本机记录',
        'read-proj-mapping': '读取项目映射',
        'read-current-window': '读取当前窗口',
        'read-ide-meta': '读取 IDE 元数据',
        'read-session-state': '读取会话状态',
        'kpi-tokens-label': 'Token 总量',
        'kpi-cost-label': '调用金额',
        'kpi-agents-label': 'Agent',
        'kpi-projects-label': '项目',
        'kpi-sessions-label': '会话/任务',
        'kpi-lines-label': '代码改动',
        'kpi-active-label': '活跃/近期',
        'kpi-tokens-detail-none': '没有可靠 token 来源',
        'kpi-tokens-detail-format': '{n} 条记录提供 token',
        'kpi-trusted-tokens-detail-format': '{n} 条当前可信记录',
        'kpi-fleet-loading-detail': '等待团队节点快照，不显示本机临时总量。',
        'kpi-fleet-unavailable-detail': '团队节点快照不可用，未用本机账本替代。',
        'kpi-fleet-failed-detail': '团队节点快照读取失败：{error}。未用本机账本替代。',
        'kpi-fleet-snapshot-detail': '窗口 {days} 天 · 已计入 {included}/{configured} 节点 · 快照 {time}',
        'kpi-fleet-refreshing-detail': '后台刷新中，先显示上次快照',
        'kpi-fleet-partial-cache-detail': '使用最近不完整快照',
        'kpi-fleet-stale-cache-detail': '含上次缓存节点：{nodes}',
        'kpi-cost-detail-none': '未接入 LiteLLM/真实账单来源',
        'kpi-cost-detail-format': '{n} 条调用成本记录 · 订阅费见提醒',
        'kpi-agents-detail': '近期有记录的 Agent',
        'kpi-projects-detail': '有会话记录的项目',
        'kpi-sessions-detail': '近窗口记录总数',
        'kpi-lines-detail-none': '仅显示真实改动字段',
        'kpi-lines-detail-format': '-{removed} · {files} 个文件',
        'kpi-active-detail': '进行中或近期会话',
        'cost-unavailable': '金额不可用 {n} 条',
        'syncing-agent-ledger': '正在读取团队节点和本机 Agent 账本。',
        'sync-failed': '连接失败',
        'read-failed': '读取失败：',
        'fleet-read-failed': '团队节点读取失败：',
        'fleet-node-status-unavailable': '团队节点状态暂不可用。',
        'sub-read-failed': '订阅状态读取失败：',
        'routing-advice-unavailable': '路由建议暂不可用。',
        'plan-table-unavailable': '计划明细暂不可用。',
        'feishu-read-failed': '飞书提醒状态读取失败：',
        'syncing-done': '正在加载数据…',
        'ledger-background-syncing': '本机 Agent 账本仍在后台扫描，完成后会自动补齐明细。',
        'ledger-read-failed': '账本后台读取失败',
        'ledger-timeout-or-syncing': '账本仍在同步或读取超时',
        'days-format': '近 {n} 天',
        'syncing': '同步中',
        'manual-refresh': '手动',
        'auto-refresh': '自动',
        'refresh-countdown': '{n} 秒后刷新',
        'demo-mode-title': 'Demo 模式',
        'demo-mode-desc': '当前展示匿名示例数据，不读取本机日志、订阅文件或团队节点配置。',
        'status-running': '运行中 · 8001',
        'status-error': '异常',
        'provider-requests': 'Provider 请求',
        'provider-col': 'Provider',
        'requests-col': '请求数',
        'requests-total-summary': '总请求 {total} · Fallback {fallbacks}',
        'requests-restart-note': '自上次重启以来的累计值',
        'routing-config': '路由配置',
        'routing-type-col': '类型',
        'routing-keywords-col': '关键词',
        'providers-label': 'Providers: {list}',
        'kpi-not-integrated': '未接入',
        'no-agent-records': '尚未识别到 Agent 账本记录。',
        'no-project-records': '暂无项目任务记录。',
        'no-session-records': '暂无会话记录。',
        'no-fleet-records': '尚未配置授权团队节点。',
        'no-fleet-activity-records': '尚未配置授权活动节点。',
        'no-plan-records': '尚未录入真实订阅、续费日或额度上限，所以这里不显示任何虚拟计划。',
        'fleet-notes-empty': '无团队节点备注。',
        'routing-advice-empty': '尚未录入带 provider_key 和真实额度的计划，因此不会改变网关路由。',
        'sub-alerts-none-title': '订阅提醒',
        'sub-alerts-none-desc': '暂无临近续费或额度提醒',
        'sub-alerts-normal-item': '全部正常',
        'sub-alerts-plans-count': '计划 {n} 个',
        'sub-alerts-active-title': '订阅提醒',
        'sub-alerts-active-desc': '{alerts} 个提醒 · 续费 {renewals}',
        'sub-alerts-view-detail': '查看明细',
        'sub-alerts-date-unknown': '日期未知',
        'sub-alerts-date-today': '今天到期/续费',
        'sub-alerts-date-days': '{n} 天后',
        'stat-summary': '统计摘要',
        'stat-agent-makeup': 'Agent 构成',
        'stat-peak': '峰值 ({date})',
        'stat-top-agent': 'Top Agent',
        'stat-token-total': '总 Token',
        'stat-sessions-total': '会话数',
        'stat-pct-col': '占比',
        'empty-data': '暂无数据',
        'unavailable': '不可用',
        'routing-avoid': '避让：',
        'routing-prefer': '优先：',
        'routing-rem-pct': '剩余 {n}%',
        'plan-id-label': '计划',
        'plan-status-label': '状态',
        'plan-provider-label': 'Provider',
        'plan-model-label': '模型',
        'plan-fee-label': '费用',
        'plan-renewal-label': '续费/到期',
        'plan-autorenew-label': '自动续费',
        'plan-reset-label': '重置',
        'plan-remaining-label': '剩余',
        'plan-source-label': '来源',
        'yes': '是',
        'no': '否',
        'feishu-status-ready': '可发送',
        'feishu-status-pending': '待配置',
        'feishu-config-title': '飞书提醒配置',
        'feishu-configured': '已配置',
        'feishu-missing': '缺失',
        'feishu-recipient-id': '收件人 ID',
        'feishu-daily-check': '每日检查',
        'feishu-daily-check-time': '{tz} {hour}:00 后',
        'feishu-default-advance': '默认提前',
        'feishu-default-advance-days': '{n} 天',
        'feishu-alerts-count': '飞书提醒项',
        'feishu-last-sent': '上次发送',
        'feishu-none': '无',
        'feishu-missing-fields': '缺少',
        'feishu-default-days-input': '默认提前天数',
        'feishu-check-hour-input': '每日检查小时',
        'feishu-save-btn': '保存提醒设置',
        'feishu-save-status-saving': '保存中...',
        'feishu-save-status-saved': '已保存',
        'feishu-save-status-failed': '保存失败：',
        'feishu-window-plan': '计划',
        'feishu-window-renewal': '续费/到期',
        'feishu-window-advance': '提前天数',
        'feishu-window-start': '开始提醒',
        'agent-snapshot-title': 'Agent 接入状态',
        'agent-snapshot-status-col': '状态',
        'agent-snapshot-count-col': '数量',
        'agent-snapshot-installed': '已安装',
        'agent-snapshot-connected': '已接入且有记录',
        'agent-snapshot-fleet-only': '团队节点活动',
        'agent-snapshot-not-connected': '已安装但未接入',
        'agent-snapshot-no-recent': '已安装但无近期记录',
        'agent-fleet-activity-note': '来自团队节点活动记录；如果没有经过网关，不产生 token。',
        'agent-fleet-nodes-label': '节点 {list}',
        'agent-activity-label': '活动',
        'fleet-agent-collector': '团队节点活动',
        'missing-explain-cache': '本地缓存最近计算日期是 {date}。',
        'missing-explain-no-recent': '{list} 的采集器已识别本地结构，但当前窗口没有真实会话记录，因此不计入任务数。',
        'missing-explain-openclaw-connected': 'OpenClaw 已经接入：会从 session 索引和任务运行库读取记录。',
        'missing-explain-openclaw-disconnected': 'OpenClaw 已安装，但当前窗口没有可展示的近期 session/task。',
        'missing-explain-antigravity': 'Antigravity 已安装，但目前只识别到 IDE 数据和日志；还没有映射出可靠的任务/token 账本表。',
        'missing-explain-pending': '{list} 已安装，但当前只做安装识别；还没有接入可靠的会话/token 采集器。',
        'missing-explain-all-ok': '所有已识别 Agent 都有当前窗口账本记录。',
        'agent-usage-col-agent': 'Agent',
        'agent-usage-col-status': '状态',
        'agent-usage-col-projects': '项目',
        'agent-usage-col-sessions': '会话/任务',
        'agent-usage-col-token': 'Token',
        'agent-usage-col-change': '代码改动',
        'agent-usage-col-cost': '金额',
        'agent-usage-active-tag': '有近期任务',
        'agent-usage-recorded-tag': '已记录',
        'rank-col-name': '名称',
        'rank-col-token': 'Token',
        'rank-col-records': '记录',
        'rank-col-data': '数据',
        'project-col-project': '项目',
        'project-col-status': '状态',
        'project-col-agent': 'Agent',
        'project-col-sessions': '会话/任务',
        'project-col-active': '活跃',
        'project-col-token': 'Token',
        'project-col-change': '代码改动',
        'project-col-latest': '最新任务',
        'project-status-active': '有进展',
        'project-status-recorded': '已记录',
        'session-col-time': '时间',
        'session-col-agent': 'Agent',
        'session-col-project': '项目',
        'session-col-status': '状态',
        'session-col-task': '任务',
        'session-col-token': 'Token',
        'session-col-change': '代码改动',
        'session-col-cost': '金额',
        'fleet-col-item': '项目',
        'fleet-col-count': '数量',
        'fleet-configured-pcs': '已配置团队设备',
        'fleet-connected-nodes': '已连接节点',
        'fleet-records-count': '账本记录',
        'fleet-known-token-records': '有 token 的记录',
        'fleet-row-sample-records': '已加载样本 {n}',
        'fleet-nodes-token': '团队节点 token',
        'fleet-activity-sessions': '活动次数',
        'fleet-n8n-workflows': 'n8n 工作流',
        'fleet-n8n-active-workflows': 'n8n 活跃工作流',
        'fleet-n8n-executions': 'n8n 执行次数',
        'fleet-n8n-non-success': 'n8n 非成功执行',
        'fleet-config-path': '配置文件：',
        'config-path-fleet': '团队节点配置',
        'config-path-subscriptions': '订阅额度配置',
        'config-path-feishu': '飞书提醒配置',
        'config-path-none': '暂无可展示的配置路径。',
        'fleet-node-status-title': '节点状态',
        'fleet-ops-title': '健康检查',
        'fleet-complete-title': '数据完整',
        'fleet-partial-title': '数据不完整',
        'fleet-none-title': '未配置节点',
        'fleet-complete-desc': '{connected}/{configured} 个节点已连接',
        'fleet-partial-desc': '{connected}/{configured} 个节点已连接 · 异常 {issues} 个',
        'fleet-unavailable-nodes': '异常节点：{nodes}',
        'fleet-stale-nodes': '缓存/过期节点：{nodes}',
        'fleet-cache-stale': '使用上次成功同步',
        'fleet-export-stale': '导出已过期',
        'fleet-health-connected': '连接率',
        'fleet-health-trusted-nodes': '可信节点',
        'fleet-health-stale-known': '上次已知 Token',
        'fleet-health-token-coverage': 'Token 覆盖率',
        'fleet-health-n8n-success': 'n8n 成功率',
        'fleet-health-records': '账本记录',
        'fleet-health-activity': '活动次数',
        'fleet-health-token-total': '当前可信 Token',
        'fleet-health-token-breakdown': 'Token 口径',
        'fleet-health-real-token-nodes': '真实 token 节点',
        'fleet-health-estimated-token-nodes': '估算 token 节点',
        'fleet-health-activity-only-nodes': '仅活动节点',
        'fleet-health-n8n-workflows': 'n8n 工作流',
        'fleet-health-n8n-active': '活跃工作流',
        'fleet-node-token': 'Token',
        'fleet-node-last-known-token': '上次已知',
        'fleet-node-excluded-current': '未计入当前总量',
        'fleet-node-activity': '活动',
        'fleet-node-cost': '成本',
        'fleet-node-cache-age': '缓存 {n} 秒',
        'fleet-node-issue': '错误原因',
        'fleet-node-action': '处理建议',
        'fleet-node-stale-action': '优先安装只读账本服务，让主节点主动拉取；暂用 shared directory 时请恢复每小时导出或手动重新导出。',
        'fleet-data-quality-real': '真实 token',
        'fleet-data-quality-activity-only': '仅活动',
        'fleet-data-quality-estimated': '估算',
        'fleet-data-quality-mixed': '混合',
        'fleet-data-quality-stale': '上次已知',
        'fleet-data-quality-unavailable': '不可用',
        'fleet-real-token-detail': '真实 {tokens} / {records} 条',
        'fleet-estimated-token-detail': '估算 {tokens} / {records} 条',
        'fleet-unavailable-token-detail': '不可用 {records} 条',
        'fleet-excluded-stale-detail': '已排除过期同步 {tokens} / {records} 条',
        'sub-summary-title': '订阅状态',
        'sub-plans-label': '订阅计划',
        'sub-alerts-label': '提醒项',
        'sub-renewal-label': '最近续费',
        'sub-quota-label': '额度状态',
        'sub-alerts-clear': '暂无提醒',
        'routing-advice-title': '路由建议',
        'fleet-rank-col-pc-agent': '电脑 / Agent',
        'fleet-rank-col-agent': 'Agent',
        'fleet-rank-col-project': '项目',
        'fleet-rank-col-sources': '来源',
        'fleet-node-col-node': '节点',
        'fleet-node-col-type': '类型',
        'fleet-node-col-status': '状态',
        'fleet-rank-col-token': 'Token',
        'fleet-rank-col-records': '记录',
        'fleet-rank-col-activity': '活动',
        'fleet-rank-col-non-success': '非成功',
        'fleet-rank-col-latest': '最近',
        'hero-title': 'AI Agent 用量账本',
        'hero-sub': '多 Agent · 智能路由 · 实时监控',
        'agent-status-title': 'Agent 接入状态',
        'data-explain-title': '数据说明',
        'loading': '正在加载数据…',
        'unnamed-plan': '未命名计划',
        'feishu-receive-label': '接收方',
        'title': 'Smart Agent Ledger | Real-time AI Agent Router Dashboard',
        'routing-local-label': '\u672c\u5730\u4f18\u5148',
        'routing-coding-label': '\u4ee3\u7801\u751f\u6210',
        'routing-reason-label': '\u63a8\u7406\u5927\u6a21\u578b',
        'routing-quality-label': '\u9ad8\u8d28\u91cf\u5355\u5361',
        'add-keyword-placeholder': '\u56de\u8f66\u6dfb\u52a0...',
        'btn-save-routing': '\u4fdd\u5b58\u8def\u7521\u914d\u7f6e',
        'saving': '\u6b63\u5728\u4fdd\u5b58...',
        'saved': '\u4fdd\u5b58\u6210\u529f',
        'save-failed': '\u4fdd\u5b58\u5931\u8d25'
      },
      en: {
        'brand-text': 'Agent Ledger',
        'collapse-btn-title': 'Collapse Sidebar',
        'expand-btn-title': 'Expand Sidebar',
        'nav-overview': 'Overview',
        'nav-agents': 'Agent',
        'nav-rankings': 'Rankings',
        'nav-trends': 'Trends',
        'nav-projects': 'Projects',
        'nav-sessions': 'Sessions (Admin)',
        'nav-fleet': 'Team Nodes',
        'nav-subscriptions': 'Subscriptions',
        'nav-settings': 'Manage',
        'page-title': 'Smart Agent Ledger',
        'page-sub': 'Multi-Agent Agent Ledger · Real-time Dashboard',
        'label-time': 'Time',
        'btn-7d': '7D',
        'btn-30d': '30D',
        'btn-90d': '90D',
        'label-agent': 'Agent',
        'all': 'All',
        'label-data': 'Data',
        'btn-token-only': 'Token Only',
        'btn-all': 'All',
        'display-toggle-title': 'Toggle Display Mode',
        'refresh-btn-title': 'Refresh Data',
        'sec-agent-list': 'Agent Inventory',
        'sec-rankings': 'Global Rankings',
        'h3-agent-rank': 'Agent Overview Rankings',
        'h3-agent-activity-rank': 'Agent Activity Rankings',
        'h3-node-activity-rank': 'Connected Device Rankings',
        'h3-project-rank': 'Project Usage Rankings',
        'h3-model-rank': 'Model / Provider Usage Rankings',
        'h3-activity-rank': 'Project Activity Rankings',
        'sec-trends': 'Usage Trends',
        'btn-day': 'Daily',
        'btn-week': 'Weekly',
        'btn-activity': 'Activity',
        'sec-projects': 'Project Progress',
        'sec-sessions': 'Session Details',
        'admin-sessions-note': 'Admin view for investigating per-session token usage. For daily monitoring, use Agents and Projects.',
        'sec-fleet': 'Team Nodes',
        'sec-subscriptions': 'Subscription Quotas',
        'sec-settings': 'Manage',
        'sett-range': 'Data Window',
        'sett-max-records': 'Max Records',
        'sett-interval': 'Refresh Rate',
        'seconds-unit': ' s',
        'sett-auto-refresh': 'Auto Refresh',
        'h3-ledger-notes': 'Ledger Remarks',
        'h3-config-paths': 'Config Files',
        'h3-source-notes': 'Data Source Notes',
        'management-diagnostics': 'Alerts & Diagnostics',
        'node-ops-title': 'Health Check',
        'node-ops-loading': 'Reading node status.',
        'node-ops-healthy': 'All current trusted nodes are healthy.',
        'node-ops-stale': 'Cached/stale nodes: {nodes}',
        'node-ops-unavailable': 'Unreachable nodes: {nodes}',
        'node-ops-action-readonly': 'Prefer the read-only ledger service; keep shared directory files as fallback sync only.',
        'monthly-report-title': 'Monthly Export',
        'monthly-report-desc': 'Generate a Markdown usage report for the current window. The file stays in local reports.',
        'monthly-report-button': 'Generate Report',
        'monthly-report-running': 'Generating report…',
        'monthly-report-done': 'Generated: ',
        'monthly-report-failed': 'Generation failed: ',
        'foot-desc': 'Multi-Agent Agent Ledger',

        // Dynamic JS Strings
        'syncing-ledger': 'Syncing local Agent ledger...',
        'reading-sub': 'Reading subscription ledger',
        'waiting-token': 'Awaiting token logs',
        'waiting-cost': 'Awaiting cost logs',
        'read-local-records': 'Read local logs',
        'read-proj-mapping': 'Read project mappings',
        'read-current-window': 'Read active window',
        'read-ide-meta': 'Read IDE metadata',
        'read-session-state': 'Read session states',
        'kpi-tokens-label': 'Total Tokens',
        'kpi-cost-label': 'Total Cost',
        'kpi-agents-label': 'Agents',
        'kpi-projects-label': 'Projects',
        'kpi-sessions-label': 'Sessions/Tasks',
        'kpi-lines-label': 'Code Changes',
        'kpi-active-label': 'Active/Recent',
        'kpi-tokens-detail-none': 'No reliable token source',
        'kpi-tokens-detail-format': '{n} logs with token data',
        'kpi-trusted-tokens-detail-format': '{n} current trusted logs',
        'kpi-fleet-loading-detail': 'Waiting for team-node snapshot; local temporary totals are not shown.',
        'kpi-fleet-unavailable-detail': 'Team-node snapshot unavailable; local ledger was not used as a substitute.',
        'kpi-fleet-failed-detail': 'Team-node snapshot read failed: {error}. Local ledger was not used as a substitute.',
        'kpi-fleet-snapshot-detail': '{days} day window · included {included}/{configured} nodes · snapshot {time}',
        'kpi-fleet-refreshing-detail': 'Refreshing in background; showing last snapshot first',
        'kpi-fleet-partial-cache-detail': 'Using recent partial snapshot',
        'kpi-fleet-stale-cache-detail': 'Includes last-known nodes: {nodes}',
        'kpi-cost-detail-none': 'No LiteLLM or real cost logs',
        'kpi-cost-detail-format': '{n} cost logs · Check alerts for subscriptions',
        'kpi-agents-detail': 'Active agents in period',
        'kpi-projects-detail': 'Projects with activity',
        'kpi-sessions-detail': 'Total active session window',
        'kpi-lines-detail-none': 'Showing code diff counts',
        'kpi-lines-detail-format': '-{removed} · {files} files',
        'kpi-active-detail': 'Ongoing or recent sessions',
        'cost-unavailable': '{n} items with cost unavailable',
        'syncing-agent-ledger': 'Reading team nodes and local agent ledger.',
        'sync-failed': 'Connection Failed',
        'read-failed': 'Read failed: ',
        'fleet-read-failed': 'Team node data read failed: ',
        'fleet-node-status-unavailable': 'Team node status currently unavailable.',
        'sub-read-failed': 'Quota data read failed: ',
        'routing-advice-unavailable': 'Routing advice currently unavailable.',
        'plan-table-unavailable': 'Plans list currently unavailable.',
        'feishu-read-failed': 'Feishu alert data read failed: ',
        'syncing-done': 'Loading data...',
        'ledger-background-syncing': 'Local scanning continues in background. Details will fill automatically.',
        'ledger-read-failed': 'Background ledger sync failed',
        'ledger-timeout-or-syncing': 'Ledger sync timed out or still loading',
        'days-format': 'Last {n} days',
        'syncing': 'Syncing',
        'manual-refresh': 'Manual',
        'auto-refresh': 'Auto',
        'refresh-countdown': 'Refresh in {n}s',
        'demo-mode-title': 'Demo Mode',
        'demo-mode-desc': 'Showing anonymous sample data. Local logs, subscription files, and team-node configs are not read.',
        'status-running': 'Running · 8001',
        'status-error': 'Offline',
        'provider-requests': 'Provider Requests',
        'provider-col': 'Provider',
        'requests-col': 'Requests',
        'requests-total-summary': 'Total {total} · Fallbacks {fallbacks}',
        'requests-restart-note': 'Cumulative since gateway start',
        'routing-config': 'Routing Settings',
        'routing-type-col': 'Type',
        'routing-keywords-col': 'Keywords',
        'providers-label': 'Providers: {list}',
        'kpi-not-integrated': 'Not Linked',
        'no-agent-records': 'No active agent ledger logs discovered.',
        'no-project-records': 'No project logs found.',
        'no-session-records': 'No session records found.',
        'no-fleet-records': 'No authorized team nodes.',
        'no-fleet-activity-records': 'No authorized activity nodes yet.',
        'no-plan-records': 'No subscriptions, renewal dates, or limits registered.',
        'fleet-notes-empty': 'No team-node logs or remarks.',
        'routing-advice-empty': 'No custom provider subscription key limits found. Dynamic routing disabled.',
        'sub-alerts-none-title': 'Quotas & Subscriptions',
        'sub-alerts-none-desc': 'No pending renewals or critical quota alerts',
        'sub-alerts-normal-item': 'All Healthy',
        'sub-alerts-plans-count': '{n} Active plans',
        'sub-alerts-active-title': 'Quota Alert',
        'sub-alerts-active-desc': '{alerts} issues · {renewals} renewals due',
        'sub-alerts-view-detail': 'View Details',
        'sub-alerts-date-unknown': 'Unknown date',
        'sub-alerts-date-today': 'Due today',
        'sub-alerts-date-days': 'In {n} days',
        'stat-summary': 'Stats Summary',
        'stat-agent-makeup': 'Agent Composition',
        'stat-peak': 'Peak ({date})',
        'stat-top-agent': 'Top Agent',
        'stat-token-total': 'Tokens',
        'stat-sessions-total': 'Sessions',
        'stat-pct-col': 'Share',
        'empty-data': 'No data available',
        'unavailable': 'N/A',
        'routing-avoid': 'Avoid: ',
        'routing-prefer': 'Prefer: ',
        'routing-rem-pct': '{n}% left',
        'plan-id-label': 'Plan',
        'plan-status-label': 'Status',
        'plan-provider-label': 'Provider',
        'plan-model-label': 'Model',
        'plan-fee-label': 'Rate',
        'plan-renewal-label': 'Renewal',
        'plan-autorenew-label': 'Auto Renew',
        'plan-reset-label': 'Reset',
        'plan-remaining-label': 'Remaining',
        'plan-source-label': 'Source',
        'yes': 'Yes',
        'no': 'No',
        'feishu-status-ready': 'Ready to Send',
        'feishu-status-pending': 'Pending Config',
        'feishu-config-title': 'Feishu Alerts Settings',
        'feishu-configured': 'Linked',
        'feishu-missing': 'Missing',
        'feishu-recipient-id': 'Recipient ID',
        'feishu-daily-check': 'Daily Audit',
        'feishu-daily-check-time': 'After {hour}:00 ({tz})',
        'feishu-default-advance': 'Default Alert',
        'feishu-default-advance-days': '{n} days prior',
        'feishu-alerts-count': 'Active Alerts',
        'feishu-last-sent': 'Last Sent',
        'feishu-none': 'None',
        'feishu-missing-fields': 'Missing fields',
        'feishu-default-days-input': 'Warning Days',
        'feishu-check-hour-input': 'Audit Time (Hour)',
        'feishu-save-btn': 'Save Settings',
        'feishu-save-status-saving': 'Saving...',
        'feishu-save-status-saved': 'Saved successfully',
        'feishu-save-status-failed': 'Save failed: ',
        'feishu-window-plan': 'Plan',
        'feishu-window-renewal': 'Renewal',
        'feishu-window-advance': 'Alert Days',
        'feishu-window-start': 'Reminder Starts',
        'agent-snapshot-title': 'Agent Link Status',
        'agent-snapshot-status-col': 'Status',
        'agent-snapshot-count-col': 'Count',
        'agent-snapshot-installed': 'Installed',
        'agent-snapshot-connected': 'Linked & active',
        'agent-snapshot-fleet-only': 'Team node activity',
        'agent-snapshot-not-connected': 'Installed/Not connected',
        'agent-snapshot-no-recent': 'Installed/No recent logs',
        'agent-fleet-activity-note': 'Activity from team nodes; no tokens unless routed through the gateway.',
        'agent-fleet-nodes-label': 'Nodes {list}',
        'agent-activity-label': 'Activity',
        'fleet-agent-collector': 'Team node activity',
        'missing-explain-cache': 'Local cache computed on {date}.',
        'missing-explain-no-recent': '{list} directory recognized. No active session windows found.',
        'missing-explain-openclaw-connected': 'OpenClaw linked: polling active sessions and task tables.',
        'missing-explain-openclaw-disconnected': 'OpenClaw recognized. No recent sessions to display.',
        'missing-explain-antigravity': 'Antigravity recognized. Logs and metadata loaded; task/token mapping schema pending.',
        'missing-explain-pending': '{list} recognized. Integration connectors pending.',
        'missing-explain-all-ok': 'All recognized agents have active session mappings.',
        'agent-usage-col-agent': 'Agent',
        'agent-usage-col-status': 'Status',
        'agent-usage-col-projects': 'Projects',
        'agent-usage-col-sessions': 'Sessions/Tasks',
        'agent-usage-col-token': 'Token',
        'agent-usage-col-change': 'Diffs',
        'agent-usage-col-cost': 'Cost',
        'agent-usage-active-tag': 'Active',
        'agent-usage-recorded-tag': 'Idle',
        'rank-col-name': 'Name',
        'rank-col-token': 'Token',
        'rank-col-records': 'Logs',
        'rank-col-data': 'Data',
        'project-col-project': 'Project',
        'project-col-status': 'Status',
        'project-col-agent': 'Agent',
        'project-col-sessions': 'Sessions/Tasks',
        'project-col-active': 'Active',
        'project-col-token': 'Token',
        'project-col-change': 'Diffs',
        'project-col-latest': 'Latest Task',
        'project-status-active': 'Ongoing',
        'project-status-recorded': 'Linked',
        'session-col-time': 'Time',
        'session-col-agent': 'Agent',
        'session-col-project': 'Project',
        'session-col-status': 'Status',
        'session-col-task': 'Task',
        'session-col-token': 'Token',
        'session-col-change': 'Diffs',
        'session-col-cost': 'Cost',
        'fleet-col-item': 'PC Category',
        'fleet-col-count': 'Count',
        'fleet-configured-pcs': 'Configured Devices',
        'fleet-connected-nodes': 'Active Nodes',
        'fleet-records-count': 'Total Logs',
        'fleet-known-token-records': 'Token-mapped logs',
        'fleet-row-sample-records': 'Loaded sample {n}',
        'fleet-nodes-token': 'Total Team Tokens',
        'fleet-activity-sessions': 'Activity Count',
        'fleet-n8n-workflows': 'n8n Workflows',
        'fleet-n8n-active-workflows': 'Active n8n Workflows',
        'fleet-n8n-executions': 'n8n Executions',
        'fleet-n8n-non-success': 'n8n Non-success',
        'fleet-config-path': 'Config path: ',
        'config-path-fleet': 'Team Nodes Config',
        'config-path-subscriptions': 'Subscription Quotas Config',
        'config-path-feishu': 'Feishu Alerts Config',
        'config-path-none': 'No config paths available.',
        'fleet-node-status-title': 'Node Status',
        'fleet-ops-title': 'Health Check',
        'fleet-complete-title': 'Data complete',
        'fleet-partial-title': 'Data incomplete',
        'fleet-none-title': 'No nodes configured',
        'fleet-complete-desc': '{connected}/{configured} nodes connected',
        'fleet-partial-desc': '{connected}/{configured} nodes connected · {issues} issue(s)',
        'fleet-unavailable-nodes': 'Unavailable nodes: {nodes}',
        'fleet-stale-nodes': 'Cached/stale nodes: {nodes}',
        'fleet-cache-stale': 'Using last successful sync',
        'fleet-export-stale': 'Export stale',
        'fleet-health-connected': 'Connection Rate',
        'fleet-health-trusted-nodes': 'Trusted Nodes',
        'fleet-health-stale-known': 'Last Known Tokens',
        'fleet-health-token-coverage': 'Token Coverage',
        'fleet-health-n8n-success': 'n8n Success Rate',
        'fleet-health-records': 'Ledger Records',
        'fleet-health-activity': 'Activity Count',
        'fleet-health-token-total': 'Current Trusted Tokens',
        'fleet-health-token-breakdown': 'Token Basis',
        'fleet-health-real-token-nodes': 'Real Token Nodes',
        'fleet-health-estimated-token-nodes': 'Estimated Token Nodes',
        'fleet-health-activity-only-nodes': 'Activity-only Nodes',
        'fleet-health-n8n-workflows': 'n8n Workflows',
        'fleet-health-n8n-active': 'Active Workflows',
        'fleet-node-token': 'Token',
        'fleet-node-last-known-token': 'Last known',
        'fleet-node-excluded-current': 'Excluded from current total',
        'fleet-node-activity': 'Activity',
        'fleet-node-cost': 'Cost',
        'fleet-node-cache-age': 'Cache {n}s',
        'fleet-node-issue': 'Issue',
        'fleet-node-action': 'Action',
        'fleet-node-stale-action': 'Prefer the read-only ledger service so the main node can pull data; if using shared directory, restore hourly export or export manually.',
        'fleet-data-quality-real': 'Real tokens',
        'fleet-data-quality-activity-only': 'Activity only',
        'fleet-data-quality-estimated': 'Estimated',
        'fleet-data-quality-mixed': 'Mixed',
        'fleet-data-quality-stale': 'Last known',
        'fleet-data-quality-unavailable': 'Unavailable',
        'fleet-real-token-detail': 'Real {tokens} / {records} logs',
        'fleet-estimated-token-detail': 'Estimated {tokens} / {records} logs',
        'fleet-excluded-stale-detail': 'Excluded stale sync {tokens} / {records} logs',
        'fleet-unavailable-token-detail': 'Unavailable {records} logs',
        'sub-summary-title': 'Subscription Status',
        'sub-plans-label': 'Plans',
        'sub-alerts-label': 'Alerts',
        'sub-renewal-label': 'Next Renewal',
        'sub-quota-label': 'Quota Status',
        'sub-alerts-clear': 'No alerts',
        'routing-advice-title': 'Routing Advice',
        'fleet-rank-col-pc-agent': 'Node / Agent',
        'fleet-rank-col-agent': 'Agent',
        'fleet-rank-col-project': 'Project',
        'fleet-rank-col-sources': 'Sources',
        'fleet-node-col-node': 'Node',
        'fleet-node-col-type': 'Type',
        'fleet-node-col-status': 'Status',
        'fleet-rank-col-token': 'Token',
        'fleet-rank-col-records': 'Logs',
        'fleet-rank-col-activity': 'Activity',
        'fleet-rank-col-non-success': 'Non-success',
        'fleet-rank-col-latest': 'Latest',
        'hero-title': 'AI Agent Usage Ledger',
        'hero-sub': 'Multi-Agent · Smart Routing · Real-time Monitoring',
        'agent-status-title': 'Agent Link Status',
        'data-explain-title': 'Data Legend',
        'loading': 'Loading data...',
        'unnamed-plan': 'Unnamed Plan',
        'feishu-receive-label': 'Receiver',
        'title': 'Smart Agent Ledger | Real-time AI Agent Router Dashboard',
        'routing-local-label': 'Local Hint',
        'routing-coding-label': 'Coding',
        'routing-reason-label': 'Reasoning',
        'routing-quality-label': 'Quality',
        'add-keyword-placeholder': 'Press Enter to add...',
        'btn-save-routing': 'Save Routing Config',
        'saving': 'Saving...',
        'saved': 'Saved successfully',
        'save-failed': 'Save failed'
      }
    };

    function t(key, defaultVal) {
      const lang = state.settings.lang || 'zh';
      return (translations[lang] && translations[lang][key]) || defaultVal;
    }

    function applyLanguage() {
      const lang = state.settings.lang || 'zh';
      document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en-US';

      // Update HTML static translations
      document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        const text = t(key);
        if (text) {
          el.textContent = text;
        }
      });

      // Update titles/tooltips
      document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.dataset.i18nTitle;
        const text = t(key);
        if (text) {
          el.title = text;
        }
      });

      // Update document title
      document.title = t('title', 'Smart Agent Ledger | Real-time AI Agent Router Dashboard');

      // Update dynamic elements
      updateRefreshState();

      // Trigger rerendering of lists so dynamic headers update
      if (state.lastLedger && state.lastLedgerLoadId === state.activeLoadId) {
        rerenderWithFilters();
        renderKpis(state.lastLedger);
      }
      if (state.lastFleet && state.lastFleetLoadId === state.activeLoadId) {
        renderFleet(state.lastFleet);
      }
      if (state.lastSubscriptions) {
        renderSubscriptions(state.lastSubscriptions);
      }
      if (state.lastFeishu) {
        renderFeishuReminder(state.lastFeishu);
      }
      renderConfigPaths();
    }

    const defaultSettings = {
      settingsVersion: 2,
      days: 30,
      limit: 120,
      refreshMs: 30000,
      autoRefresh: false,
      displayMode: false,
      lang: navigator.language.startsWith('zh') ? 'zh' : 'en'
    };

    function updateIcons() {
      if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
      }
    }
    const state = {
      settings: loadSettings(),
      loading: false,
      refreshTimer: null,
      countdownTimer: null,
      nextRefreshAt: null,
      eventSource: null,  // P6: SSE 连接
      stats: null,
      config: null,
      lastLedger: null,
      lastFleet: null,
      lastSubscriptions: null,
      lastFeishu: null,
      demoMode: false,
      ledgerPromise: null,
      ledgerPromiseLoadId: null,
      lastLedgerLoadId: null,
      lastFleetLoadId: null,
      ledgerRetryTimer: null,
      activeLoadId: 0,
      fleetLoading: false,
      fleetLoadFailed: false,
      fleetLoadError: '',
      activePage: 'overview',
      // P4: 全局筛选状态
      filterAgent: 'all',
      filterDataMode: 'token', // 'token' or 'all'
      trendGranularity: 'day',
      trendMode: 'token', // 'token' | 'cost' | 'both' | 'activity'
    };
    const previousCounters = new Map();
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';

    function renderDemoModeBanner(data) {
      if (data && data.demo_mode) state.demoMode = true;
      const target = document.getElementById('demoBanner');
      if (!target) return;
      if (!state.demoMode) {
        target.hidden = true;
        target.innerHTML = '';
        return;
      }
      target.hidden = false;
      target.innerHTML =
        '<div><strong>' + esc(t('demo-mode-title', 'Demo 模式')) + '</strong>' +
        '<span>' + esc(t('demo-mode-desc', '当前展示匿名示例数据，不读取本机日志、订阅文件或团队节点配置。')) + '</span></div>';
    }

    function loadSettings() {
      try {
        const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
        const settings = { ...defaultSettings, ...saved };
        if (saved.settingsVersion !== defaultSettings.settingsVersion) {
          settings.autoRefresh = false;
          settings.settingsVersion = defaultSettings.settingsVersion;
          localStorage.setItem(storageKey, JSON.stringify(settings));
        }
        return settings;
      } catch {
        return { ...defaultSettings };
      }
    }

    function saveSettings() {
      localStorage.setItem(storageKey, JSON.stringify(state.settings));
    }

    const esc = value => ('' + (value ?? ''))
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');

    const fmtInt = value => Number(value || 0).toLocaleString('en-US');
    const fmtMoney = value => {
      if (value === null || value === undefined) return t('unavailable', '不可用');
      const n = Number(value || 0);
      if (!Number.isFinite(n)) return t('unavailable', '不可用');
      const abs = Math.abs(n);
      const sign = n < 0 ? '-' : '';
      if (abs === 0) return '$0';
      if (abs < 0.0001) return sign + '<$0.0001';
      if (abs < 1) return sign + '$' + abs.toFixed(4);
      if (abs < 1000) return sign + '$' + abs.toFixed(2);
      if (abs < 1000000) return sign + '$' + (abs / 1000).toFixed(1) + 'K';
      return sign + '$' + (abs / 1000000).toFixed(1) + 'M';
    };
    const fmtPct = value => value === null || value === undefined ? t('unavailable', '不可用') : Number(value).toFixed(1) + '%';
    const fmtShort = value => {
      const n = Number(value || 0);
      if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(2) + 'B';
      if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1) + 'M';
      if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + 'K';
      return fmtInt(n);
    };
    const fmtTime = value => {
      if (!value) return '—';
      const d = new Date(value);
      if (Number.isNaN(d.getTime())) return esc(value);
      return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    };
    const fmtBilling = plan => {
      if (plan.billing_amount === null || plan.billing_amount === undefined || !plan.billing_currency) return t('unavailable', '不可用');
      const amount = Number(plan.billing_amount);
      const amountText = Number.isInteger(amount) ? fmtInt(amount) : amount.toFixed(2);
      const periodLabels = { month: '月', month_reference: '月参考', quarter: '季', year: '年', usage: '按量' };
      const suffix = periodLabels[plan.billing_period] || plan.billing_period || '';
      return plan.billing_currency + ' ' + amountText + (suffix ? ' / ' + suffix : '');
    };

    const badgeClass = status => {
      if (['active', 'recent', 'connected', 'completed', 'success', 'done'].includes(status)) return 'ok';
      if (['failed', 'error', 'timed_out', 'not_found'].includes(status)) return 'err';
      return 'warn';
    };
    const statusLabel = status => {
      const labels = {
        active: '进行中',
        recent: '近期',
        failed: '失败',
        error: '错误',
        timed_out: '超时',
        aggregate: '汇总',
        connected: '有记录',
        installed_no_recent_records: '已安装/无近期',
        installed_not_connected: '已安装/未接入',
        not_found: '未发现',
        completed: '完成',
        success: '成功',
        done: '完成',
        ended: '结束',
        archived: '归档',
        draft: '草稿',
        pending_action: '待处理',
        recorded: '已记录',
        disabled: '已停用',
        unreachable: '不可达',
        missing_url: '缺少地址'
      };
      return labels[status] || '已记录';
    };
    const statusTone = status => {
      if (status === 'connected') return 'ok';
      if (status === 'not_found' || status === 'unreachable') return 'err';
      return 'warn';
    };
    const nodeStatusLabel = status => {
      const labels = {
        connected: state.settings.lang === 'zh' ? '已连接' : 'Connected',
        refreshing: state.settings.lang === 'zh' ? '刷新中' : 'Refreshing',
        unreachable: state.settings.lang === 'zh' ? '不可达' : 'Unreachable',
        disabled: state.settings.lang === 'zh' ? '已停用' : 'Disabled',
        missing_url: state.settings.lang === 'zh' ? '缺少地址' : 'Missing URL',
        error: state.settings.lang === 'zh' ? '错误' : 'Error'
      };
      return labels[status] || status || 'unknown';
    };
    const dataQualityLabel = quality => {
      const labels = {
        real: t('fleet-data-quality-real', '真实 token'),
        activity_only: t('fleet-data-quality-activity-only', '仅活动'),
        estimated: t('fleet-data-quality-estimated', '估算'),
        mixed: t('fleet-data-quality-mixed', '混合'),
        stale: t('fleet-data-quality-stale', '上次已知'),
        unavailable: t('fleet-data-quality-unavailable', '不可用')
      };
      return labels[quality] || quality || t('fleet-data-quality-unavailable', '不可用');
    };
    const unknownCostStatuses = new Set(['unknown', 'local_token_estimate_only', 'no_token_or_cost_in_cache', 'task_status_only', 'not_available', 'no_cost_source']);
    const unknownTokenStatuses = new Set(['unknown', 'not_available', 'status_only', 'pending_schema_mapping', 'server_side_only']);
    const hasKnownToken = row => Number(row.known_token_sessions || 0) > 0 ||
      (Number(row.total_tokens || 0) > 0 && !unknownTokenStatuses.has(row.token_status || 'unknown'));
    const hasKnownCost = row => Number(row.known_cost_sessions || 0) > 0 ||
      ((row.actual_cost_usd !== null && row.actual_cost_usd !== undefined) ||
        (row.estimated_cost_usd !== null && row.estimated_cost_usd !== undefined && !unknownCostStatuses.has(row.cost_status || 'unknown')));
    const fmtTokenFor = row => hasKnownToken(row) ? fmtShort(row.total_tokens) : t('unavailable', '不可用');
    const fmtCostFor = row => hasKnownCost(row)
      ? fmtMoney(row.actual_cost_usd ?? row.estimated_cost_usd ?? row.known_cost_usd)
      : t('unavailable', '不可用');
    const fmtChange = row => {
      const added = Number(row.lines_added || 0);
      const removed = Number(row.lines_removed || 0);
      const files = Number(row.files_changed || 0);
      if (!added && !removed && !files) return '—';
      const fileText = files ? ' · ' + fmtInt(files) + ' 文件' : '';
      return '+' + fmtInt(added) + ' / -' + fmtInt(removed) + fileText;
    };
    const componentType = row => row.component_type || (row.agent === 'LiteLLM' ? 'infrastructure' : 'agent');
    async function fetchJson(url, timeoutMs) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) throw new Error(response.status + ' ' + response.statusText);
        return await response.json();
      } finally {
        clearTimeout(timer);
      }
    }

    async function postJson(url, payload, timeoutMs) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          signal: controller.signal
        });
        if (!response.ok) throw new Error(response.status + ' ' + response.statusText);
        return await response.json();
      } finally {
        clearTimeout(timer);
      }
    }

    function renderPlaceholders() {
      document.getElementById('content').style.display = 'block';
      document.getElementById('loading').style.display = 'block';
      document.getElementById('loading').textContent = t('syncing-ledger', '正在同步本机 Agent 账本...');
      document.getElementById('signal-chips').innerHTML = [t('syncing', '同步中'), t('syncing', '同步中'), t('syncing', '同步中'), t('syncing', '同步中')]
        .map(item => '<span class="signal-chip">' + esc(item) + '</span>').join('');
      document.getElementById('kpiGrid').innerHTML = [
        [t('kpi-tokens-label', 'Token 总量'), t('syncing', '同步中'), t('waiting-token', '等待真实 token 来源')],
        [t('kpi-cost-label', '调用金额'), t('syncing', '同步中'), t('waiting-cost', '等待真实调用成本来源')],
        [t('kpi-agents-label', 'Agent'), t('syncing', '同步中'), t('read-local-records', '读取本机记录')],
        [t('kpi-projects-label', '项目'), t('syncing', '同步中'), t('read-proj-mapping', '读取项目映射')],
        [t('kpi-sessions-label', '会话/任务'), t('syncing', '同步中'), t('read-current-window', '读取当前窗口')],
        [t('kpi-lines-label', '代码改动'), t('syncing', '同步中'), t('read-ide-meta', '读取 IDE 元数据')],
        [t('kpi-active-label', '活跃/近期'), t('syncing', '同步中'), t('read-session-state', '读取会话状态')]
      ].map(([label, value, detail]) =>
        '<article class="kpi">' +
          '<div class="label">' + esc(label) + '</div>' +
          '<div class="value">' + esc(value) + '</div>' +
          '<div class="detail">' + esc(detail) + '</div>' +
        '</article>'
      ).join('');
      document.getElementById('agentSnapshot').innerHTML = '<div class="empty">' + t('syncing', '同步中') + '</div>';
      document.getElementById('missing-explain').innerHTML = '<li>' + t('syncing', '同步中') + '</li>';
      document.getElementById('agentInventory').innerHTML = '<div class="empty">' + t('syncing', '同步中') + '</div>';
      document.getElementById('projectTable').innerHTML = '<div class="empty">' + t('syncing', '同步中') + '</div>';
      document.getElementById('sessionTable').innerHTML = '<div class="empty">' + t('syncing', '同步中') + '</div>';
      document.getElementById('fleetSummary').innerHTML = '<div class="empty">' + t('syncing', '同步中') + '</div>';
      document.getElementById('fleetNodeStatus').innerHTML = '<div class="empty">' + t('syncing', '同步中') + '</div>';
      document.getElementById('subSummary').innerHTML = '<div class="empty">' + t('syncing', '同步中') + '</div>';
      document.getElementById('routing-advice').innerHTML = '<div class="empty">' + t('syncing', '同步中') + '</div>';
      document.getElementById('feishuConfig').innerHTML = '<div class="empty">' + t('syncing', '同步中') + '</div>';
      document.getElementById('planTable').innerHTML = '<div class="empty">' + t('syncing', '同步中') + '</div>';
      document.getElementById('stats').innerHTML = '<h3>' + t('provider-requests', 'Provider 请求') + '</h3><div class="empty" style="margin-top:10px;">' + t('syncing', '同步中') + '</div>';
      document.getElementById('config').innerHTML = '<h3>' + t('routing-config', '路由配置') + '</h3><div class="empty" style="margin-top:10px;">' + t('syncing', '同步中') + '</div>';
      document.getElementById('nodeOpsSummary').innerHTML = '<div class="empty">' + t('node-ops-loading', '正在读取节点状态。') + '</div>';
      document.getElementById('ledger-notes').innerHTML = t('syncing', '同步中');
      document.getElementById('configPaths').innerHTML = '<div class="empty">' + t('syncing', '同步中') + '</div>';
      document.getElementById('fleetNotes').innerHTML = t('syncing', '同步中');
    }

    function animateCounter(el, key, value, formatter) {
      if (!el || value === null || value === undefined || Number.isNaN(Number(value))) {
        if (el) el.textContent = formatter ? formatter(value) : t('unavailable', '不可用');
        return;
      }
      const next = Number(value);
      const hasPrevious = previousCounters.has(key);
      const start = hasPrevious ? Number(previousCounters.get(key) || 0) : 0;
      previousCounters.set(key, next);
      if (hasPrevious && start === next) {
        el.textContent = formatter(next);
        return;
      }
      const duration = 900;
      const startedAt = performance.now();
      el.classList.remove('counter-pop');
      void el.offsetWidth;
      el.classList.add('counter-pop');
      const tick = now => {
        const t = Math.min(1, (now - startedAt) / duration);
        const eased = 1 - Math.pow(1 - t, 3);
        const current = start + (next - start) * eased;
        el.textContent = formatter(current);
        if (t < 1) {
          requestAnimationFrame(tick);
        } else {
          el.textContent = formatter(next);
        }
      };
      requestAnimationFrame(tick);
    }

    function topLevelSection(id) {
      const corePages = new Set(['overview', 'agents', 'projects', 'fleet', 'settings']);
      if (!corePages.has(id)) return null;
      const section = document.getElementById(id);
      return section && section.parentElement && section.parentElement.id === 'content' ? section : null;
    }

    function setActivePage(target, options = {}) {
      const requested = topLevelSection(target) ? target : 'overview';
      state.activePage = requested;
      for (const section of document.querySelectorAll('#content > section[id]')) {
        section.hidden = section.id !== requested;
      }
      for (const item of document.querySelectorAll('.nav button')) {
        item.classList.toggle('active', item.dataset.target === requested);
      }
      if (options.updateHash !== false && history.replaceState) {
        const suffix = requested === 'overview' ? '' : '#' + requested;
        history.replaceState(null, '', location.pathname + location.search + suffix);
      }
      if (options.scroll !== false) {
        window.scrollTo({ top: 0, behavior: options.behavior || 'auto' });
      }
      if (requested === 'trends') {
        setTimeout(renderTrendChart, 80);
      }
    }

    function bindNavigation() {
      document.getElementById('collapseBtn').addEventListener('click', () => {
        const app = document.getElementById('app');
        app.classList.toggle('collapsed');
        const btn = document.getElementById('collapseBtn');
        if (app.classList.contains('collapsed')) {
          btn.innerHTML = '<i data-lucide="chevron-right"></i>';
          btn.title = t('expand-btn-title', '展开侧栏');
        } else {
          btn.innerHTML = '<i data-lucide="chevron-left"></i>';
          btn.title = t('collapse-btn-title', '收起侧栏');
        }
        updateIcons();
        setTimeout(renderTrendChart, 260);
      });
      for (const button of document.querySelectorAll('.nav button')) {
        button.addEventListener('click', () => {
          setActivePage(button.dataset.target, { updateHash: true, behavior: 'auto' });
        });
      }
      document.addEventListener('click', event => {
        const link = event.target.closest && event.target.closest('a[href^="#"]');
        if (!link) return;
        const target = decodeURIComponent(link.getAttribute('href').slice(1));
        if (!topLevelSection(target)) return;
        event.preventDefault();
        setActivePage(target, { updateHash: true, behavior: 'auto' });
      });
      window.addEventListener('hashchange', () => {
        const target = decodeURIComponent((location.hash || '#overview').slice(1));
        setActivePage(target || 'overview', { updateHash: false, behavior: 'auto' });
      });

      // Modal Close Handlers
      const modalClose = document.getElementById('modalCloseBtn');
      if (modalClose) {
        modalClose.addEventListener('click', () => {
          document.getElementById('sessionDetailModal').style.display = 'none';
        });
      }
      const modalOverlay = document.getElementById('sessionDetailModal');
      if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
          if (e.target.id === 'sessionDetailModal') {
            modalOverlay.style.display = 'none';
          }
        });
      }
    }

    function bindSettings() {
      document.getElementById('refreshBtn').addEventListener('click', () => load({ manual: true }));
      document.getElementById('displayToggle').addEventListener('click', () => {
        setDisplayMode(!state.settings.displayMode);
      });
      // P5: Language switcher trigger
      const langToggle = document.getElementById('langToggle');
      if (langToggle) {
        langToggle.addEventListener('click', () => {
          state.settings.lang = state.settings.lang === 'zh' ? 'en' : 'zh';
          saveSettings();
          applySettings();
          applyLanguage();
        });
      }
      // Day buttons are bound in bindFilters() to avoid duplicate listeners
      document.getElementById('settLimit').addEventListener('change', event => {
        const value = Math.max(20, Math.min(300, Number(event.target.value || defaultSettings.limit)));
        state.settings.limit = value;
        saveSettings();
        applySettings();
        load({ manual: true });
      });
      document.getElementById('settRefresh').addEventListener('change', event => {
        state.settings.refreshMs = Number(event.target.value) * 1000;
        saveSettings();
        applySettings();
        scheduleRefresh();
      });
      document.getElementById('settAutoRefresh').addEventListener('click', () => {
        state.settings.autoRefresh = !state.settings.autoRefresh;
        saveSettings();
        applySettings();
        scheduleRefresh();
      });
      const reportButton = document.getElementById('exportMonthlyReport');
      if (reportButton) {
        reportButton.addEventListener('click', exportMonthlyReport);
      }
    }

    function setDisplayMode(enabled) {
      state.settings.displayMode = Boolean(enabled);
      saveSettings();
      applySettings();
      if (state.settings.displayMode) {
        returnToOverview('smooth');
      }
    }

    function returnToOverview(behavior) {
      window.setTimeout(() => {
        setActivePage('overview', { updateHash: true, behavior: behavior || 'auto' });
      }, 120);
    }

    function applySettings() {
      document.body.classList.toggle('display-mode', Boolean(state.settings.displayMode));
      const _arBtn = document.getElementById('settAutoRefresh');
      if (_arBtn) { _arBtn.textContent = state.settings.autoRefresh ? 'ON' : 'OFF'; _arBtn.classList.toggle('active', state.settings.autoRefresh); }
      document.getElementById('settRefresh').value = String(Math.round(state.settings.refreshMs / 1000));
      document.getElementById('settLimit').value = String(state.settings.limit);
      document.getElementById('displayToggle').classList.toggle('active', Boolean(state.settings.displayMode));
      for (const button of document.querySelectorAll('#daysGroup .btn-sm, #settDays .btn-sm')) {
        button.classList.toggle('active', Number(button.dataset.days) === Number(state.settings.days));
      }
      // P5: Sidebar translation
      const sidebarNote = document.getElementById('sidebar-note');
      if (sidebarNote) sidebarNote.textContent = t('days-format', '近 {n} 天').replace('{n}', state.settings.days);
      updateRefreshState();
    }

    function scheduleRefresh() {
      clearTimeout(state.refreshTimer);
      clearInterval(state.countdownTimer);
      state.nextRefreshAt = null;
      if (!state.settings.autoRefresh) {
        disconnectSse();  // P6: 手动模式关闭 SSE
        updateRefreshState();
        return;
      }
      // P6: autoRefresh 开启时优先尝试 SSE; 成功则由推送驱动, 不启动轮询计时器
      if (connectSse()) {
        state.countdownTimer = setInterval(updateRefreshState, 1000);
        updateRefreshState();
        return;
      }
      // SSE 不可用 → 回退轮询
      state.nextRefreshAt = Date.now() + Number(state.settings.refreshMs);
      state.refreshTimer = setTimeout(() => load(), Number(state.settings.refreshMs));
      state.countdownTimer = setInterval(updateRefreshState, 1000);
      updateRefreshState();
    }

    function updateRefreshState() {
      const target = document.getElementById('refreshState');
      if (!target) return;
      if (state.loading) {
        target.textContent = t('syncing', '同步中');
        return;
      }
      if (!state.settings.autoRefresh) {
        target.textContent = t('manual-refresh', '手动刷新');
        return;
      }
      if (!state.nextRefreshAt) {
        target.textContent = t('auto-refresh', '自动刷新');
        return;
      }
      const seconds = Math.max(0, Math.ceil((state.nextRefreshAt - Date.now()) / 1000));
      target.textContent = t('refresh-countdown', '{n} 秒后刷新').replace('{n}', seconds);
    }

    async function loadStatus() {
      const [health, stats, config] = await Promise.all([
        fetchJson(base + '/health', 8000),
        fetchJson(base + '/stats', 8000),
        fetchJson(base + '/config', 8000)
      ]);
      state.stats = stats;
      state.config = config;
      document.getElementById('healthPill').innerHTML =
        health.status === 'ok'
          ? '<span class="dot ok"></span><span>' + t('status-running', '运行中 · 8001') + '</span>'
          : '<span class="dot err"></span><span>' + t('status-error', '异常') + '</span>';

      let statsHtml = '<h3>' + t('provider-requests', 'Provider 请求') + '</h3><div class="table-wrap" style="margin-top:10px;"><table><tr><th>' + t('provider-col', 'Provider') + '</th><th class="num">' + t('requests-col', '请求数') + '</th></tr>';
      for (const [provider, count] of Object.entries(stats.by_provider || {})) {
        statsHtml += '<tr><td>' + esc(provider) + '</td><td class="num">' + fmtInt(count) + '</td></tr>';
      }
      statsHtml += '</table></div>';
      statsHtml += '<div class="subtle" style="margin-top:8px;">' + t('requests-total-summary', '总请求 {total} · Fallback {fallbacks}').replace('{total}', fmtInt(stats.total_requests || 0)).replace('{fallbacks}', fmtInt(stats.fallbacks || 0)) + '</div>' +
        '<div class="subtle">' + t('requests-restart-note', '自上次重启以来的累计值') + '</div>';
      document.getElementById('stats').innerHTML = statsHtml;

      // Initialize state.routingConfig from response
      state.routingConfig = JSON.parse(JSON.stringify(config.routing || {}));
      renderRoutingConfig();
    }

    function currentFleet() {
      return state.lastFleetLoadId === state.activeLoadId ? state.lastFleet : null;
    }

    function renderWindowLoadingState() {
      const days = Number(state.settings.days || defaultSettings.days);
      const detail = t('kpi-fleet-loading-detail', '等待团队节点快照，不显示本机临时总量。');
      document.getElementById('signal-chips').innerHTML = [
        t('days-format', '近 {n} 天').replace('{n}', days),
        t('nav-fleet', '团队节点') + ' ' + t('syncing', '同步中'),
        'Token ' + t('syncing', '同步中')
      ].map(item => '<span class="signal-chip">' + esc(item) + '</span>').join('');
      document.getElementById('kpiGrid').innerHTML = [
        [t('fleet-health-token-total', '当前可信 Token'), t('syncing', '同步中'), detail, 'cpu'],
        [t('kpi-cost-label', '调用金额'), t('syncing', '同步中'), detail, 'dollar-sign'],
        [t('kpi-agents-label', 'Agent'), t('syncing', '同步中'), detail, 'bot'],
        [t('kpi-projects-label', '项目'), t('syncing', '同步中'), detail, 'folder-git-2'],
        [t('kpi-sessions-label', '会话/任务'), t('syncing', '同步中'), detail, 'message-square'],
        [t('kpi-lines-label', '代码改动'), t('syncing', '同步中'), t('read-ide-meta', '读取 IDE 元数据'), 'code-xml'],
        [t('kpi-active-label', '活跃/近期'), t('syncing', '同步中'), detail, 'sparkles']
      ].map(([label, value, itemDetail, icon]) =>
        '<article class="kpi">' +
          '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">' +
            '<div class="label">' + esc(label) + '</div>' +
            '<i data-lucide="' + icon + '" style="width:16px; height:16px; color:var(--muted-2);"></i>' +
          '</div>' +
          '<div class="value">' + esc(value) + '</div>' +
          '<div class="detail">' + esc(itemDetail) + '</div>' +
        '</article>'
      ).join('');
      document.getElementById('cost-note').textContent = detail;
      updateIcons();
    }

    function resetWindowDataForReload() {
      state.lastLedger = null;
      state.lastFleet = null;
      state.lastLedgerLoadId = null;
      state.lastFleetLoadId = null;
      state.fleetLoading = true;
      state.fleetLoadFailed = false;
      state.fleetLoadError = '';
      document.getElementById('content').style.display = 'block';
      showLedgerLoading(t('syncing-agent-ledger', '正在读取团队节点和本机 Agent 账本。'));
      renderWindowLoadingState();
    }

    function renderKpis(ledger) {
      const localTotals = ledger.totals || {};
      const fleet = currentFleet();
      const fleetSnapshotReady = !!(fleet && fleet.totals);
      const fleetTotals = fleetSnapshotReady ? fleet.totals : {};
      const fleetHealth = fleetSnapshotReady ? (fleet.node_health || {}) : {};
      const staleFleetNodeNames = fleetSnapshotReady
        ? (fleet.nodes || [])
            .filter(node => node.stale_ledger_cache)
            .map(node => node.node || node.name || 'unknown')
            .filter(Boolean)
        : [];
      const configuredNodes = Number(fleetHealth.configured_nodes ?? fleetTotals.configured_nodes ?? 0);
      const includedNodes = Number(fleetHealth.current_data_node_count ?? fleetTotals.current_data_nodes ?? 0);
      const snapshotDays = Number((fleet && fleet.window_days) || state.settings.days || ledger.window_days || 30);
      const snapshotTime = fleetSnapshotReady ? fmtTime(fleet.generated_at) : '';
      const fleetFallback = state.fleetLoading ? t('syncing', '同步中') : t('unavailable', '不可用');
      const fleetUnavailableDetail = state.fleetLoading
        ? t('kpi-fleet-loading-detail', '等待团队节点快照，不显示本机临时总量。')
        : (state.fleetLoadFailed
            ? t('kpi-fleet-failed-detail', '团队节点快照读取失败：{error}。未用本机账本替代。')
                .replace('{error}', state.fleetLoadError || t('unavailable', '不可用'))
            : t('kpi-fleet-unavailable-detail', '团队节点快照不可用，未用本机账本替代。'));
      const fleetSnapshotDetail = fleetSnapshotReady
        ? t('kpi-fleet-snapshot-detail', '窗口 {days} 天 · 已计入 {included}/{configured} 节点 · 快照 {time}')
            .replace('{days}', fmtInt(snapshotDays))
            .replace('{included}', fmtInt(includedNodes))
            .replace('{configured}', fmtInt(configuredNodes))
            .replace('{time}', snapshotTime || t('unavailable', '不可用'))
        : fleetUnavailableDetail;
      const totals = fleetSnapshotReady ? {
        ...localTotals,
        sessions: Number(fleetTotals.activity_sessions || fleetTotals.records || 0),
        agents: (fleet.agent_activity_rank || fleet.agent_token_rank || []).length,
        projects: (fleet.project_activity_rank || fleet.project_token_rank || []).length,
        total_tokens: Number(fleetTotals.total_tokens || 0),
        known_token_sessions: Number(fleetTotals.known_token_records || 0),
        known_cost_usd: Number(fleetTotals.known_cost_usd || 0),
        known_cost_sessions: Number(fleetTotals.known_cost_sessions || 0),
        active_sessions: Number(fleetTotals.active_sessions || fleetTotals.activity_sessions || 0),
        unknown_cost_sessions: Number(fleetTotals.unknown_cost_sessions || 0)
      } : {};
      const knownTokenSessions = Number(totals.known_token_sessions || 0);
      const knownCostSessions = Number(totals.known_cost_sessions || 0);
      const excludedStaleTokenTotal = Number(fleetTotals.excluded_stale_total_tokens || 0);
      const excludedStaleTokenRecords = Number(fleetTotals.excluded_stale_token_records || 0);
      const tokenKpiDetail = fleetSnapshotReady
        ? [
            knownTokenSessions
              ? t('kpi-trusted-tokens-detail-format', '{n} 条当前可信记录').replace('{n}', fmtInt(knownTokenSessions))
              : t('kpi-tokens-detail-none', '没有可靠 token 来源'),
            fleetSnapshotDetail,
            fleet && (fleet._stale || fleet._refreshing)
              ? t('kpi-fleet-refreshing-detail', '后台刷新中，先显示上次快照')
              : '',
            fleet && fleet._partial_cache
              ? t('kpi-fleet-partial-cache-detail', '使用最近不完整快照')
              : '',
            staleFleetNodeNames.length
              ? t('kpi-fleet-stale-cache-detail', '含上次缓存节点：{nodes}').replace('{nodes}', staleFleetNodeNames.join('、'))
              : '',
            (excludedStaleTokenTotal > 0 || excludedStaleTokenRecords > 0)
              ? t('fleet-excluded-stale-detail', '已排除过期同步 {tokens} / {records} 条')
                  .replace('{tokens}', fmtShort(excludedStaleTokenTotal))
                  .replace('{records}', fmtInt(excludedStaleTokenRecords))
              : ''
          ].filter(Boolean).join(' · ')
        : fleetUnavailableDetail;
      const hasCodeChanges = Number(localTotals.lines_added || 0) || Number(localTotals.lines_removed || 0) || Number(localTotals.files_changed || 0);
      const cards = [
        {
          key: 'tokens',
          label: t('fleet-health-token-total', '当前可信 Token'),
          icon: 'cpu',
          value: fleetSnapshotReady && knownTokenSessions ? Number(totals.total_tokens || 0) : null,
          formatter: fmtShort,
          fallback: fleetFallback,
          detail: tokenKpiDetail,
          type: 'primary emphasis'
        },
        {
          key: 'cost',
          label: t('kpi-cost-label', '调用金额'),
          icon: 'dollar-sign',
          value: fleetSnapshotReady && knownCostSessions ? Number(totals.known_cost_usd || 0) : null,
          formatter: fmtMoney,
          fallback: fleetSnapshotReady ? t('kpi-not-integrated', '未接入') : fleetFallback,
          detail: knownCostSessions
            ? t('kpi-cost-detail-format', '{n} 条调用成本记录 · 订阅费见提醒').replace('{n}', fmtInt(knownCostSessions))
            : (fleetSnapshotReady ? t('kpi-cost-detail-none', '未接入 LiteLLM/真实账单来源') : fleetSnapshotDetail),
          type: 'money emphasis'
        },
        { key: 'agents', label: t('kpi-agents-label', 'Agent'), icon: 'bot', value: fleetSnapshotReady ? Number(totals.agents || 0) : null, formatter: value => fmtInt(Math.round(value)), fallback: fleetFallback, detail: fleetSnapshotReady ? t('kpi-agents-detail', '近期有记录的 Agent') : fleetSnapshotDetail, type: 'violet' },
        { key: 'projects', label: t('kpi-projects-label', '项目'), icon: 'folder-git-2', value: fleetSnapshotReady ? Number(totals.projects || 0) : null, formatter: value => fmtInt(Math.round(value)), fallback: fleetFallback, detail: fleetSnapshotReady ? t('kpi-projects-detail', '有会话记录的项目') : fleetSnapshotDetail, type: '' },
        { key: 'sessions', label: t('kpi-sessions-label', '会话/任务'), icon: 'message-square', value: fleetSnapshotReady ? Number(totals.sessions || 0) : null, formatter: value => fmtInt(Math.round(value)), fallback: fleetFallback, detail: fleetSnapshotReady ? t('kpi-sessions-detail', '近窗口记录总数') : fleetSnapshotDetail, type: '' },
        {
          key: 'lines',
          label: t('kpi-lines-label', '代码改动'),
          icon: 'code-xml',
          value: hasCodeChanges ? Number(localTotals.lines_added || 0) : null,
          formatter: value => '+' + fmtShort(Math.round(value)),
          fallback: t('kpi-not-integrated', '未接入'),
          detail: hasCodeChanges ? t('kpi-lines-detail-format', '-{removed} · {files} 个文件').replace('{removed}', fmtShort(localTotals.lines_removed || 0)).replace('{files}', fmtInt(localTotals.files_changed || 0)) : t('kpi-lines-detail-none', '仅显示真实改动字段'),
          type: 'warn'
        },
        { key: 'active', label: t('kpi-active-label', '活跃/近期'), icon: 'sparkles', value: fleetSnapshotReady ? Number(totals.active_sessions || 0) : null, formatter: value => fmtInt(Math.round(value)), fallback: fleetFallback, detail: fleetSnapshotReady ? t('kpi-active-detail', '进行中或近期会话') : fleetSnapshotDetail, type: '' }
      ];

      document.getElementById('kpiGrid').innerHTML = cards.map(card =>
        '<article class="kpi ' + esc(card.type) + '">' +
          '<div class="kpi-head">' +
            '<div class="label">' + esc(card.label) + '</div>' +
            '<i data-lucide="' + card.icon + '" style="width:16px; height:16px; color:var(--muted-2);"></i>' +
          '</div>' +
          '<div class="value-row"><div class="value" data-counter="' + esc(card.key) + '">' + esc(card.fallback || '0') + '</div></div>' +
          '<div class="detail">' + esc(card.detail) + '</div>' +
        '</article>'
      ).join('');

      for (const card of cards) {
        const el = document.querySelector('[data-counter="' + card.key + '"]');
        if (card.value === null || card.value === undefined) {
          el.textContent = card.fallback || t('unavailable', '不可用');
        } else {
          animateCounter(el, card.key, card.value, card.formatter);
        }
      }

      const fleetCount = fleetTotals.connected_nodes || 0;
      const signalItems = fleetSnapshotReady
        ? [
            'Agent ' + fmtInt(totals.agents || 0),
            t('kpi-projects-label', '项目') + ' ' + fmtInt(totals.projects || 0),
            t('kpi-sessions-label', '会话') + ' ' + fmtInt(totals.sessions || 0),
            t('nav-fleet', '团队节点') + ' ' + fmtInt(fleetCount),
            knownTokenSessions ? 'Token ' + fmtShort(totals.total_tokens || 0) : 'Token ' + t('unavailable', '不可用')
          ]
        : [
            t('days-format', '近 {n} 天').replace('{n}', snapshotDays),
            t('nav-fleet', '团队节点') + ' ' + fleetFallback,
            'Token ' + fleetFallback
          ];
      document.getElementById('signal-chips').innerHTML = signalItems.map(item => '<span class="signal-chip">' + esc(item) + '</span>').join('');

      const sidebarNote = document.getElementById('sidebar-note');
      if (sidebarNote) sidebarNote.textContent = t('days-format', '近 {n} 天').replace('{n}', snapshotDays);

      document.getElementById('cost-note').textContent = fleetSnapshotReady
        ? t('cost-unavailable', '金额不可用 {n} 条').replace('{n}', fmtInt(totals.unknown_cost_sessions || 0))
        : fleetUnavailableDetail;
      updateIcons();
    }

    function mergeFleetActivityAgents(agentInventory) {
      const merged = new Map();
      for (const row of agentInventory) {
        const key = String(row.agent || 'unknown').toLowerCase();
        merged.set(key, { ...row });
      }

      const fleet = currentFleet();
      const activityRows = (fleet && fleet.agent_activity_rank) || [];
      for (const row of activityRows) {
        const agent = row.agent || 'unknown';
        if (!agent || agent === 'unknown') continue;
        const key = String(agent).toLowerCase();
        const existing = merged.get(key);
        const nodes = Array.isArray(row.nodes) ? row.nodes : [];
        if (existing) {
          existing.fleet_activity_sessions = Number(row.sessions || 0);
          existing.fleet_nodes = nodes;
          existing.fleet_latest_at = row.latest_at || existing.last_seen;
          existing.n8n_non_success = row.n8n_non_success || 0;
          existing.n8n_success = row.n8n_success || 0;
          merged.set(key, existing);
          continue;
        }
        merged.set(key, {
          agent,
          component_type: 'agent',
          status: 'connected',
          collector_status: t('fleet-agent-collector', '团队节点活动'),
          note: t('agent-fleet-activity-note', '来自团队节点活动记录；如果没有经过网关，不产生 token。'),
          record_count: Number(row.sessions || 0),
          total_tokens: Number(row.total_tokens || 0),
          known_token_sessions: Number(row.known_token_sessions || 0),
          token_status: Number(row.known_token_sessions || 0) > 0 ? 'ok' : 'not_available',
          cost_status: 'not_available',
          last_seen: row.latest_at || '',
          installed: false,
          fleet_only: true,
          fleet_activity_sessions: Number(row.sessions || 0),
          fleet_nodes: nodes,
          n8n_non_success: row.n8n_non_success || 0,
          n8n_success: row.n8n_success || 0,
        });
      }
      return Array.from(merged.values()).sort((a, b) => {
        const aActivity = Number(a.fleet_activity_sessions || a.record_count || 0);
        const bActivity = Number(b.fleet_activity_sessions || b.record_count || 0);
        const aTokens = Number(a.total_tokens || 0);
        const bTokens = Number(b.total_tokens || 0);
        return (bTokens - aTokens) || (bActivity - aActivity) || String(a.agent).localeCompare(String(b.agent));
      });
    }

    function renderInventory(ledger) {
      const inventory = ledger.agent_inventory || [];
      const agentInventory = mergeFleetActivityAgents(inventory.filter(row => componentType(row) === 'agent'));
      const componentInventory = inventory.filter(row => componentType(row) !== 'agent');
      const renderCards = rows => rows.map(row => {
        const nodeDetail = row.fleet_nodes && row.fleet_nodes.length
          ? t('agent-fleet-nodes-label', '节点 {list}').replace('{list}', row.fleet_nodes.join('、'))
          : '';
        const detail = row.cache_last_computed
          ? (state.settings.lang === 'zh' ? '缓存日期 ' : 'Cached at ') + esc(row.cache_last_computed)
          : esc([row.note || '', nodeDetail].filter(Boolean).join(' · '));
        const activityValue = Number(row.fleet_activity_sessions || row.record_count || 0);
        const usageValue = hasKnownToken(row)
          ? fmtShort(row.total_tokens)
          : (activityValue && row.fleet_only ? fmtInt(activityValue) : (fmtChange(row) !== '—' ? fmtChange(row) : t('unavailable', '不可用')));
        const usageLabel = hasKnownToken(row)
          ? 'Token'
          : (activityValue && row.fleet_only ? t('agent-activity-label', '活动') : (fmtChange(row) !== '—' ? (state.settings.lang === 'zh' ? '代码改动' : 'Code Diff') : 'Token'));

        let statusIcon = 'alert-circle';
        if (row.status === 'connected') statusIcon = 'check-circle';
        else if (row.status === 'not_found' || row.status === 'unreachable') statusIcon = 'x-circle';

        return '<article class="agent-card">' +
          '<div class="agent-card-head">' +
            '<div><div class="agent-title">' + esc(row.agent) + '</div><div class="subtle">' + esc(row.collector_status || '') + '</div></div>' +
            '<span class="badge ' + statusTone(row.status) + '"><i data-lucide="' + statusIcon + '" style="width:12px; height:12px; margin-right:4px;"></i>' + statusLabel(row.status) + '</span>' +
          '</div>' +
          '<div class="subtle">' + detail + '</div>' +
          '<div class="agent-meta">' +
            '<div class="metric"><strong>' + fmtInt(activityValue) + '</strong><span>' + (state.settings.lang === 'zh' ? '近期记录' : 'Recent logs') + '</span></div>' +
            '<div class="metric"><strong>' + esc(usageValue) + '</strong><span>' + esc(usageLabel) + '</span></div>' +
            '<div class="metric"><strong>' + fmtTime(row.last_seen) + '</strong><span>' + (state.settings.lang === 'zh' ? '最近' : 'Latest') + '</span></div>' +
          '</div>' +
        '</article>';
      }).join('');
      document.getElementById('agentInventory').innerHTML = renderCards(agentInventory) || '<div class="empty">' + t('no-agent-records', '没有识别到 Agent。') + '</div>';

      const connected = agentInventory.filter(row => row.status === 'connected').length;
      const installed = agentInventory.filter(row => row.installed && !row.fleet_only).length;
      const fleetOnly = agentInventory.filter(row => row.fleet_only).length;
      const notConnected = agentInventory.filter(row => row.status === 'installed_not_connected').map(row => row.agent);
      const noRecent = agentInventory.filter(row => row.status === 'installed_no_recent_records').map(row => row.agent);
      document.getElementById('agentSnapshot').innerHTML =
        '<table><tr><th>' + t('agent-snapshot-status-col', '状态') + '</th><th class="num">' + t('agent-snapshot-count-col', '数量') + '</th></tr>' +
        '<tr><td>' + t('agent-snapshot-installed', '已安装') + '</td><td class="num">' + fmtInt(installed) + '</td></tr>' +
        '<tr><td>' + t('agent-snapshot-connected', '已接入且有记录') + '</td><td class="num">' + fmtInt(connected) + '</td></tr>' +
        '<tr><td>' + t('agent-snapshot-fleet-only', '团队节点活动') + '</td><td class="num">' + fmtInt(fleetOnly) + '</td></tr>' +
        '<tr><td>' + t('agent-snapshot-not-connected', '已安装但未接入') + '</td><td class="num">' + fmtInt(notConnected.length) + '</td></tr>' +
        '<tr><td>' + t('agent-snapshot-no-recent', '已安装但无近期记录') + '</td><td class="num">' + fmtInt(noRecent.length) + '</td></tr>' +
        '</table>';

      const explain = [];
      const claude = agentInventory.find(row => row.agent === 'Claude Code');
      const openclaw = agentInventory.find(row => row.agent === 'OpenClaw');
      const antigravity = agentInventory.find(row => row.agent === 'Antigravity');
      if (claude && claude.status !== 'connected') {
        explain.push(t('missing-explain-cache', '本地缓存最近计算日期是 {date}。').replace('{date}', claude.cache_last_computed || 'unknown'));
      }
      const parsedNoRecent = agentInventory
        .filter(row => row.status === 'installed_no_recent_records' && row.agent !== 'Claude Code')
        .map(row => row.agent);
      if (parsedNoRecent.length) {
        explain.push(t('missing-explain-no-recent', '{list} 的采集器已识别本地结构，但当前窗口没有真实会话记录，因此不计入任务数。').replace('{list}', parsedNoRecent.join('、')));
      }
      if (openclaw) {
        explain.push(openclaw.status === 'connected'
          ? t('missing-explain-openclaw-connected', 'OpenClaw 已经接入：会从 session 索引和任务运行库读取记录。')
          : t('missing-explain-openclaw-disconnected', 'OpenClaw 已安装，但当前窗口没有可展示的近期 session/task。'));
      }
      if (antigravity) {
        explain.push(t('missing-explain-antigravity', 'Antigravity 已安装，但目前只识别到 IDE 数据和日志；还没有映射出可靠的任务/token 账本表。'));
      }
      const fleetOnlyAgents = agentInventory.filter(row => row.fleet_only).map(row => row.agent);
      if (fleetOnlyAgents.length) {
        explain.push(t('agent-fleet-activity-note', '来自团队节点活动记录；如果没有经过网关，不产生 token。') + ' ' + fleetOnlyAgents.join('、'));
      }
      const pendingAgents = agentInventory
        .filter(row => row.status === 'installed_not_connected' && row.agent !== 'Antigravity')
        .map(row => row.agent);
      if (pendingAgents.length) {
        explain.push(t('missing-explain-pending', '{list} 已安装，但当前只做安装识别；还没有接入可靠的会话/token 采集器。').replace('{list}', pendingAgents.join('、')));
      }
      if (!explain.length) explain.push(t('missing-explain-all-ok', '所有已识别 Agent 都有当前窗口账本记录。'));
      document.getElementById('missing-explain').innerHTML = explain.map(item => '<li>' + esc(item) + '</li>').join('');
    }

    function renderRankTable(rows, labelField, extraField) {
      const knownRows = rows.filter(hasKnownToken)
        .slice()
        .sort((a, b) => Number(b.total_tokens || 0) - Number(a.total_tokens || 0))
        .slice(0, 12);
      if (!knownRows.length) {
        return '<div class="empty">' + t('no-session-records', '暂无真实 token 记录。') + '</div>';
      }
      const maxTokens = Math.max(1, ...knownRows.map(row => Number(row.total_tokens || 0)));
      let html = '<table><tr><th>' + t('rank-col-name', '名称') + '</th><th class="num">' + t('rank-col-token', 'Token') + '</th><th class="num">' + t('rank-col-records', '记录') + '</th></tr>';
      for (const row of knownRows) {
        const pct = Math.max(2, Math.round((Number(row.total_tokens || 0) / maxTokens) * 100));
        const extraValue = extraField ? row[extraField] : row.latest_task;
        const extraText = Array.isArray(extraValue) ? extraValue.join(', ') : (extraValue || row.latest_task || '');
        html += '<tr>' +
          '<td><div class="agent-name">' + esc(row[labelField] || 'unknown') + '</div>' +
            '<div class="subtle">' + esc(extraText) + '</div></td>' +
          '<td><div class="num">' + fmtShort(row.total_tokens) + '</div><div class="meter"><span style="width:' + pct + '%"></span></div></td>' +
          '<td class="num">' + fmtInt(row.sessions || row.tasks || row.known_token_sessions || 0) + '</td>' +
        '</tr>';
      }
      html += '</table>';
      return html;
    }

    function renderActivityRankTable(rows, labelField, extraField) {
      const activityRows = rows
        .filter(row => Number(row.sessions || row.activity_count || 0) > 0)
        .slice()
        .sort((a, b) => Number(b.sessions || b.activity_count || 0) - Number(a.sessions || a.activity_count || 0))
        .slice(0, 12);
      if (!activityRows.length) {
        return '<div class="empty">' + t('no-fleet-activity-records', '尚未配置授权活动节点。') + '</div>';
      }
      let html = '<table><tr><th>' + t('rank-col-name', '名称') + '</th><th class="num">' + t('fleet-rank-col-activity', '活动') + '</th><th class="num">' + t('fleet-rank-col-non-success', '非成功') + '</th></tr>';
      for (const row of activityRows) {
        const extraValue = extraField ? row[extraField] : row.agents;
        const extraText = Array.isArray(extraValue) ? extraValue.join(', ') : (extraValue || '');
        html += '<tr>' +
          '<td><div class="agent-name">' + esc(row[labelField] || 'unknown') + '</div>' +
            '<div class="subtle">' + esc(extraText) + '</div></td>' +
          '<td class="num">' + fmtInt(row.sessions || row.activity_count || 0) + '</td>' +
          '<td class="num">' + fmtInt(row.n8n_non_success || 0) + '</td>' +
        '</tr>';
      }
      html += '</table>';
      return html;
    }

    function renderAgentOverviewRankTable(tokenRows, activityRows, extraField) {
      const groups = new Map();
      const ensure = agent => {
        const key = String(agent || 'unknown');
        if (!groups.has(key)) {
          groups.set(key, {
            agent: key,
            total_tokens: 0,
            known_token_sessions: 0,
            token_sessions: 0,
            activity_sessions: 0,
            n8n_non_success: 0,
            nodes: new Set(),
            projects: new Set(),
            latest_task: '',
          });
        }
        return groups.get(key);
      };
      for (const row of tokenRows || []) {
        const agent = row.agent || 'unknown';
        if (agent === 'unknown') continue;
        const group = ensure(agent);
        group.total_tokens += Number(row.total_tokens || 0);
        group.known_token_sessions += Number(row.known_token_sessions || 0);
        group.token_sessions += Number(row.sessions || row.tasks || row.known_token_sessions || 0);
        group.latest_task = row.latest_task || group.latest_task;
        const extraValue = extraField ? row[extraField] : row.latest_task;
        (Array.isArray(extraValue) ? extraValue : [extraValue]).filter(Boolean).forEach(item => group.nodes.add(item));
        (row.projects || []).forEach(item => group.projects.add(item));
      }
      for (const row of activityRows || []) {
        const agent = row.agent || 'unknown';
        if (agent === 'unknown') continue;
        const group = ensure(agent);
        group.activity_sessions += Number(row.sessions || row.activity_count || 0);
        group.n8n_non_success += Number(row.n8n_non_success || 0);
        const extraValue = extraField ? row[extraField] : row.projects;
        (Array.isArray(extraValue) ? extraValue : [extraValue]).filter(Boolean).forEach(item => group.nodes.add(item));
        (row.projects || []).forEach(item => group.projects.add(item));
      }

      const rows = Array.from(groups.values())
        .filter(row => row.agent !== 'unknown')
        .sort((a, b) =>
          Number(b.activity_sessions || 0) - Number(a.activity_sessions || 0) ||
          Number(b.total_tokens || 0) - Number(a.total_tokens || 0) ||
          a.agent.localeCompare(b.agent)
        )
        .slice(0, 12);
      if (!rows.length) {
        return '<div class="empty">' + t('no-session-records', '暂无会话记录。') + '</div>';
      }
      const maxActivity = Math.max(1, ...rows.map(row => Number(row.activity_sessions || 0)));
      let html = '<table><tr><th>' + t('rank-col-name', '名称') + '</th><th class="num">' + t('rank-col-token', 'Token') + '</th><th class="num">' + t('fleet-rank-col-activity', '活动') + '</th><th class="num">' + t('rank-col-data', '数据') + '</th></tr>';
      for (const row of rows) {
        const activityPct = Math.max(2, Math.round((Number(row.activity_sessions || 0) / maxActivity) * 100));
        const nodeText = Array.from(row.nodes || []).join(', ');
        const tokenKnown = Number(row.known_token_sessions || 0) > 0 || Number(row.total_tokens || 0) > 0;
        const tokenText = tokenKnown ? fmtShort(row.total_tokens) : t('unavailable', '不可用');
        const dataText = tokenKnown
          ? (row.activity_sessions ? 'Token + ' + t('agent-activity-label', '活动') : 'Token')
          : t('agent-activity-label', '活动');
        html += '<tr>' +
          '<td><div class="agent-name">' + esc(row.agent) + '</div><div class="subtle">' + esc(nodeText || row.latest_task || '') + '</div></td>' +
          '<td class="num">' + esc(tokenText) + '</td>' +
          '<td><div class="num">' + fmtInt(row.activity_sessions || row.token_sessions || 0) + '</div><div class="meter"><span style="width:' + activityPct + '%"></span></div></td>' +
          '<td class="num">' + esc(dataText) + '</td>' +
        '</tr>';
      }
      html += '</table>';
      return html;
    }

    function renderRankings(ledger) {
      const fleet = currentFleet();
      const useFleet = !!(fleet && fleet.totals && Number(fleet.totals.connected_nodes || 0) > 0);
      const agentRows = useFleet ? (fleet.agent_token_rank || []) : (ledger.by_agent || []);
      const agentActivityRows = useFleet ? (fleet.agent_activity_rank || []) : (ledger.by_agent || []);
      const nodeActivityRows = useFleet ? (fleet.node_activity_rank || []) : [];
      const projectRows = useFleet ? (fleet.project_token_rank || []) : (ledger.by_project || []);
      const modelRows = useFleet ? (fleet.model_token_rank || []) : (ledger.by_model || []);
      const activityRows = useFleet ? (fleet.project_activity_rank || []) : (ledger.by_project || []);

      document.getElementById('agent-token-rank').innerHTML =
        renderAgentOverviewRankTable(agentRows, agentActivityRows, useFleet ? 'nodes' : 'latest_task');
      document.getElementById('agent-activity-rank').innerHTML =
        renderActivityRankTable(agentActivityRows.filter(row => (row.agent || '') !== 'unknown'), 'agent', useFleet ? 'nodes' : 'projects');
      document.getElementById('node-activity-rank').innerHTML =
        renderActivityRankTable(nodeActivityRows.filter(row => (row.node || '') !== 'unknown'), 'node', 'agents');
      document.getElementById('project-token-rank').innerHTML =
        renderRankTable(projectRows.filter(row => (row.project || '') !== 'unknown'), 'project', 'agents');
      document.getElementById('model-token-rank').innerHTML =
        renderRankTable(modelRows.filter(r => (r.model || '') !== 'unknown'), 'model', 'agents');
      document.getElementById('activity-rank').innerHTML =
        renderActivityRankTable(activityRows.filter(row => (row.project || '') !== 'unknown'), 'project', 'agents');
    }

    function renderProjects(ledger) {
      let html = '<table><tr><th>' + t('project-col-project', '项目') + '</th><th>' + t('project-col-status', '状态') + '</th><th>' + t('project-col-agent', 'Agent') + '</th><th class="num">' + t('project-col-sessions', '会话/任务') + '</th><th class="num">' + t('project-col-active', '活跃') + '</th><th class="num">' + t('project-col-token', 'Token') + '</th><th>' + t('project-col-change', '代码改动') + '</th><th>' + t('project-col-latest', '最新任务') + '</th></tr>';
      const projectRows = (ledger.by_project || []).slice().sort((a, b) => {
        const au = (a.project || 'unknown') === 'unknown' ? 1 : 0;
        const bu = (b.project || 'unknown') === 'unknown' ? 1 : 0;
        if (au !== bu) return au - bu;
        const tokenDelta = Number(b.total_tokens || 0) - Number(a.total_tokens || 0);
        if (tokenDelta !== 0) return tokenDelta;
        const activeDelta = Number(b.active_sessions || 0) - Number(a.active_sessions || 0);
        if (activeDelta !== 0) return activeDelta;
        return new Date(b.latest_at || 0) - new Date(a.latest_at || 0);
      });
      for (const row of projectRows.slice(0, 30)) {
        const active = Number(row.active_sessions || 0) > 0;
        html += '<tr>' +
          '<td class="project">' + esc(row.project || 'unknown') + '<div class="subtle">' + fmtTime(row.latest_at) + '</div></td>' +
          '<td><span class="badge ' + (active ? 'ok' : 'warn') + '">' + (active ? t('project-status-active', '有进展') : t('project-status-recorded', '已记录')) + '</span></td>' +
          '<td>' + esc((row.agents || []).join(', ')) + '</td>' +
          '<td class="num">' + fmtInt(row.sessions) + '</td>' +
          '<td class="num">' + fmtInt(row.active_sessions) + '</td>' +
          '<td class="num">' + (hasKnownToken(row) ? fmtShort(row.total_tokens) : t('unavailable', '不可用')) + '</td>' +
          '<td>' + esc(fmtChange(row)) + '</td>' +
          '<td class="task">' + esc(row.latest_task || '—') + '</td>' +
        '</tr>';
      }
      html += '</table>';
      document.getElementById('projectTable').innerHTML = projectRows.length ? html : '<div class="empty">' + t('no-project-records', '暂无项目任务记录。') + '</div>';
    }

    function renderSessions(ledger) {
      let html = '<table><tr><th>' + t('session-col-time', '时间') + '</th><th>' + t('session-col-agent', 'Agent') + '</th><th>' + t('session-col-project', '项目') + '</th><th>' + t('session-col-status', '状态') + '</th><th>' + t('session-col-task', '任务') + '</th><th class="num">' + t('session-col-token', 'Token') + '</th><th>' + t('session-col-change', '代码改动') + '</th><th class="num">' + t('session-col-cost', '金额') + '</th></tr>';
      state.recentSessions = ledger.recent_sessions || [];
      for (const row of state.recentSessions) {
        const status = row.status || 'recorded';
        html += `<tr style="cursor: pointer;" onclick="openSessionDetail('${esc(row.session_id)}')">` +
          '<td>' + fmtTime(row.ended_at || row.started_at) + '</td>' +
          '<td><span class="agent-name">' + esc(row.agent) + '</span><div class="subtle">' + esc(row.source || '') + '</div></td>' +
          '<td class="project">' + esc(row.project || 'unknown') + '</td>' +
          '<td><span class="badge ' + badgeClass(status) + '">' + statusLabel(status) + '</span></td>' +
          '<td class="task">' + esc(row.task || '—') + '</td>' +
          '<td class="num">' + fmtTokenFor(row) + '</td>' +
          '<td>' + esc(fmtChange(row)) + '</td>' +
          '<td class="num">' + fmtCostFor(row) + '</td>' +
        '</tr>';
      }
      html += '</table>';
      document.getElementById('sessionTable').innerHTML = (ledger.recent_sessions || []).length ? html : '<div class="empty">' + t('no-session-records', '暂无会话记录。') + '</div>';
      const notes = (ledger.notes || []).concat((ledger.access_issues || []).map(item => item.source + ': ' + item.issue));
      document.getElementById('ledger-notes').innerHTML = notes.map(esc).join('<br>');
    }

    function renderConfigPaths() {
      const target = document.getElementById('configPaths');
      if (!target) return;
      const rows = [];
      if (state.lastFleet && state.lastFleet.config_path) {
        rows.push([t('config-path-fleet', '团队节点配置'), state.lastFleet.config_path]);
      }
      if (state.lastSubscriptions && state.lastSubscriptions.config_path) {
        rows.push([t('config-path-subscriptions', '订阅额度配置'), state.lastSubscriptions.config_path]);
      }
      if (state.lastFeishu && state.lastFeishu.config_path) {
        rows.push([t('config-path-feishu', '飞书提醒配置'), state.lastFeishu.config_path]);
      }
      if (!rows.length) {
        target.innerHTML = '<div class="empty">' + t('config-path-none', '暂无可展示的配置路径。') + '</div>';
        return;
      }
      target.innerHTML =
        '<table><tr><th>' + t('fleet-col-item', '项目') + '</th><th>' + t('fleet-config-path', '配置文件：') + '</th></tr>' +
        rows.map(([label, path]) => '<tr><td>' + esc(label) + '</td><td><code>' + esc(path) + '</code></td></tr>').join('') +
        '</table>';
    }

    function renderFleetNotes(data) {
      const target = document.getElementById('fleetNotes');
      if (!target) return;
      const notes = (data?.notes || []).concat((data?.access_issues || []).map(item => item.node + ': ' + item.issue));
      target.innerHTML = notes.length ? notes.map(esc).join('<br>') : t('fleet-notes-empty', '无团队节点备注。');
    }

    function renderNodeOps(data) {
      const target = document.getElementById('nodeOpsSummary');
      if (!target) return;
      const health = data?.node_health || {};
      const staleNodes = (health.stale_nodes || []).filter(Boolean);
      const unavailableNodes = (health.unavailable_nodes || []).filter(Boolean);
      const lines = [];
      if (unavailableNodes.length) {
        lines.push(t('node-ops-unavailable', '不可达节点：{nodes}').replace('{nodes}', unavailableNodes.join('、')));
      }
      if (staleNodes.length) {
        lines.push(t('node-ops-stale', '使用缓存或过期数据：{nodes}').replace('{nodes}', staleNodes.join('、')));
        lines.push(t('node-ops-action-readonly', '推荐改用只读账本服务；shared directory 文件只作为备用同步。'));
      }
      if (!lines.length) {
        lines.push(t('node-ops-healthy', '全部当前可信节点正常。'));
      }
      target.innerHTML = lines.map(line => '<div>' + esc(line) + '</div>').join('');
    }

    function renderFleet(data) {
      renderDemoModeBanner(data);
      state.lastFleet = data;
      const totals = data.totals || {};
      const health = data.node_health || {};
      const pct = (num, den) => den > 0 ? Math.max(0, Math.min(100, (Number(num || 0) / den) * 100)) : 0;
      const totalRecords = Number(totals.records || 0);
      const knownTokenRecords = Number(totals.known_token_records || 0);
      const rowSampleRecords = Number(totals.row_sample_records || 0);
      const tokenBreakdown = totals.token_breakdown || {};
      const realTokenRecords = Number(totals.real_token_records ?? tokenBreakdown.real_token_records ?? 0);
      const realTokenTotal = Number(totals.real_total_tokens ?? tokenBreakdown.real_total_tokens ?? 0);
      const estimatedTokenRecords = Number(totals.estimated_token_records ?? tokenBreakdown.estimated_token_records ?? 0);
      const estimatedTokenTotal = Number(totals.estimated_total_tokens ?? tokenBreakdown.estimated_total_tokens ?? 0);
      const unavailableTokenRecords = Number(totals.unavailable_token_records ?? tokenBreakdown.unavailable_token_records ?? 0);
      const excludedStaleTokenRecords = Number(totals.excluded_stale_token_records || 0);
      const excludedStaleTokenTotal = Number(totals.excluded_stale_total_tokens || 0);
      const connectedPct = pct(totals.connected_nodes || 0, totals.configured_nodes || 0);
      const tokenCoverage = pct(knownTokenRecords, Math.max(totalRecords, knownTokenRecords));
      const n8nExecutions = Number(totals.n8n_executions || 0);
      const n8nSuccessRate = n8nExecutions > 0 ? pct(totals.n8n_success || 0, n8nExecutions) : null;
      const configured = Number(health.configured_nodes ?? totals.configured_nodes ?? 0);
      const connected = Number(health.connected_nodes ?? totals.connected_nodes ?? 0);
      const currentDataNodeCount = Number(health.current_data_node_count ?? totals.current_data_nodes ?? 0);
      const staleNodeCount = Number(health.stale_node_count ?? totals.stale_nodes ?? 0);
      const issueCount = Number(health.issue_count ?? (data.access_issues || []).length);
      const healthTitle = health.status === 'not_configured'
        ? t('fleet-none-title', '未配置节点')
        : (health.complete ? t('fleet-complete-title', '数据完整') : t('fleet-partial-title', '数据不完整'));
      const healthDesc = health.complete
        ? t('fleet-complete-desc', '{connected}/{configured} 个节点已连接')
            .replace('{connected}', fmtInt(connected))
            .replace('{configured}', fmtInt(configured))
        : t('fleet-partial-desc', '{connected}/{configured} 个节点已连接 · 异常 {issues} 个')
            .replace('{connected}', fmtInt(connected))
            .replace('{configured}', fmtInt(configured))
            .replace('{issues}', fmtInt(issueCount));
      const unavailableNodes = (health.unavailable_nodes || []).filter(Boolean);
      const staleNodes = (health.stale_nodes || []).filter(Boolean);
      const healthDetail = [
        unavailableNodes.length
          ? t('fleet-unavailable-nodes', '异常节点：{nodes}').replace('{nodes}', unavailableNodes.join('、'))
          : '',
        staleNodes.length
          ? t('fleet-stale-nodes', '缓存/过期节点：{nodes}').replace('{nodes}', staleNodes.join('、'))
          : '',
      ].filter(Boolean).join(' · ');
      const healthBanner =
        '<div class="data-health-banner ' + (health.complete ? 'ok' : 'warn') + '">' +
          '<div><strong>' + esc(healthTitle) + '</strong><span>' + esc(healthDesc) + '</span>' +
            (healthDetail ? '<span>' + esc(healthDetail) + '</span>' : '') +
          '</div>' +
        '</div>';
      const gaugeCard = (label, value, percent, detail) =>
        '<div class="dashboard-card gauge-card">' +
          '<div class="dashboard-card-label">' + esc(label) + '</div>' +
          '<div class="dashboard-card-value">' + esc(value) + '</div>' +
          '<div class="meter"><span style="width:' + Math.round(percent || 0) + '%"></span></div>' +
          '<div class="dashboard-card-detail">' + esc(detail || '') + '</div>' +
        '</div>';
      const metricCard = (label, value, detail) =>
        '<div class="dashboard-card">' +
          '<div class="dashboard-card-label">' + esc(label) + '</div>' +
          '<div class="dashboard-card-value">' + esc(value) + '</div>' +
          '<div class="dashboard-card-detail">' + esc(detail || '') + '</div>' +
        '</div>';
      const recordDetail = [
        t('fleet-known-token-records', '有 token 的记录') + ' ' + fmtInt(knownTokenRecords),
        (rowSampleRecords > 0 && totalRecords > rowSampleRecords)
          ? t('fleet-row-sample-records', '已加载样本 {n}').replace('{n}', fmtInt(rowSampleRecords))
          : ''
      ].filter(Boolean).join(' · ');
      const tokenBreakdownDetail = [
        realTokenRecords > 0
          ? t('fleet-real-token-detail', '真实 {tokens} / {records} 条')
              .replace('{tokens}', fmtShort(realTokenTotal))
              .replace('{records}', fmtInt(realTokenRecords))
          : '',
        estimatedTokenRecords > 0
          ? t('fleet-estimated-token-detail', '估算 {tokens} / {records} 条')
              .replace('{tokens}', fmtShort(estimatedTokenTotal))
              .replace('{records}', fmtInt(estimatedTokenRecords))
          : '',
        unavailableTokenRecords > 0
          ? t('fleet-unavailable-token-detail', '不可用 {records} 条').replace('{records}', fmtInt(unavailableTokenRecords))
          : '',
        excludedStaleTokenRecords > 0 || excludedStaleTokenTotal > 0
          ? t('fleet-excluded-stale-detail', '已排除过期同步 {tokens} / {records} 条')
              .replace('{tokens}', fmtShort(excludedStaleTokenTotal))
              .replace('{records}', fmtInt(excludedStaleTokenRecords))
          : '',
      ].filter(Boolean).join(' · ') || t('fleet-nodes-token', '团队节点 token');
      document.getElementById('fleetSummary').innerHTML =
        '<h3>' + t('fleet-ops-title', '运行仪表盘') + '</h3>' +
        healthBanner +
        '<div class="dashboard-card-grid">' +
          gaugeCard(
            t('fleet-health-connected', '连接率'),
            Math.round(connectedPct) + '%',
            connectedPct,
            fmtInt(totals.connected_nodes || 0) + ' / ' + fmtInt(totals.configured_nodes || 0)
          ) +
          gaugeCard(
            t('fleet-health-trusted-nodes', '可信节点'),
            fmtInt(currentDataNodeCount) + ' / ' + fmtInt(configured),
            pct(currentDataNodeCount, configured),
            staleNodeCount > 0
              ? t('fleet-stale-nodes', '缓存/过期节点：{nodes}').replace('{nodes}', fmtInt(staleNodeCount))
              : t('fleet-complete-title', '数据完整')
          ) +
          gaugeCard(
            t('fleet-health-token-coverage', 'Token 覆盖率'),
            Math.round(tokenCoverage) + '%',
            tokenCoverage,
            fmtInt(knownTokenRecords) + ' / ' + fmtInt(Math.max(totalRecords, knownTokenRecords))
          ) +
          (n8nSuccessRate === null ? metricCard(t('fleet-health-n8n-success', 'n8n 成功率'), t('unavailable', '不可用'), t('fleet-n8n-executions', 'n8n 执行次数') + ' 0') : gaugeCard(
            t('fleet-health-n8n-success', 'n8n 成功率'),
            Math.round(n8nSuccessRate) + '%',
            n8nSuccessRate,
            fmtInt(totals.n8n_non_success || 0) + ' ' + t('fleet-rank-col-non-success', '非成功')
          )) +
          metricCard(t('fleet-health-records', '账本记录'), fmtInt(totalRecords), recordDetail) +
          metricCard(t('fleet-health-activity', '活动次数'), fmtInt(totals.activity_sessions || 0), t('fleet-connected-nodes', '已连接节点') + ' ' + fmtInt(totals.connected_nodes || 0)) +
          metricCard(t('fleet-health-token-total', '当前可信 Token'), knownTokenRecords ? fmtShort(totals.total_tokens || 0) : t('unavailable', '不可用'), tokenBreakdownDetail) +
          ((excludedStaleTokenRecords > 0 || excludedStaleTokenTotal > 0)
            ? metricCard(t('fleet-health-stale-known', '上次已知 Token'), fmtShort(excludedStaleTokenTotal), t('fleet-excluded-stale-detail', '已排除过期同步 {tokens} / {records} 条').replace('{tokens}', fmtShort(excludedStaleTokenTotal)).replace('{records}', fmtInt(excludedStaleTokenRecords)))
            : '') +
          metricCard(t('fleet-health-real-token-nodes', '真实 token 节点'), fmtInt(totals.real_token_nodes || 0), t('fleet-health-estimated-token-nodes', '估算 token 节点') + ' ' + fmtInt(totals.estimated_token_nodes || 0) + ' · ' + t('fleet-health-activity-only-nodes', '仅活动节点') + ' ' + fmtInt(totals.activity_only_nodes || 0)) +
          metricCard(t('fleet-health-n8n-workflows', 'n8n 工作流'), fmtInt(totals.n8n_workflows || 0), t('fleet-health-n8n-active', '活跃工作流') + ' ' + fmtInt(totals.n8n_active_workflows || 0)) +
        '</div>';

      const nodeRows = data.nodes || [];
      let nodeHtml = '<h3>' + t('fleet-node-status-title', '节点状态') + '</h3>';
      if (!nodeRows.length) {
        nodeHtml += '<div class="empty" style="margin-top:10px;">' + t('no-fleet-records', '尚未配置授权团队节点。') + '</div>';
      } else {
        nodeHtml += '<div class="node-card-list">';
        for (const row of nodeRows) {
          const status = row.status || 'unknown';
          const summary = row.summary && typeof row.summary === 'object' ? row.summary : {};
          const tokenTotal = Number(row.token_total || 0);
          const currentIncluded = row.current_data_included !== false;
          const tokenLabel = currentIncluded
            ? t('fleet-node-token', 'Token')
            : t('fleet-node-last-known-token', '上次已知');
          const activityCount = Number(row.activity_count || 0);
          const costValue = Number(row.known_cost_usd || 0);
          const latestAt = row.latest_at || summary.latest_at || row.exported_at || row.queried_at;
          const cacheAge = row.stale_ledger_cache && row.ledger_cache_age_seconds !== undefined
            ? t('fleet-node-cache-age', '缓存 {n} 秒').replace('{n}', fmtInt(row.ledger_cache_age_seconds || 0))
            : '';
          const detailParts = [
            row.source_type || 'smart_gateway',
            dataQualityLabel(row.data_quality),
            row.stale_ledger_cache ? t('fleet-cache-stale', '使用上次成功同步') : '',
            row.export_stale ? t('fleet-export-stale', '导出已过期') : '',
            currentIncluded ? '' : t('fleet-node-excluded-current', '未计入当前总量'),
            cacheAge,
            (row.records !== undefined ? t('fleet-rank-col-records', '记录') + ' ' + fmtInt(row.records || 0) : ''),
            summary.executions ? t('fleet-n8n-executions', 'n8n 执行次数') + ' ' + fmtInt(summary.executions) : '',
          ].filter(Boolean);
          const issueParts = [];
          if (row.issue) {
            issueParts.push('<strong>' + esc(t('fleet-node-issue', '错误原因')) + '</strong><span>' + esc(row.issue) + '</span>');
          }
          const operatorHint = row.operator_hint || (row.export_stale ? t('fleet-node-stale-action', '优先安装只读账本服务，让主节点主动拉取；暂用 shared directory 时请恢复每小时导出或手动重新导出。') : '');
          if (operatorHint) {
            issueParts.push('<strong>' + esc(t('fleet-node-action', '处理建议')) + '</strong><span>' + esc(operatorHint) + '</span>');
          }
          const issueHtml = issueParts.length
            ? '<div class="node-card-issue">' + issueParts.join('') + '</div>'
            : '';
          nodeHtml += '<article class="node-card">' +
            '<div class="node-card-main">' +
              '<div><div class="agent-name">' + esc(row.node || 'unknown') + '</div><div class="subtle">' + esc(detailParts.join(' · ')) + '</div></div>' +
              '<span class="badge ' + badgeClass(status) + '">' + esc(nodeStatusLabel(status)) + '</span>' +
            '</div>' +
            '<div class="node-card-metrics">' +
              '<div><strong>' + fmtInt(row.records || 0) + '</strong><span>' + t('fleet-rank-col-records', '记录') + '</span></div>' +
              '<div><strong>' + (tokenTotal > 0 ? fmtShort(tokenTotal) : t('unavailable', '不可用')) + '</strong><span>' + tokenLabel + '</span></div>' +
              '<div><strong>' + fmtInt(activityCount) + '</strong><span>' + t('fleet-node-activity', '活动') + '</span></div>' +
              '<div><strong>' + fmtTime(latestAt) + '</strong><span>' + t('fleet-rank-col-latest', '最近') + '</span></div>' +
            '</div>' +
            (costValue > 0 ? '<div class="node-card-cost">' + esc(t('fleet-node-cost', '成本')) + ' $' + esc(fmtShort(costValue)) + '</div>' : '') +
            issueHtml +
          '</article>';
        }
        nodeHtml += '</div>';
      }

      document.getElementById('fleetNodeStatus').innerHTML = nodeHtml;
      renderNodeOps(data);
      renderFleetNotes(data);
      renderConfigPaths();
    }

    function subscriptionStatusLabel(status) {
      const labels = {
        ok: state.settings.lang === 'zh' ? '正常' : 'Healthy',
        renewal_due: state.settings.lang === 'zh' ? '需续费' : 'Due',
        renewal_soon: state.settings.lang === 'zh' ? '临近续费' : 'Soon',
        quota_low: state.settings.lang === 'zh' ? '额度偏低' : 'Low Quota',
        quota_unknown: state.settings.lang === 'zh' ? '额度未知' : 'Unknown Quota'
      };
      return labels[status] || status;
    }

    function subscriptionBadge(status) {
      if (status === 'ok') return 'ok';
      if (status === 'renewal_due' || status === 'quota_low') return 'err';
      return 'warn';
    }

    function renderSubscriptions(data) {
      renderDemoModeBanner(data);
      state.lastSubscriptions = data;
      const totals = data.totals || {};
      const plans = data.plans || [];
      renderSubscriptionAlerts(data);
      const datedPlans = plans
        .filter(plan => plan.renewal_at)
        .slice()
        .sort((a, b) => Number(a.days_to_renewal ?? 9999) - Number(b.days_to_renewal ?? 9999));
      const nextPlan = datedPlans[0];
      const nextRenewalText = nextPlan
        ? (nextPlan.name || nextPlan.id || t('unnamed-plan', '未命名计划')) + ' · ' + fmtTime(nextPlan.renewal_at)
        : t('unavailable', '不可用');
      const alertText = Number(totals.alerts || 0) > 0
        ? fmtInt(totals.alerts || 0) + ' ' + t('sub-alerts-label', '提醒项')
        : t('sub-alerts-clear', '暂无提醒');
      const quotaText = Number(totals.quota_alerts || 0) > 0
        ? fmtInt(totals.quota_alerts || 0) + ' ' + t('sub-quota-label', '额度状态')
        : t('sub-alerts-clear', '暂无提醒');
      document.getElementById('subSummary').innerHTML =
        '<h3>' + t('sub-summary-title', '订阅状态') + '</h3>' +
        '<div class="dashboard-card-grid subscription-summary">' +
          '<div class="dashboard-card"><div class="dashboard-card-label">' + t('sub-plans-label', '订阅计划') + '</div><div class="dashboard-card-value">' + fmtInt(totals.plans || 0) + '</div><div class="dashboard-card-detail">' + esc(t('sub-plans-label', '订阅计划')) + '</div></div>' +
          '<div class="dashboard-card"><div class="dashboard-card-label">' + t('sub-alerts-label', '提醒项') + '</div><div class="dashboard-card-value">' + esc(alertText) + '</div><div class="dashboard-card-detail">' + t('sub-renewal-label', '最近续费') + ' ' + fmtInt(totals.renewal_alerts || 0) + '</div></div>' +
          '<div class="dashboard-card"><div class="dashboard-card-label">' + t('sub-renewal-label', '最近续费') + '</div><div class="dashboard-card-value small">' + esc(nextRenewalText) + '</div><div class="dashboard-card-detail">' + esc(nextPlan && nextPlan.billing_amount ? fmtBilling(nextPlan) : '') + '</div></div>' +
          '<div class="dashboard-card"><div class="dashboard-card-label">' + t('sub-quota-label', '额度状态') + '</div><div class="dashboard-card-value">' + esc(quotaText) + '</div><div class="dashboard-card-detail">' + (Number(totals.quota_alerts || 0) ? t('agent-snapshot-status-col', '状态') : t('sub-alerts-normal-item', '全部正常')) + '</div></div>' +
        '</div>';
      renderConfigPaths();

      const advice = data.routing_advice || {};
      const preferred = advice.preferred || [];
      const avoid = advice.avoid || [];
      if (!preferred.length && !avoid.length) {
        document.getElementById('routing-advice').innerHTML =
          '<h3>' + t('routing-advice-title', '路由建议') + '</h3><div class="subtle" style="margin-top:8px;">' +
          t('routing-advice-empty', '尚未录入带 provider_key 和真实额度的计划，因此不会改变网关路由。') +
          '</div>';
      } else {
        let html = '<h3>' + t('routing-advice-title', '路由建议') + '</h3>';
        if (avoid.length) {
          html += '<div style="margin-top:8px;"><strong>' + t('routing-avoid', '避让：') + '</strong>' + esc(avoid.map(item => item.provider_key + '（' + item.reason + '）').join('、')) + '</div>';
        }
        if (preferred.length) {
          html += '<div style="margin-top:8px;"><strong>' + t('routing-prefer', '优先：') + '</strong>' + esc(preferred.map(item => item.provider_key + '（' + t('routing-rem-pct', '剩余 {n}%').replace('{n}', item.remaining_pct ?? 'N/A') + '）').join('、')) + '</div>';
        }
        document.getElementById('routing-advice').innerHTML = html;
      }

      if (!plans.length) {
        document.getElementById('planTable').innerHTML =
          '<div class="empty">' + t('no-plan-records', '尚未录入真实订阅、续费日或额度上限，所以这里不显示任何虚拟计划。') + '</div>';
        return;
      }
      let html = '<table><tr><th>' + t('plan-id-label', '计划') + '</th><th>' + t('plan-status-label', '状态') + '</th><th>' + t('plan-provider-label', 'Provider') + '</th><th>' + t('plan-fee-label', '费用') + '</th><th>' + t('plan-renewal-label', '续费/到期') + '</th><th>' + t('plan-autorenew-label', '自动续费') + '</th><th class="num">' + t('plan-remaining-label', '剩余') + '</th></tr>';
      for (const plan of plans) {
        const autoRenew = plan.auto_renew === true ? t('yes', '是') : (plan.auto_renew === false ? t('no', '否') : t('unavailable', '不可用'));
        html += '<tr>' +
          '<td><div class="agent-name">' + esc(plan.name || plan.id || 'N/A') + '</div><div class="subtle">' + esc(plan.agent || '') + '</div></td>' +
          '<td><span class="badge ' + subscriptionBadge(plan.status) + '">' + subscriptionStatusLabel(plan.status) + '</span></td>' +
          '<td><div>' + esc(plan.provider_key || plan.provider || '—') + '</div><div class="subtle">' + esc(plan.model || '') + '</div></td>' +
          '<td>' + esc(fmtBilling(plan)) + '</td>' +
          '<td>' + (plan.renewal_at ? fmtTime(plan.renewal_at) : t('unavailable', '不可用')) + '</td>' +
          '<td>' + esc(autoRenew) + '</td>' +
          '<td class="num">' + fmtPct(plan.quota_remaining_pct) + '</td>' +
        '</tr>';
      }
      html += '</table>';
      document.getElementById('planTable').innerHTML = html;
    }

    function renderSubscriptionAlerts(data) {
      const plans = data.plans || [];
      const alerts = plans
        .filter(plan => plan.status && plan.status !== 'ok')
        .sort((a, b) => Number(a.days_to_renewal ?? 9999) - Number(b.days_to_renewal ?? 9999))
        .slice(0, 4);
      const totals = data.totals || {};
      const target = document.getElementById('subscriptionAlerts');
      if (!target) return;
      if (!alerts.length) {
        target.innerHTML =
          '<div class="overview-alert-title"><strong>' + t('sub-alerts-none-title', '订阅提醒') + '</strong><span class="subtle">' + t('sub-alerts-none-desc', '暂无临近续费或额度提醒') + '</span></div>' +
          '<div class="alert-items"><div class="alert-item"><strong>' + t('sub-alerts-normal-item', '全部正常') + '</strong><span class="subtle">' + t('sub-alerts-plans-count', '计划 {n} 个').replace('{n}', fmtInt(totals.plans || 0)) + '</span></div></div>' +
          '<a class="text-link" href="#settings">' + t('sub-alerts-view-detail', '查看明细') + '</a>';
        return;
      }
      target.innerHTML =
        '<div class="overview-alert-title"><strong>' + t('sub-alerts-active-title', '订阅提醒') + '</strong><span class="subtle">' +
          t('sub-alerts-active-desc', '{alerts} 个提醒 · 续费 {renewals}')
            .replace('{alerts}', fmtInt(totals.alerts || alerts.length))
            .replace('{renewals}', fmtInt(totals.renewal_alerts || 0)) + '</span></div>' +
        '<div class="alert-items">' + alerts.map(plan => {
          const days = plan.days_to_renewal === null || plan.days_to_renewal === undefined
            ? t('sub-alerts-date-unknown', '日期未知')
            : (Number(plan.days_to_renewal) <= 0 ? t('sub-alerts-date-today', '今天到期/续费') : t('sub-alerts-date-days', '{n} 天后').replace('{n}', plan.days_to_renewal));
          const billing = fmtBilling(plan);
          return '<div class="alert-item">' +
            '<strong>' + esc(plan.name || plan.id || t('unnamed-plan', '未命名计划')) + '</strong>' +
            '<span class="badge ' + subscriptionBadge(plan.status) + '" style="margin-top:6px;">' + subscriptionStatusLabel(plan.status) + '</span>' +
            '<div class="subtle" style="margin-top:6px;">' + esc(days) + ' · ' + esc(billing) + '</div>' +
          '</div>';
        }).join('') + '</div>' +
        '<a class="text-link" href="#settings">' + t('sub-alerts-view-detail', '查看明细') + '</a>';
    }

    async function loadLedger(loadId = state.activeLoadId) {
      const ledger = await fetchJson(base + '/agent-ledger?days=' + state.settings.days + '&limit=' + state.settings.limit, 45000);
      if (loadId !== state.activeLoadId) return { status: 'ignored' };
      applyLedger(ledger, loadId);
      return { status: 'done' };
    }

    function scheduleLedgerRetry(delayMs = 4000, loadId = state.activeLoadId) {
      clearTimeout(state.ledgerRetryTimer);
      state.ledgerRetryTimer = setTimeout(async () => {
        if (loadId !== state.activeLoadId) return;
        if (state.loading) {
          scheduleLedgerRetry(delayMs, loadId);
          return;
        }
        try {
          await loadLedger(loadId);
          const fleet = currentFleet();
          if (fleet && (fleet.nodes || []).some(node => node.status === 'refreshing')) {
            await loadFleet(loadId);
          }
        } catch (error) {
          showLedgerLoading(t('ledger-timeout-or-syncing', '账本仍在同步或读取超时') + '：' + error.message);
        }
      }, delayMs);
    }

    // P6: 抽取渲染逻辑, 供 loadLedger 和 SSE 推送复用
    function applyLedger(ledger, loadId = state.activeLoadId) {
      if (loadId !== state.activeLoadId) return;
      renderDemoModeBanner(ledger);
      if (ledger && ledger._refreshing && !(ledger.totals && ledger.totals.sessions)) {
        showLedgerLoading(t('ledger-background-syncing', '本机 Agent 账本仍在后台扫描，完成后会自动补齐明细。'));
        scheduleLedgerRetry(4000, loadId);
        return;
      }
      clearTimeout(state.ledgerRetryTimer);
      state.lastLedger = ledger;
      state.lastLedgerLoadId = loadId;
      document.getElementById('loading').style.display = 'none';
      document.getElementById('content').style.display = 'block';
      if (!state.fleetLoading || currentFleet()) {
        renderKpis(ledger);
      }
      renderInventory(ledger);
      renderProjects(ledger);
      renderSessions(ledger);
      populateAgentFilter(ledger);
      const fleet = currentFleet();
      if (fleet && (fleet.nodes || []).some(node => node.status === 'refreshing')) {
        loadFleet(loadId).catch(() => {});
      }
    }

    // P6: SSE 推送 — autoRefresh 开启时优先用, 失败自动回退轮询
    function connectSse() {
      if (state.eventSource) { try { state.eventSource.close(); } catch (e) {} }
      if (!window.EventSource) { return false; }  // 浏览器不支持, 用轮询
      const url = base + '/stream/ledger?days=' + state.settings.days + '&limit=' + state.settings.limit;
      let es;
      try {
        es = new EventSource(url);
      } catch (e) {
        return false;
      }
      state.eventSource = es;
      es.addEventListener('ledger', (e) => {
        try {
          const ledger = JSON.parse(e.data);
          applyLedger(ledger, state.activeLoadId);
          // SSE 活跃, 关闭轮询计时器 (避免重复刷新)
          clearTimeout(state.refreshTimer);
          state.nextRefreshAt = null;
          updateRefreshState();
        } catch (err) { /* 解析失败忽略, 等下一条 */ }
      });
      es.onerror = () => {
        try { es.close(); } catch (e2) {}
        state.eventSource = null;
        // SSE 断开, 回退到轮询
        if (state.settings.autoRefresh && !state.refreshTimer) {
          scheduleRefresh();
        }
      };
      return true;
    }

    function disconnectSse() {
      if (state.eventSource) {
        try { state.eventSource.close(); } catch (e) {}
        state.eventSource = null;
      }
    }

    async function loadSubscriptions() {
      const data = await fetchJson(base + '/subscription-ledger', 15000);
      renderSubscriptions(data);
    }

    function renderFeishuReminder(data) {
      renderDemoModeBanner(data);
      state.lastFeishu = data;
      const labels = {
        app_id: 'App ID',
        app_secret: 'App Secret',
        receive_id_type: t('feishu-label-receive-type', '接收方类型'),
        receive_id: t('feishu-label-receive-id', '接收方 ID')
      };
      const missing = data.missing || [];
      const missingText = missing.length ? missing.map(item => labels[item] || item).join('、') : t('feishu-none', '无');
      const badge = data.ready_to_send
        ? '<span class="badge ok">' + t('feishu-status-ready', '可发送') + '</span>'
        : '<span class="badge warn">' + t('feishu-status-pending', '待配置') + '</span>';
      const recipientLabel = data.receive_id_present
        ? esc((data.recipient_name || t('feishu-configured', '已配置')) + ' · ' + (data.receive_id_type || '') + (data.receive_id_masked ? ' · ' + data.receive_id_masked : ''))
        : t('feishu-missing', '缺失');
      const windows = data.reminder_windows || [];
      const windowRows = windows.map(item =>
        '<tr>' +
          '<td>' + esc(item.name || item.id || t('unnamed-plan', '未命名')) + '</td>' +
          '<td>' + (item.renewal_at ? fmtTime(item.renewal_at) : t('unavailable', '不可用')) + '</td>' +
          '<td><input class="feishu-plan-warning" data-plan-id="' + esc(item.id || '') + '" type="number" min="0" max="365" step="1" value="' + esc(item.warning_days ?? data.default_renewal_warning_days ?? 7) + '" /></td>' +
          '<td>' + esc(item.remind_start_date || t('unavailable', '不可用')) + '</td>' +
        '</tr>'
      ).join('');
      document.getElementById('feishuConfig').innerHTML =
        '<div style="margin-bottom:8px;">' + badge + '</div>' +
        '<table><tr><th>' + t('fleet-col-item', '项目') + '</th><th>' + t('agent-snapshot-status-col', '状态') + '</th></tr>' +
        '<tr><td>App ID</td><td>' + (data.app_id_present ? t('feishu-configured', '已配置') : t('feishu-missing', '缺失')) + '</td></tr>' +
        '<tr><td>App Secret</td><td>' + (data.app_secret_present ? t('feishu-configured', '已配置') : t('feishu-missing', '缺失')) + '</td></tr>' +
        '<tr><td>' + t('feishu-receive-label', '接收方') + '</td><td>' + recipientLabel + '</td></tr>' +
        '<tr><td>' + t('feishu-daily-check', '每日检查') + '</td><td>' + esc(
            t('feishu-daily-check-time', '{tz} {hour}:00 后')
              .replace('{tz}', data.timezone || 'Asia/Shanghai')
              .replace('{hour}', String(data.reminder_hour ?? 9).padStart(2, '0'))
          ) + '</td></tr>' +
        '<tr><td>' + t('feishu-default-advance', '默认提前') + '</td><td>' + esc(
            t('feishu-default-advance-days', '{n} 天').replace('{n}', data.default_renewal_warning_days ?? 7)
          ) + '</td></tr>' +
        '<tr><td>' + t('feishu-alerts-count', '飞书提醒项') + '</td><td>' + fmtInt(data.feishu_alerts || 0) + '</td></tr>' +
        '<tr><td>' + t('feishu-last-sent', '上次发送') + '</td><td>' + esc(data.last_sent_date || t('feishu-none', '无')) + '</td></tr>' +
        '<tr><td>' + t('feishu-missing-fields', '缺少') + '</td><td>' + esc(missingText) + '</td></tr>' +
        '</table>' +
        '<div class="control-grid" style="grid-template-columns: repeat(3, minmax(160px, 1fr)); margin-top:12px;">' +
          '<div class="control"><label for="feishu-default-warning-days">' + t('feishu-default-days-input', '默认提前天数') + '</label><input id="feishu-default-warning-days" type="number" min="0" max="365" step="1" value="' + esc(data.default_renewal_warning_days ?? 7) + '" /></div>' +
          '<div class="control"><label for="feishu-reminder-hour">' + t('feishu-check-hour-input', '每日检查小时') + '</label><input id="feishu-reminder-hour" type="number" min="0" max="23" step="1" value="' + esc(data.reminder_hour ?? 9) + '" /></div>' +
          '<div class="control"><div class="control-title">' + t('plan-reset-label', '保存') + '</div><button id="save-feishu-settings" class="setting-button">' + t('feishu-save-btn', '保存提醒设置') + '</button><div id="feishu-save-status" class="subtle"></div></div>' +
        '</div>' +
        (windowRows ? '<div class="table-wrap" style="margin-top:12px;"><table><tr><th>' + t('feishu-window-plan', '计划') + '</th><th>' + t('feishu-window-renewal', '续费/到期') + '</th><th>' + t('feishu-window-advance', '提前天数') + '</th><th>' + t('feishu-window-start', '开始提醒') + '</th></tr>' + windowRows + '</table></div>' : '') +
        '<div style="margin-top:10px; white-space:pre-wrap;">' + esc(data.preview || '') + '</div>';
      const saveButton = document.getElementById('save-feishu-settings');
      if (saveButton) saveButton.addEventListener('click', saveFeishuReminderSettings);
      renderConfigPaths();
    }

    async function saveFeishuReminderSettings() {
      const status = document.getElementById('feishu-save-status');
      if (status) status.textContent = t('feishu-save-status-saving', '保存中...');
      const planWarningDays = {};
      for (const input of document.querySelectorAll('.feishu-plan-warning')) {
        const planId = input.dataset.planId;
        if (!planId) continue;
        planWarningDays[planId] = Math.max(0, Math.min(365, Number(input.value || 0)));
      }
      const payload = {
        default_renewal_warning_days: Math.max(0, Math.min(365, Number(document.getElementById('feishu-default-warning-days')?.value || 7))),
        reminder_hour: Math.max(0, Math.min(23, Number(document.getElementById('feishu-reminder-hour')?.value || 9))),
        plan_warning_days: planWarningDays
      };
      try {
        const data = await postJson(base + '/feishu-reminder/settings', payload, 15000);
        renderFeishuReminder(data);
        const nextStatus = document.getElementById('feishu-save-status');
        if (nextStatus) nextStatus.textContent = t('feishu-save-status-saved', '已保存');
      } catch (error) {
        if (status) status.textContent = t('feishu-save-status-failed', '保存失败：') + error.message;
      }
    }

    async function loadFeishuReminder() {
      const data = await fetchJson(base + '/feishu-reminder', 15000);
      renderFeishuReminder(data);
    }

    function loadOptionalPanels(loadId = state.activeLoadId) {
      Promise.allSettled([loadSubscriptions(), loadFeishuReminder()]).then(results => {
        if (loadId !== state.activeLoadId) return;
        if (results[0].status === 'rejected') {
          document.getElementById('subSummary').innerHTML = '<div class="empty">' + t('sub-read-failed', '订阅状态读取失败：') + esc(results[0].reason.message) + '</div>';
          document.getElementById('subscriptionAlerts').innerHTML =
            '<div class="overview-alert-title"><strong>' + t('sub-alerts-none-title', '订阅提醒') + '</strong><span class="subtle">' + t('sub-read-failed', '订阅状态读取失败：') + esc(results[0].reason.message) + '</span></div>' +
            '<div class="alert-items"><div class="alert-item"><strong>' + esc(t('unavailable', '不可用')) + '</strong><span class="subtle">' + esc(t('routing-advice-unavailable', '路由建议暂不可用。')) + '</span></div></div>' +
            '<a class="text-link" href="#settings">' + t('sub-alerts-view-detail', '查看明细') + '</a>';
          document.getElementById('routing-advice').innerHTML = '<div class="empty">' + t('routing-advice-unavailable', '路由建议暂不可用。') + '</div>';
          document.getElementById('planTable').innerHTML = '<div class="empty">' + t('plan-table-unavailable', '计划明细暂不可用。') + '</div>';
        }
        if (results[1].status === 'rejected') {
          document.getElementById('feishuConfig').innerHTML = '<div class="empty">' + t('feishu-read-failed', '飞书提醒状态读取失败：') + esc(results[1].reason.message) + '</div>';
        }
      });
    }

    async function exportMonthlyReport() {
      const button = document.getElementById('exportMonthlyReport');
      const target = document.getElementById('monthlyReportStatus');
      if (!button || !target) return;
      button.disabled = true;
      target.textContent = t('monthly-report-running', '正在生成月报…');
      try {
        const data = await postJson(
          base + '/reports/monthly-usage?days=' + state.settings.days + '&limit=' + state.settings.limit,
          {},
          60000
        );
        const detail = [
          data.path ? '<code>' + esc(data.path) + '</code>' : '',
          data.total_tokens ? 'Token ' + fmtShort(data.total_tokens) : '',
        ].filter(Boolean).join('<br>');
        target.innerHTML = esc(t('monthly-report-done', '已生成：')) + detail;
      } catch (error) {
        target.innerHTML = esc(t('monthly-report-failed', '生成失败：')) + esc(error.message);
      } finally {
        button.disabled = false;
      }
    }

    async function loadFleet(loadId = state.activeLoadId) {
      state.fleetLoading = true;
      state.fleetLoadFailed = false;
      state.fleetLoadError = '';
      try {
        const data = await fetchJson(base + '/fleet-ledger?days=' + state.settings.days + '&limit=' + state.settings.limit, 60000);
        if (loadId !== state.activeLoadId) return { status: 'ignored' };
        state.fleetLoadFailed = false;
        state.fleetLoadError = '';
        state.lastFleetLoadId = loadId;
        renderFleet(data);
        document.getElementById('loading').style.display = 'none';
        renderKpis(state.lastLedger || { window_days: state.settings.days, totals: {} });
        if (state.lastLedger && state.lastLedgerLoadId === loadId) {
          renderInventory(state.lastLedger);
          populateAgentFilter(state.lastLedger);
        }
        return { status: 'done' };
      } finally {
        if (loadId === state.activeLoadId) {
          state.fleetLoading = false;
        }
      }
    }

    function showLedgerLoading(message) {
      document.getElementById('loading').style.display = 'block';
      document.getElementById('loading').innerHTML = esc(message);
    }

    function startLedgerLoad(loadId = state.activeLoadId) {
      if (state.ledgerPromise && state.ledgerPromiseLoadId === loadId) return state.ledgerPromise;
      state.ledgerPromiseLoadId = loadId;
      state.ledgerPromise = loadLedger(loadId)
        .then(result => result || { status: 'done' })
        .catch(error => ({ status: 'error', error }))
        .finally(() => {
          if (state.ledgerPromiseLoadId === loadId) {
            state.ledgerPromise = null;
            state.ledgerPromiseLoadId = null;
          }
        });
      return state.ledgerPromise;
    }

    async function load(options = {}) {
      if (state.loading) {
        state.pendingLoadOptions = { ...options, skipSchedule: true };
        if (options.manual || options.force) {
          state.activeLoadId += 1;
          state.fleetLoading = false;
          state.fleetLoadFailed = false;
          state.fleetLoadError = '';
        }
        return;
      }
      const loadId = state.activeLoadId + 1;
      state.activeLoadId = loadId;
      state.lastLedgerLoadId = null;
      state.lastFleetLoadId = null;
      state.loading = true;
      state.fleetLoading = true;
      state.fleetLoadFailed = false;
      state.fleetLoadError = '';
      document.getElementById('content').style.display = 'block';
      showLedgerLoading(t('syncing-agent-ledger', '正在读取团队节点和本机 Agent 账本。'));
      renderWindowLoadingState();
      updateRefreshState();
      try {
        await loadStatus();
        if (loadId !== state.activeLoadId) return;
      } catch (error) {
        if (loadId !== state.activeLoadId) return;
        document.getElementById('healthPill').innerHTML = '<span class="dot err"></span><span>' + t('sync-failed', '连接失败') + '</span>';
        document.getElementById('stats').innerHTML = '<h3>' + t('provider-requests', 'Provider 请求') + '</h3><div class="empty" style="margin-top:10px;">' + t('read-failed', '读取失败：') + esc(error.message) + '</div>';
        document.getElementById('config').innerHTML = '<h3>' + t('routing-config', '路由配置') + '</h3><div class="empty" style="margin-top:10px;">' + t('read-failed', '读取失败：') + esc(error.message) + '</div>';
      }

      const ledgerPromise = startLedgerLoad(loadId);

      const fleetResult = await Promise.allSettled([loadFleet(loadId)]);
      if (loadId !== state.activeLoadId) return;
      if (fleetResult[0].status === 'rejected') {
        state.fleetLoadFailed = true;
        state.fleetLoadError = fleetResult[0].reason?.message || String(fleetResult[0].reason || '');
        document.getElementById('fleetSummary').innerHTML = '<div class="empty">' + t('fleet-read-failed', '团队节点读取失败：') + esc(fleetResult[0].reason.message) + '</div>';
        document.getElementById('fleetNodeStatus').innerHTML = '<div class="empty">' + t('fleet-node-status-unavailable', '团队节点状态暂不可用。') + '</div>';
        document.getElementById('nodeOpsSummary').innerHTML = '<div class="empty">' + t('fleet-read-failed', '团队节点读取失败：') + esc(fleetResult[0].reason.message) + '</div>';
      }
      if (state.lastLedger && state.lastLedgerLoadId === loadId) {
        renderKpis(state.lastLedger);
      }
      loadOptionalPanels(loadId);

      try {
        const result = await Promise.race([
          ledgerPromise,
          new Promise(resolve => setTimeout(() => resolve({ status: 'timeout' }), 12000))
        ]);
        if (loadId !== state.activeLoadId) return;
        if (result.status === 'timeout') {
          showLedgerLoading(t('ledger-background-syncing', '本机 Agent 账本仍在后台扫描，完成后会自动补齐明细。'));
          ledgerPromise.then(lateResult => {
            if (loadId !== state.activeLoadId) return;
            if (lateResult.status === 'error') {
              document.getElementById('loading').style.display = 'block';
              document.getElementById('loading').innerHTML =
                '<span class="warn">' + t('ledger-read-failed', '账本后台读取失败') + '</span><br><code>' + esc(lateResult.error.message) + '</code>';
            }
          });
        } else if (result.status === 'error') {
          throw result.error;
        }
      } catch (error) {
        if (loadId !== state.activeLoadId) return;
        document.getElementById('loading').style.display = 'block';
        document.getElementById('loading').innerHTML =
          '<span class="warn">' + t('ledger-timeout-or-syncing', '账本仍在同步或读取超时') + '</span><br><code>' + esc(error.message) + '</code>';
      } finally {
        const isCurrentLoad = loadId === state.activeLoadId;
        state.loading = false;
        const pendingLoadOptions = state.pendingLoadOptions;
        state.pendingLoadOptions = null;
        if (pendingLoadOptions) {
          window.setTimeout(() => load(pendingLoadOptions), 0);
        } else if (isCurrentLoad && !options.skipSchedule) {
          scheduleRefresh();
        }
        if (isCurrentLoad) updateRefreshState();
        updateIcons();
      }
    }

    bindNavigation();
    bindSettings();
    bindFilters();   // P4
    applySettings();
    applyLanguage(); // Apply user-facing translations on initial script load
    renderPlaceholders();
    setActivePage(decodeURIComponent((location.hash || '#overview').slice(1)) || 'overview', { updateHash: false, scroll: false });
    window.addEventListener('resize', () => {
      if (state.activePage === 'trends') renderTrendChart();
    });
    if (state.settings.displayMode) {
      setActivePage('overview', { updateHash: true, behavior: 'auto' });
    }
    window.setTimeout(() => load({ skipSchedule: false }), 250);

    // ── P4: 全局筛选绑定 ──────────────────────────────────
    function bindFilters() {
      // 时间筛选 (顶部栏 + 设置页同步)
      document.querySelectorAll('#daysGroup .btn-sm, #settDays .btn-sm').forEach(btn => {
        btn.addEventListener('click', () => {
          const days = parseInt(btn.dataset.days);
          if (days === Number(state.settings.days)) return;
          state.settings.days = days;
          saveSettings();
          applySettings();
          syncDayButtons(days);
          resetWindowDataForReload();
          load({ skipSchedule: true, force: true });
        });
      });

      // Agent 筛选
      const agentSel = document.getElementById('agentFilter');
      if (agentSel) agentSel.addEventListener('change', () => {
        state.filterAgent = agentSel.value;
        rerenderWithFilters();
      });

      // 数据模式切换
      document.querySelectorAll('#dataModeGroup .btn-sm').forEach(btn => {
        btn.addEventListener('click', () => {
          state.filterDataMode = btn.dataset.mode;
          document.querySelectorAll('#dataModeGroup .btn-sm').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          rerenderWithFilters();
        });
      });

      // 趋势图粒度
      document.querySelectorAll('#trendGranularity .btn-sm').forEach(btn => {
        btn.addEventListener('click', () => {
          state.trendGranularity = btn.dataset.gran;
          document.querySelectorAll('#trendGranularity .btn-sm').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          renderTrendChart();
        });
      });

      // 趋势图模式：Token / 金额 / 叠加
      document.querySelectorAll('#trendMode .btn-sm').forEach(btn => {
        btn.addEventListener('click', () => {
          state.trendMode = btn.dataset.tmode;
          document.querySelectorAll('#trendMode .btn-sm').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          renderTrendChart();
        });
      });
    }

    function syncDayButtons(days) {
      document.querySelectorAll('#daysGroup .btn-sm, #settDays .btn-sm').forEach(b => {
        b.classList.toggle('active', parseInt(b.dataset.days) === days);
      });
    }

    // P4: 筛选后的数据
    function filteredSessions() {
      if (state.lastLedgerLoadId !== state.activeLoadId) return [];
      const sessions = (state.lastLedger && state.lastLedger.recent_sessions) || [];
      return sessions.filter(s => {
        if (state.filterAgent !== 'all' && (s.agent || '') !== state.filterAgent) return false;
        if (state.filterDataMode === 'token') {
          const hasToken = Number(s.total_tokens || 0) > 0 && !unknownTokenStatuses.has(s.token_status || '');
          if (!hasToken) return false;
        }
        return true;
      });
    }


    function rerenderWithFilters() {
      if (!state.lastLedger || state.lastLedgerLoadId !== state.activeLoadId) return;
      const ledger = state.lastLedger;
      const sessions = filteredSessions();
      // 重新用筛选后的数据渲染各面板
      const fakeLedger = { ...ledger, recent_sessions: sessions };

      // 从筛选后的 sessions 重新聚合 by_agent / by_project
      const byAgent = {};
      const byProject = {};
      sessions.forEach(s => {
        const agent = s.agent || 'unknown';
        if (!byAgent[agent]) byAgent[agent] = { agent, sessions: 0, total_tokens: 0, known_token_sessions: 0, projects: new Set(), latest_task: '', active_sessions: 0, lines_added: 0, lines_removed: 0, files_changed: 0, known_cost_sessions: 0, known_cost_usd: 0 };
        const a = byAgent[agent];
        a.sessions++;
        a.total_tokens = Number(a.total_tokens || 0) + Number(s.total_tokens || 0);
        if (Number(s.total_tokens || 0) > 0 && !unknownTokenStatuses.has(s.token_status || '')) a.known_token_sessions = (Number(a.known_token_sessions || 0) || 0) + 1;
        if (s.project) a.projects.add(s.project);
        if (s.task) a.latest_task = s.task;
        if (Number(s.active_sessions || 0) > 0 || ['active','recent'].includes(s.status)) a.active_sessions++;
        a.lines_added = Number(a.lines_added || 0) + Number(s.lines_added || 0);
        a.lines_removed = Number(a.lines_removed || 0) + Number(s.lines_removed || 0);
        a.files_changed = Number(a.files_changed || 0) + Number(s.files_changed || 0);
        if (Number(s.known_cost_usd || 0) > 0) { a.known_cost_sessions = (Number(a.known_cost_sessions || 0) || 0) + 1; a.known_cost_usd = Number(a.known_cost_usd || 0) + Number(s.known_cost_usd || 0); }

        const proj = s.project || 'unknown';
        if (!byProject[proj]) byProject[proj] = { project: proj, sessions: 0, total_tokens: 0, known_token_sessions: 0, agents: new Set(), latest_task: '', active_sessions: 0, latest_at: '', lines_added: 0, lines_removed: 0, files_changed: 0, known_cost_sessions: 0, known_cost_usd: 0 };
        const p = byProject[proj];
        p.sessions++;
        p.total_tokens = Number(p.total_tokens || 0) + Number(s.total_tokens || 0);
        if (Number(s.total_tokens || 0) > 0 && !unknownTokenStatuses.has(s.token_status || '')) p.known_token_sessions = (Number(p.known_token_sessions || 0) || 0) + 1;
        if (s.agent) p.agents.add(s.agent);
        if (s.task) p.latest_task = s.task;
        if (s.ended_at || s.started_at) p.latest_at = s.ended_at || s.started_at;
        if (Number(s.active_sessions || 0) > 0 || ['active','recent'].includes(s.status)) p.active_sessions++;
        p.lines_added = Number(p.lines_added || 0) + Number(s.lines_added || 0);
        p.lines_removed = Number(p.lines_removed || 0) + Number(s.lines_removed || 0);
        p.files_changed = Number(p.files_changed || 0) + Number(s.files_changed || 0);
        if (Number(s.known_cost_usd || 0) > 0) { p.known_cost_sessions = (Number(p.known_cost_sessions || 0) || 0) + 1; p.known_cost_usd = Number(p.known_cost_usd || 0) + Number(s.known_cost_usd || 0); }
      });
      // Convert Sets to Arrays for renderers
      Object.values(byAgent).forEach(a => { a.projects = [...(a.projects || [])]; });
      Object.values(byProject).forEach(p => { p.agents = [...(p.agents || [])]; });
      fakeLedger.by_agent = Object.values(byAgent);
      fakeLedger.by_project = Object.values(byProject);
      // P9.2: 从筛选 sessions 重聚合 by_model
      const byModel = {};
      sessions.forEach(s => {
        const m = s.model || 'unknown';
        if (!byModel[m]) byModel[m] = { model: m, sessions: 0, total_tokens: 0, agents: new Set(), known_cost_usd: 0, known_cost_sessions: 0, known_token_sessions: 0 };
        const p = byModel[m];
        p.sessions++;
        p.total_tokens += Number(s.total_tokens || 0);
        (s.agent && s.agent !== 'unknown') && p.agents.add(s.agent);
        if (Number(s.total_tokens || 0) > 0) p.known_token_sessions++;
        const c = Number(s.estimated_cost_usd || s.actual_cost_usd || 0);
        if (c > 0) { p.known_cost_usd += c; p.known_cost_sessions++; }
      });
      Object.values(byModel).forEach(m => { m.agents = [...(m.agents || [])]; });
      fakeLedger.by_model = Object.values(byModel).sort((a, b) => (b.total_tokens || 0) - (a.total_tokens || 0));

      renderInventory(fakeLedger);
      renderProjects(fakeLedger);
      renderSessions(fakeLedger);
      updateIcons();
    }


    function renderTrendChart(hoverState = null) {
      const canvas = document.getElementById('trendChart');
      if (!canvas || !state.lastLedger || state.lastLedgerLoadId !== state.activeLoadId) return;
      const ctx = canvas.getContext('2d');
      const localSessions = filteredSessions();
      const mode = state.trendMode || 'token'; // 'token' | 'cost' | 'both' | 'activity'
      const fleet = currentFleet();
      const fleetTimeline = ((fleet && fleet.activity_timeline) || [])
        .filter(row => state.filterAgent === 'all' || (row.agent || '') === state.filterAgent);
      const activityRows = fleetTimeline.length
        ? fleetTimeline
        : localSessions.map(row => ({
            ...row,
            activity: Number(row.sessions || row.session_count || 1),
            date: (row.started_at || row.ended_at || '').slice(0, 10),
          }));
      const sessions = mode === 'activity' ? activityRows : localSessions;

      // 按天/周聚合 token + cost
      const gran = state.trendGranularity;
      const tokenBuckets = {};
      const costBuckets = {};
      const activityBuckets = {};
      const agentTokenBuckets = {};
      const agentCostBuckets = {};
      const agentActivityBuckets = {};

      function _timeKey(ts) {
        if (!ts) return '';
        const d = new Date(ts);
        if (Number.isNaN(d.getTime())) return String(ts).slice(0, 10);
        if (gran === 'week') {
          const jan1 = new Date(d.getFullYear(), 0, 1);
          const wk = Math.ceil(((d - jan1) / 86400000 + jan1.getDay() + 1) / 7);
          return `${d.getFullYear()}-W${String(wk).padStart(2,'0')}`;
        }
        return ts.substring(0, 10);
      }

      localSessions.forEach(s => {
        const ts = s.started_at || s.ended_at;
        if (!ts) return;
        const key = _timeKey(ts);
        if (!key) return;
        const agent = s.agent || 'unknown';

        tokenBuckets[key] = (tokenBuckets[key] || 0) + Number(s.total_tokens || 0);
        if (!agentTokenBuckets[agent]) agentTokenBuckets[agent] = {};
        agentTokenBuckets[agent][key] = (agentTokenBuckets[agent][key] || 0) + Number(s.total_tokens || 0);

        const cost = hasKnownCost(s) ? Number(s.estimated_cost_usd ?? s.actual_cost_usd ?? 0) : 0;
        costBuckets[key] = (costBuckets[key] || 0) + cost;
        if (!agentCostBuckets[agent]) agentCostBuckets[agent] = {};
        agentCostBuckets[agent][key] = (agentCostBuckets[agent][key] || 0) + cost;
      });

      activityRows.forEach(row => {
        const ts = row.date || row.latest_at || row.ended_at || row.started_at;
        const key = _timeKey(ts);
        if (!key) return;
        const agent = row.agent || 'unknown';
        const count = Number(row.activity || row.sessions || row.session_count || 1);
        activityBuckets[key] = (activityBuckets[key] || 0) + count;
        if (!agentActivityBuckets[agent]) agentActivityBuckets[agent] = {};
        agentActivityBuckets[agent][key] = (agentActivityBuckets[agent][key] || 0) + count;
      });

      const buckets = mode === 'cost' ? costBuckets : (mode === 'activity' ? activityBuckets : tokenBuckets);
      const agentBuckets = mode === 'cost' ? agentCostBuckets : (mode === 'activity' ? agentActivityBuckets : agentTokenBuckets);
      const keySet = new Set(Object.keys(buckets));
      if (mode === 'both') {
        Object.keys(costBuckets).forEach(key => keySet.add(key));
      }
      const keys = Array.from(keySet).sort();

      state.trendKeys = keys;
      state.trendBuckets = buckets;
      state.trendAgentBuckets = agentBuckets;
      state._costBuckets = costBuckets;
      state._tokenBuckets = tokenBuckets;
      state._activityBuckets = activityBuckets;

      if (keys.length === 0) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#9aa7ba';
        ctx.font = '14px Inter, system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('暂无数据', canvas.width / 2, canvas.height / 2);
        return;
      }

      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      const cssWidth = rect.width || canvas.parentElement?.clientWidth || 800;
      const cssHeight = rect.height || Number(canvas.getAttribute('height')) || 320;
      const expectedW = Math.round(cssWidth * dpr);
      const expectedH = Math.round(cssHeight * dpr);
      if (canvas.width !== expectedW || canvas.height !== expectedH) {
        canvas.width = expectedW;
        canvas.height = expectedH;
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const W = cssWidth, H = cssHeight;
      const pad = { top: 20, right: (mode === 'both') ? 60 : 20, bottom: 40, left: 60 };

      ctx.clearRect(0, 0, W, H);

      const values = keys.map(k => Number(buckets[k] || 0));
      const maxVal = Math.max(...values, 1);
      const plotW = W - pad.left - pad.right;
      const plotH = H - pad.top - pad.bottom;

      // Hover vertical guide
      if (hoverState) {
        ctx.beginPath();
        ctx.moveTo(hoverState.hoverX, pad.top);
        ctx.lineTo(hoverState.hoverX, pad.top + plotH);
        ctx.strokeStyle = 'rgba(0, 210, 255, 0.35)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // 左 Y 轴
      ctx.strokeStyle = 'rgba(255,255,255,0.03)';
      ctx.lineWidth = 1;
      const yTicks = 5;
      for (let i = 0; i <= yTicks; i++) {
        const y = pad.top + (plotH / yTicks) * i;
        ctx.beginPath();
        ctx.moveTo(pad.left, y);
        ctx.lineTo(W - pad.right, y);
        ctx.stroke();
        ctx.fillStyle = '#5d6c86';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'right';
        const val = maxVal - (maxVal / yTicks) * i;
        ctx.fillText(mode === 'cost' ? '$' + formatCompact(val) : formatCompact(val), pad.left - 8, y + 4);
      }

      // "both" 模式：右 Y 轴 (cost)
      if (mode === 'both') {
        const costVals = keys.map(k => costBuckets[k] || 0);
        const maxCost = Math.max(...costVals, 0.01);
        for (let i = 0; i <= yTicks; i++) {
          const y = pad.top + (plotH / yTicks) * i;
          ctx.fillStyle = '#ffbd5a';
          ctx.font = '11px sans-serif';
          ctx.textAlign = 'left';
          const val = maxCost - (maxCost / yTicks) * i;
          ctx.fillText('$' + formatCompact(val), W - pad.right + 8, y + 4);
        }
      }

      // X axis
      ctx.fillStyle = '#5d6c86';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'center';
      const step = Math.max(1, Math.floor(keys.length / 12));
      keys.forEach((k, i) => {
        if (i % step === 0) {
          const x = pad.left + (plotW / Math.max(keys.length - 1, 1)) * i;
          ctx.fillText(k.slice(5), x, H - pad.bottom + 18);
        }
      });

      // Top agents
      const agents = Object.keys(agentBuckets).sort((a, b) =>
        Object.values(agentBuckets[b]).reduce((s, v) => s + v, 0) - Object.values(agentBuckets[a]).reduce((s, v) => s + v, 0)
      ).slice(0, 6);

      const colors = ['#37d5ff','#00f5a0','#aa8cff','#ffbd5a','#ff6d8d','#c7f25c'];

      // 绘制主曲线（per agent）
      agents.forEach((agent, ai) => {
        const data = keys.map(k => Number(agentBuckets[agent][k] || 0));
        const color = colors[ai % colors.length];
        const r = parseInt(color.slice(1,3),16), g = parseInt(color.slice(3,5),16), b = parseInt(color.slice(5,7),16);
        const points = data.map((v, i) => ({
          x: pad.left + (plotW / Math.max(keys.length - 1, 1)) * i,
          y: pad.top + plotH - (v / maxVal) * plotH,
          val: v,
        }));

        // Area
        ctx.beginPath();
        ctx.moveTo(points[0].x, pad.top + plotH);
        ctx.lineTo(points[0].x, points[0].y);
        for (let i = 0; i < points.length - 1; i++) {
          const xc = (points[i].x + points[i+1].x) / 2;
          const yc = (points[i].y + points[i+1].y) / 2;
          ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
        }
        ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
        ctx.lineTo(points[points.length - 1].x, pad.top + plotH);
        ctx.closePath();
        ctx.fillStyle = `rgba(${r},${g},${b},0.07)`;
        ctx.fill();

        // Line
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 0; i < points.length - 1; i++) {
          const xc = (points[i].x + points[i+1].x) / 2;
          const yc = (points[i].y + points[i+1].y) / 2;
          ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
        }
        ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
        ctx.strokeStyle = color;
        ctx.lineWidth = 2.5;
        ctx.shadowBlur = 8;
        ctx.shadowColor = `rgba(${r},${g},${b},0.25)`;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Dots
        points.forEach((p, i) => {
          if (p.val > 0) {
            ctx.beginPath();
            const isHov = hoverState && hoverState.hoverIdx === i;
            ctx.arc(p.x, p.y, isHov ? 5.5 : 3.5, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.fill();
            if (isHov) {
              ctx.beginPath();
              ctx.arc(p.x, p.y, 9, 0, Math.PI * 2);
              ctx.strokeStyle = `rgba(${r},${g},${b},0.35)`;
              ctx.lineWidth = 1.5;
              ctx.stroke();
            }
          }
        });
      });

      // "both" 模式：额外 cost 总线（金色）
      if (mode === 'both') {
        const costVals = keys.map(k => costBuckets[k] || 0);
        const maxCost = Math.max(...costVals, 0.01);
        const cPts = costVals.map((v, i) => ({
          x: pad.left + (plotW / Math.max(keys.length - 1, 1)) * i,
          y: pad.top + plotH - (v / maxCost) * plotH,
          val: v,
        }));

        // Area
        ctx.beginPath();
        ctx.moveTo(cPts[0].x, pad.top + plotH);
        cPts.forEach((p, i) => {
          if (i === 0) { ctx.lineTo(p.x, p.y); return; }
          const prev = cPts[i-1];
          ctx.quadraticCurveTo(prev.x, prev.y, (prev.x+p.x)/2, (prev.y+p.y)/2);
        });
        ctx.lineTo(cPts[cPts.length-1].x, cPts[cPts.length-1].y);
        ctx.lineTo(cPts[cPts.length-1].x, pad.top + plotH);
        ctx.closePath();
        ctx.fillStyle = 'rgba(255,189,90,0.08)';
        ctx.fill();

        // Line
        ctx.beginPath();
        ctx.moveTo(cPts[0].x, cPts[0].y);
        for (let i = 1; i < cPts.length; i++) {
          const prev = cPts[i-1], p = cPts[i];
          ctx.quadraticCurveTo(prev.x, prev.y, (prev.x+p.x)/2, (prev.y+p.y)/2);
        }
        ctx.lineTo(cPts[cPts.length-1].x, cPts[cPts.length-1].y);
        ctx.strokeStyle = '#ffbd5a';
        ctx.lineWidth = 2;
        ctx.shadowBlur = 6;
        ctx.shadowColor = 'rgba(255,189,90,0.3)';
        ctx.stroke();
        ctx.shadowBlur = 0;
      }

      // Legend
      const legend = document.getElementById('trendLegend');
      if (legend) {
        let html = agents.map((a, i) =>
          `<span class="trend-legend-item"><span class="trend-legend-dot" style="background:${colors[i % colors.length]}"></span>${esc(a)}</span>`
        ).join('');
        if (mode === 'both') {
          html += `<span class="trend-legend-item"><span class="trend-legend-dot" style="background:#ffbd5a"></span>金额 (USD)</span>`;
        }
        legend.innerHTML = html;
      }

      renderTrendStats(sessions, buckets, keys, agents, agentBuckets, colors, costBuckets);

      // 保存静态图快照，hover 时只恢复快照 + 画 overlay（性能优化）
      state._trendSnapshot = ctx.getImageData(0, 0, canvas.width, canvas.height);
      state._trendPlotMeta = { pad, plotW, plotH, keys, mode };

      // Mouse listeners (bind once)
      if (!canvas.dataset.listened) {
        canvas.dataset.listened = "true";
        const tooltipEl = document.getElementById('chart-tooltip');

        // 仅绘制 hover overlay（竖线 + 高亮点），不重绘全部曲线
        function drawHoverOverlay(hoverX, hoverIdx) {
          const snap = state._trendSnapshot;
          if (!snap) return;
          ctx.putImageData(snap, 0, 0);
          const m = state._trendPlotMeta;
          // 竖线
          ctx.beginPath();
          ctx.moveTo(hoverX, m.pad.top);
          ctx.lineTo(hoverX, m.pad.top + m.plotH);
          ctx.strokeStyle = 'rgba(255,255,255,0.2)';
          ctx.lineWidth = 1;
          ctx.stroke();
        }

        canvas.addEventListener('mousemove', (e) => {
          if (!state.trendKeys || state.trendKeys.length === 0) return;
          const rect = canvas.getBoundingClientRect();
          const mouseX = e.clientX - rect.left;
          const mouseY = e.clientY - rect.top;
          const keys = state.trendKeys;
          const curMode = state.trendMode || 'token';
          const curPad = { top: 20, right: curMode === 'both' ? 60 : 20, bottom: 40, left: 60 };
          const plotW = rect.width - curPad.left - curPad.right;
          const xStep = plotW / Math.max(keys.length - 1, 1);
          let closestIdx = Math.round((mouseX - curPad.left) / xStep);
          closestIdx = Math.max(0, Math.min(keys.length - 1, closestIdx));
          const closestKey = keys[closestIdx];
          const closestX = curPad.left + closestIdx * xStep;

          drawHoverOverlay(closestX, closestIdx);

          if (tooltipEl) {
            const totalVal = state.trendBuckets[closestKey] || 0;
            const tokenVal = (state._tokenBuckets || {})[closestKey] || 0;
            const costVal = (state._costBuckets || {})[closestKey] || 0;
            const activityVal = (state._activityBuckets || {})[closestKey] || 0;

            let tooltipContent = `<div class="chart-tooltip-title">${closestKey}</div>`;
            if (curMode === 'cost') {
              tooltipContent += `<div class="chart-tooltip-item" style="font-weight:700;margin-bottom:6px;">
                <span class="chart-tooltip-label" style="color:var(--text-strong)">总金额</span>
                <span class="chart-tooltip-val">${fmtMoney(costVal)}</span>
              </div>`;
            } else if (curMode === 'activity') {
              tooltipContent += `<div class="chart-tooltip-item" style="font-weight:700;margin-bottom:6px;">
                <span class="chart-tooltip-label" style="color:var(--text-strong)">总活动</span>
                <span class="chart-tooltip-val">${fmtInt(activityVal || totalVal)}</span>
              </div>`;
            } else {
              tooltipContent += `<div class="chart-tooltip-item" style="font-weight:700;margin-bottom:6px;">
                <span class="chart-tooltip-label" style="color:var(--text-strong)">总 Token</span>
                <span class="chart-tooltip-val">${fmtInt(totalVal)}</span>
              </div>`;
              if (costVal > 0) {
                tooltipContent += `<div class="chart-tooltip-item" style="margin-bottom:6px;color:#ffbd5a">
                  <span class="chart-tooltip-label">金额</span>
                  <span class="chart-tooltip-val">${fmtMoney(costVal)}</span>
                </div>`;
              }
            }

            const colors = ['#37d5ff','#00f5a0','#aa8cff','#ffbd5a','#ff6d8d','#c7f25c'];
            const curAB = state.trendAgentBuckets || {};
            const agentsSorted = Object.keys(curAB).sort((a, b) =>
              Object.values(curAB[b]).reduce((s, v) => s + v, 0) - Object.values(curAB[a]).reduce((s, v) => s + v, 0)
            ).slice(0, 6);
            const agentVals = [];
            for (const [agent, bkt] of Object.entries(curAB)) {
              const val = bkt[closestKey] || 0;
              if (val > 0) agentVals.push({ agent, val });
            }
            agentVals.sort((a, b) => b.val - a.val);
            agentVals.forEach(item => {
              const ai = agentsSorted.indexOf(item.agent);
              const color = ai !== -1 ? colors[ai % colors.length] : '#8c9cb6';
              tooltipContent += `<div class="chart-tooltip-item">
                <span class="chart-tooltip-dot" style="background:${color}"></span>
                <span class="chart-tooltip-label">${esc(item.agent)}</span>
                <span class="chart-tooltip-val">${curMode === 'cost' ? fmtMoney(item.val) : fmtInt(item.val)}</span>
              </div>`;
            });

            tooltipEl.innerHTML = tooltipContent;
            tooltipEl.style.opacity = '1';
            const pageRect = canvas.getBoundingClientRect();
            tooltipEl.style.left = `${pageRect.left + window.scrollX + closestX}px`;
            tooltipEl.style.top = `${pageRect.top + window.scrollY + mouseY - 15}px`;
          }
        });

        canvas.addEventListener('mouseleave', () => {
          const snap = state._trendSnapshot;
          if (snap) ctx.putImageData(snap, 0, 0);
          const tooltipEl = document.getElementById('chart-tooltip');
          if (tooltipEl) tooltipEl.style.opacity = '0';
        });
      }
    }

    function renderTrendStats(sessions, buckets, keys, agents, agentBuckets, colors, costBuckets) {
      const mode = state.trendMode || 'token';
      const totalT = sessions.reduce((s, r) => s + Number(r.total_tokens || 0), 0);
      const totalActivity = keys.reduce((s, k) => s + (buckets[k] || 0), 0);
      const totalS = mode === 'activity' ? totalActivity : sessions.length;
      const peakDay = keys.reduce((a, b) => Number(buckets[a] || 0) > Number(buckets[b] || 0) ? a : b, keys[0]);
      const peakVal = Number(buckets[peakDay] || 0);
      const costBk = costBuckets || buckets;
      const totalCostVal = keys.reduce((s, k) => s + (costBk[k] || 0), 0);
      const valueLabel = mode === 'cost' ? '总金额' : (mode === 'activity' ? '总活动' : '总 Token');
      const valueText = mode === 'cost' ? fmtMoney(totalCostVal) : (mode === 'activity' ? fmtInt(totalActivity) : formatCompact(totalT));
      const peakText = mode === 'cost' ? fmtMoney(peakVal) : (mode === 'activity' ? fmtInt(peakVal) : formatCompact(peakVal));
      const avgText = mode === 'cost'
        ? (totalCostVal > 0 ? fmtMoney(totalCostVal / Math.max(totalS, 1)) : '-')
        : (mode === 'activity' ? formatCompact(totalActivity / Math.max(keys.length, 1)) : (totalCostVal > 0 ? fmtMoney(totalCostVal / Math.max(totalS, 1)) : '-'));
      const avgLabel = mode === 'activity' ? '平均活动/周期' : '平均费用/次';

      const el = document.getElementById('trendStats');
      if (el) el.innerHTML = `
        <h3 style="font-size:13px;font-weight:700;margin:0 0 8px;color:var(--text)">统计摘要</h3>
        <div class="trend-stats-grid">
          <div class="trend-stat-card"><div class="val">${valueText}</div><div class="lbl">${valueLabel}</div></div>
          <div class="trend-stat-card"><div class="val">${totalS}</div><div class="lbl">会话数</div></div>
          <div class="trend-stat-card"><div class="val">${peakText}</div><div class="lbl">峰值 (${peakDay.slice(5)})</div></div>
          <div class="trend-stat-card"><div class="val">${avgText}</div><div class="lbl">${avgLabel}</div></div>
        </div>`;

      // Agent breakdown
      const bd = document.getElementById('trendAgentBreakdown');
      if (bd) {
        const totalBase = mode === 'cost' ? (totalCostVal || 1) : (mode === 'activity' ? totalActivity : totalT);
        const rows = agents.map((a, i) => {
          const t = Object.values(agentBuckets[a]).reduce((s,v)=>s+v,0);
          const pct = totalBase > 0 ? (t / totalBase * 100).toFixed(1) : 0;
          return `<tr>
            <td><span class="trend-legend-dot" style="background:${colors[i%colors.length]};display:inline-block;vertical-align:middle;margin-right:4px"></span>${esc(a)}</td>
            <td class="num">${mode === 'cost' ? fmtMoney(t) : (mode === 'activity' ? fmtInt(t) : formatCompact(t))}</td>
            <td class="num">${pct}%</td>
            <td><div class="meter"><span style="width:${pct}%;background:${colors[i%colors.length]}"></span></div></td>
          </tr>`;
        }).join('');
        bd.innerHTML = `<h3 style="font-size:13px;font-weight:700;margin:0 0 8px;color:var(--text)">Agent 构成</h3>
          <table style="width:100%"><tr><th>Agent</th><th class="num">${mode === 'cost' ? '金额' : (mode === 'activity' ? '活动' : 'Token')}</th><th class="num">占比</th><th></th></tr>${rows}</table>`;
      }
    }
    function populateAgentFilter(ledger) {
      const sel = document.getElementById('agentFilter');
      if (!sel || !ledger) return;
      const fleet = currentFleet();
      const fleetAgents = ((fleet && fleet.agent_activity_rank) || []).map(row => row.agent || 'unknown');
      const agents = [...new Set((ledger.recent_sessions || []).map(s => s.agent || 'unknown').concat(fleetAgents))]
        .filter(agent => agent && agent !== 'unknown')
        .sort();
      const current = sel.value;
      sel.innerHTML = '<option value="all">全部</option>' +
        agents.map(a => `<option value="${esc(a)}"${a === current ? ' selected' : ''}>${esc(a)}</option>`).join('');
    }

    // P4: 格式化紧凑数字
    function formatCompact(n) {
      n = Number(n || 0);
      if (n >= 1e9) return (n / 1e9).toFixed(2) + 'B';
      if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
      if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
      return String(Math.round(n));
    }

    // =================================================================
    // Session Detail Modal & Hot-Reload Routing Config Panel Helpers
    // =================================================================

    window.openSessionDetail = function(sessionId) {
      const session = (state.recentSessions || []).find(s => s.session_id === sessionId);
      if (!session) return;
      showSessionModal(session);
    };

    function getFallbackTrace(route, fallback, successProvider) {
      if (!route) return null;
      const defaultProviderMap = {
        'local': 'local',
        'coding': 'deepseek_chat',
        'reasoning': 'deepseek_reasoner',
        'quality': 'glm_quality'
      };
      const chains = {
        'local': ['local', 'deepseek_chat', 'qwen_backup'],
        'coding': ['deepseek_chat', 'qwen_backup', 'glm_quality'],
        'reasoning': ['deepseek_reasoner', 'deepseek_chat', 'qwen_backup'],
        'quality': ['glm_quality', 'deepseek_chat', 'qwen_backup']
      };
      const chain = chains[route] || ['deepseek_chat', 'qwen_backup'];

      if (!fallback) {
        return [{ provider: successProvider || defaultProviderMap[route] || 'unknown', status: 'success' }];
      }

      const idx = chain.indexOf(successProvider);
      if (idx === -1) {
        const def = defaultProviderMap[route] || chain[0];
        return [
          { provider: def, status: 'fail' },
          { provider: successProvider, status: 'success' }
        ];
      }

      const steps = [];
      for (let i = 0; i <= idx; i++) {
        steps.push({
          provider: chain[i],
          status: i === idx ? 'success' : 'fail'
        });
      }
      return steps;
    }

    function showSessionModal(session) {
      const modal = document.getElementById('sessionDetailModal');
      if (!modal) return;

      const titleEl = document.getElementById('modalTitle');
      const bodyEl = document.getElementById('modalBody');

      const lang = state.settings.lang || 'zh';
      const isZh = lang === 'zh';
      const labels = {
        sessionDetail: isZh ? '\u4f1a\u8bdd\u8be6\u60c5' : 'Session Details',
        sessionId: isZh ? '\u4f1a\u8bdd ID' : 'Session ID',
        agentSource: isZh ? 'Agent / \u6765\u6e90' : 'Agent / Source',
        project: isZh ? '\u9879\u76ee' : 'Project',
        model: isZh ? '\u6a21\u578b' : 'Model',
        provider: isZh ? '\u89e3\u6790 Provider' : 'Completed Provider',
        cost: isZh ? '\u9884\u4f30\u91d1\u989d' : 'Estimated Cost',
        tokenBreakdown: isZh ? 'Token \u660e\u7ec6' : 'Token Breakdown',
        inputTokens: isZh ? '\u8f93\u5165 Token' : 'Input Tokens',
        outputTokens: isZh ? '\u8f53\u51fa Token' : 'Output Tokens',
        totalTokens: isZh ? '\u603b Token' : 'Total Tokens',
        perfRouting: isZh ? '\u6027\u80fd\u4e0e\u8def\u7531' : 'Performance & Routing',
        latency: isZh ? '\u7269\u7406\u8017\u65f6' : 'Physical Latency',
        route: isZh ? '\u68c0\u6d4b\u8def\u7531' : 'Detected Route',
        fallbackTriggered: isZh ? '\u89e6\u53d1\u5907\u7528\u8def\u7531' : 'Fallback Triggered',
        yes: isZh ? '\u662f' : 'Yes',
        no: isZh ? '\u5426' : 'No',
        trajectory: isZh ? '\u8def\u7531\u8f68\u8ff9' : 'Fallback Trajectory',
        noTrajectory: isZh ? '\u8be5\u4f1a\u8bdd\u65e0\u8def\u7531\u8f68\u8ff9\u6570\u636e\u3002' : 'No fallback trace available for this session.',
        statusSuccess: isZh ? '\u6210\u529f' : 'Success',
        statusFailed: isZh ? '\u5931\u8d25 (\u5df2\u907f\u8ba9)' : 'Failed (Fallback)'
      };

      if (titleEl) {
        titleEl.textContent = labels.sessionDetail;
      }

      const steps = getFallbackTrace(session.route, session.fallback, session.provider);
      let traceStepsHtml = '';
      if (steps && steps.length) {
        steps.forEach(step => {
          const isSuccess = step.status === 'success';
          const stepClass = isSuccess ? 'success' : 'fail';
          const icon = isSuccess ? '\u2713' : '\u2717';
          const statusText = isSuccess ? labels.statusSuccess : labels.statusFailed;
          traceStepsHtml += `
            <div class="trace-step ${stepClass}">
              <div class="trace-icon">${icon}</div>
              <div class="trace-info">
                <span class="provider-name">${esc(step.provider)}</span>
                <span class="status-text">${statusText}</span>
              </div>
            </div>
          `;
        });
      } else {
        traceStepsHtml = `<div class="subtle">${labels.noTrajectory}</div>`;
      }

      bodyEl.innerHTML = `
        <div class="modal-grid-3">
          <div class="modal-meta-card">
            <label>${labels.sessionId}</label>
            <div class="val">${esc(session.session_id || session.id || '\u2014')}</div>
          </div>
          <div class="modal-meta-card">
            <label>${labels.agentSource}</label>
            <div class="val">${esc(session.agent || '\u2014')} <span style="font-size: 11px; color: var(--muted-2);">(${esc(session.source || '\u2014')})</span></div>
          </div>
          <div class="modal-meta-card">
            <label>${labels.project}</label>
            <div class="val">${esc(session.project || '\u2014')}</div>
          </div>
        </div>

        <div class="modal-grid-3">
          <div class="modal-meta-card">
            <label>${labels.model}</label>
            <div class="val">${esc(session.model || '\u2014')}</div>
          </div>
          <div class="modal-meta-card">
            <label>${labels.provider}</label>
            <div class="val">${esc(session.provider || '\u2014')}</div>
          </div>
          <div class="modal-meta-card">
            <label>${labels.cost}</label>
            <div class="val">${session.estimated_cost_usd != null ? fmtMoney(session.estimated_cost_usd) : '\u2014'}</div>
          </div>
        </div>

        <div class="modal-section-title">${labels.tokenBreakdown}</div>
        <div class="modal-grid-3">
          <div class="modal-meta-card">
            <label>${labels.inputTokens}</label>
            <div class="val">${session.input_tokens != null ? fmtInt(session.input_tokens) : '\u2014'}</div>
          </div>
          <div class="modal-meta-card">
            <label>${labels.outputTokens}</label>
            <div class="val">${session.output_tokens != null ? fmtInt(session.output_tokens) : '\u2014'}</div>
          </div>
          <div class="modal-meta-card">
            <label>${labels.totalTokens}</label>
            <div class="val">${session.total_tokens != null ? fmtInt(session.total_tokens) : '\u2014'}</div>
          </div>
        </div>

        <div class="modal-section-title">${labels.perfRouting}</div>
        <div class="modal-grid-3">
          <div class="modal-meta-card">
            <label>${labels.latency}</label>
            <div class="val">${session.duration_ms != null ? (session.duration_ms / 1000).toFixed(2) + 's' : '\u2014'}</div>
          </div>
          <div class="modal-meta-card">
            <label>${labels.route}</label>
            <div class="val">${esc(session.route || '\u2014')}</div>
          </div>
          <div class="modal-meta-card">
            <label>${labels.fallbackTriggered}</label>
            <div class="val">${session.fallback ? labels.yes : labels.no}</div>
          </div>
        </div>

        <div class="modal-section-title">${labels.trajectory}</div>
        <div class="fallback-trace">
          ${traceStepsHtml}
        </div>
      `;

      modal.style.display = 'flex';
    }

    function renderRoutingConfig() {
      const container = document.getElementById('config');
      if (!container) return;

      const rc = state.routingConfig || {};
      const categories = [
        { key: 'local_hint', labelKey: 'routing-local-label', defaultLabel: 'Local Hint' },
        { key: 'coding', labelKey: 'routing-coding-label', defaultLabel: 'Coding' },
        { key: 'reasoning', labelKey: 'routing-reason-label', defaultLabel: 'Reasoning' },
        { key: 'quality', labelKey: 'routing-quality-label', defaultLabel: 'Quality' }
      ];

      let html = `<h3>${t('routing-config', '路由配置')}</h3>`;

      categories.forEach(cat => {
        const words = rc[cat.key] || [];
        const label = t(cat.labelKey, cat.defaultLabel);

        html += `
          <div class="config-group">
            <label>${esc(label)} <span style="font-size:10px;color:var(--muted-2);">(${esc(cat.key)})</span></label>
            <div class="tag-container" id="tags-${cat.key}">
        `;

        words.forEach(word => {
          html += `
            <span class="keyword-tag">
              <span>${esc(word)}</span>
              <button class="tag-delete-btn" onclick="window.removeKeywordTag(this, '${esc(cat.key)}', '${esc(word)}')">&times;</button>
            </span>
          `;
        });

        html += `
              <input type="text" class="tag-input" placeholder="${esc(t('add-keyword-placeholder', 'Press Enter to add...'))}" onkeydown="window.handleKeywordInput(event, '${esc(cat.key)}')">
            </div>
          </div>
        `;
      });

      html += `
        <div style="margin-top: 20px; display: flex; align-items: center; gap: 12px;">
          <button class="btn" onclick="window.saveRoutingConfig()" id="saveRoutingBtn">${t('btn-save-routing', 'Save Routing Config')}</button>
          <span id="routingSaveStatus" class="subtle" style="font-size: 13px;"></span>
        </div>
      `;

      container.innerHTML = html;
    }

    window.removeKeywordTag = function(btn, category, word) {
      if (!state.routingConfig || !state.routingConfig[category]) return;
      state.routingConfig[category] = state.routingConfig[category].filter(w => w !== word);
      renderRoutingConfig();
    };

    window.handleKeywordInput = function(event, category) {
      if (event.key === 'Enter') {
        event.preventDefault();
        const val = event.target.value.trim();
        if (!val) return;
        if (!state.routingConfig) state.routingConfig = {};
        if (!state.routingConfig[category]) state.routingConfig[category] = [];

        if (!state.routingConfig[category].includes(val)) {
          state.routingConfig[category].push(val);
        }

        event.target.value = '';
        renderRoutingConfig();
      }
    };

    window.saveRoutingConfig = function() {
      const btn = document.getElementById('saveRoutingBtn');
      const statusEl = document.getElementById('routingSaveStatus');
      if (!btn || !statusEl) return;

      btn.disabled = true;
      statusEl.textContent = t('saving', 'Saving...');
      statusEl.style.color = 'var(--muted)';

      postJson(base + '/config/routing', state.routingConfig, 15000)
        .then(res => {
          if (res.status === 'ok') {
            statusEl.textContent = t('saved', 'Saved successfully');
            statusEl.style.color = 'var(--mint)';
            loadStatus().catch(err => console.error(err));
          } else {
            statusEl.textContent = t('save-failed', 'Save failed') + ': ' + (res.message || 'unknown');
            statusEl.style.color = '#ff6464';
          }
        })
        .catch(err => {
          statusEl.textContent = t('save-failed', 'Save failed') + ': ' + err.message;
          statusEl.style.color = '#ff6464';
        })
        .finally(() => {
          btn.disabled = false;
          setTimeout(() => {
            if (statusEl.textContent === t('saved', 'Saved successfully')) {
              statusEl.textContent = '';
            }
          }, 3000);
        });
    };
