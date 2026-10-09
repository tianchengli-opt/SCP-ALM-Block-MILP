# GitHub 修改清单

本次只创建新仓库，不覆盖原始输入。所有算法科学计算逻辑修改数为**零**。代码名改变只发生在最终仓库引用位置，代码内容不变。

| 原始位置 | 最终位置 | 处理及原因 | 科学计算逻辑 | 验证 |
|---|---|---|---|---|
| 顶层run_2d_scaling.py | code/run_2d_scaling.py | 直接复制最新冻结版本，替代旧PC1Mild文件 | 不涉及 | 字节和SHA一致 |
| 顶层run_3d_difficult.py | code/run_3d_difficult.py | 直接复制最新冻结版本，替代旧DZ3文件 | 不涉及 | 字节和SHA一致 |
| 旧草稿code/两份旧文件 | 不公开，记录于source_code_audit | 保留对照证据，不混入旧执行文件 | 不涉及 | 文档字符串外AST相同 |
| 最新二维60份config及三维80份config | configs/2d、configs/3d | 完整复制参数值，只重写out_dir为可移植路径 | 不涉及 | 140组解析器往返与入口调参检查通过 |
| 旧run_plan.json | configs/run_plan.json | 更新源名、SHA、140调用、源清单绑定、预期输出 | 不涉及 | 60二维+80三维，方法及身份一致 |
| 最新140份原始instance_manifest | instances/40份规范化载荷及instance_index | 去重完整非args实例载荷；算法args另存配置；新增final哈希阶段说明 | 不涉及 | 原始同例各方法完整数据严格一致 |
| 最新160份单方法summary | results/source_summaries/对应单方法CSV | 全部从最新结果提取；其中40份Gurobi仅logfile路径脱敏 | 不涉及 | 120份字节复制，40份非路径字段逐字串相同 |
| 最新算法轨迹、固定z与历史LB审计 | results/source_summaries/同例目录 | 保留可复核LB、UB的最小必要证据；包括R12额外终止审计 | 不涉及 | 120条算法LB/UB来源匹配 |
| 最新40份gurobi_extensive.log | results/source_summaries/同例目录 | 只改LogFile路径行，其余求解数字不改 | 不涉及 | 目标、界、Gap、节点及状态匹配；计时差异保留 |
| 旧两张正式结果表 | results/local_side_scaling_results.csv、difficult_instance_results.csv | 全量重建，不拼接旧值；使用正确RD-ALM认证字段 | 不涉及 | 每张80行，逐字段来源验证 |
| Gurobi没有原始独立绝对Gap列 | 结果表绝对Gap空白并加说明 | 不把派生计算伪装成原始字段；可分析UB−LB | 不涉及 | 其他原始数值均保留 |
| 旧草稿scripts/run_experiments.py | scripts/run_experiments.py | 保留默认预览和防覆盖设计；新文件名、路径、实参、依赖检测和后置验证 | 不涉及 | 60/80预览、输出保护、模拟错误传播实测 |
| 旧草稿scripts/verify_repository.py | scripts/verify_repository.py及audit_common.py | 增强哈希、实际解析器、完整身份、数值证据、表格来源校验 | 不涉及 | 实际运行通过；严格与数值模式负向测试通过 |
| 旧PowerShell包装脚本 | scripts/run_2d_scaling.ps1、run_3d_difficult.ps1 | 保留数组式参数传递/退出码检查；增加identity与环境选项 | 不涉及 | 静态检查；PowerShell执行未验证 |
| 无 | scripts/test_repository.py | 13项标准库单元/负向测试，明确无优化 | 不涉及 | 全部通过 |
| 旧草稿README、README_zh | README.md、README_zh.md | 重写来源、操作、指标、身份、筛选、硬件和验证边界 | 不涉及 | 命令预览和本地链接检查 |
| 旧依赖说明 | requirements.txt | 仅列实际两项依赖；明确不是历史锁文件，不编造版本 | 不涉及 | 源码全AST导入依赖核对；实际缺失gurobipy预检报错 |
| 旧.gitignore/.gitattributes | 同名文件 | 保留禁缓存/密钥和禁止换行转换；允许40份脱敏原生日志 | 不涉及 | 文件清单与公开范围检查 |
| 旧草稿8份screening证据 | screening/同名文件 | 核对原始400+60候选后保留，不包装缺失hunter | 不涉及 | 460份排名/结果/配置及最终20例匹配 |
| 原始stage2 ZIP及已展开重复文件 | 不公开重复副本；保留排重审计 | 780份重复字节无再次公开必要 | 不涉及 | 逐一SHA匹配 |
| 旧数值/旧实例浮点差异 | provenance/old_vs_latest*、two_dimensional_float_differences.csv | 保留差异，不以旧表覆盖新结果，不静默放宽 | 不涉及 | 全部39,642处差异核实并作白名单测试 |
| 全部输入与最终文件 | provenance/input_inventory、file_sources、repository_manifest等 | 建立原始SHA、来源、处置、公开SHA完整链 | 不涉及 | 最终ZIP独立解压后重新核验 |
| 私有路径 | provenance/public_redactions及两类公开衍生文件 | 路径脱敏；原始档案不改；保留原/公开SHA | 不涉及 | 未改变数字，公开材料隐私扫描 |
| 历史大run.log、JSONL/摘要别名/旧报告副本 | 不公开，保留输入归档SHA与审计索引 | 减少重复/过时/私密材料，不删除原始输入 | 不涉及 | 对本次正式结果必要证据已独立保留 |
| LICENSE占位或作者未确认许可 | 不建立LICENSE授权文件 | 未经作者决定不选择许可；README明确待确认 | 不涉及 | 没有添加许可、推送或发布操作 |

逐文件记录覆盖每一份最终文件，见 `provenance/file_sources.csv`。它区分COPY、REDACTED、DERIVED、GENERATED以及对应原始来源、原始SHA和公开SHA。输入逐条处置见 `provenance/input_inventory.csv`。最后的repository_manifest只列其余所有发布文件，避免自哈希循环。

**未做的修改：**没有调整模型、约束、割生成、In-Out、λ/ρ、oracle、Gurobi求解参数、数值容差、随机实例、并行和求和、停止条件、指标定义；没有修改正式LB/UB/Gap/时间；没有复现旧论文数值而调参；没有补造缺失筛选、日志或命中时间。
