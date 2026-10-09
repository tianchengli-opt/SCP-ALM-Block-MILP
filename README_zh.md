# SCP-ALM 最终复现仓库：中文说明

## 结论与范围

本仓库使用作者指定的最新 `run_2d_scaling.py`、`run_3d_difficult.py` 和最新二维、三维正式重跑结果。已完成实际静态测试、结果溯源和归档实例一致性检查。**可作为明确披露验证边界的科研代码与结果仓库，由作者上传；不能宣称已完成第三方端到端求解复现或已授予开源许可证。** 未修改冻结算法，未发布或推送 GitHub。

英文主说明见 [README.md](README.md)。详细审计见 [最终审计报告](provenance/RELEASE_AUDIT_zh.md)，逐类修改见 [修改清单](provenance/CHANGELOG_zh.md)，逐文件来源见 `provenance/file_sources.csv`。

## 四种方法与正式数量

`p1` 对应 SCP-ALM；`p2` 对应 RD-ALM；`p1_norho` 对应 SCP-LR；`gurobi` 对应 Gurobi。内部名称没有改动。二维指两资源设置，不是经过 tail 提升后的共享变量总维数。

二维 B=300,360,…,1440，共20个规模、80条结果。每个规模为三组进程调用：`p1p2` 联合输出 SCP-ALM 和 RD-ALM，另有 `p1_norho`、`gurobi`。三维 R01–R20，每例120个局部块、三资源、四组独立调用。合计 **140组正式调用、40个实例、160条方法结果**。

## 安装、预览、运行

在项目根目录创建环境并安装依赖。`requirements.txt` 只有 numpy、gurobipy，**不是原始环境的精确锁文件**。原始40份 Gurobi 原生日志均报告引擎13.0.1；原始 Python、NumPy 及包发行版本没有足够记录，因此不能编造版本。自行配置合法 Gurobi 许可，禁止将许可证和凭据提交仓库。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\verify_repository.py
.\.venv\Scripts\python.exe scripts\run_experiments.py --study 2d --show-commands
.\.venv\Scripts\python.exe scripts\run_experiments.py --study 3d --show-commands
```

默认仅预览，不创建求解输出。真正运行全套实验必须显式加 `--execute`：

```powershell
.\.venv\Scripts\python.exe scripts\run_experiments.py --study 2d --output-root C:\SCP_ALM_runs\Study1 --execute
.\.venv\Scripts\python.exe scripts\run_experiments.py --study 3d --output-root C:\SCP_ALM_runs\Study2 --execute
```

单个规模/实例：

```powershell
python scripts\run_experiments.py --study 2d --instance B0300 --run-group p1p2 --output-root C:\SCP_ALM_runs\single_2d --execute
python scripts\run_experiments.py --study 3d --instance R17 --run-group p1 --output-root C:\SCP_ALM_runs\single_3d --execute
```

省略 `--run-group` 即运行该实例全部方法。二维的 SCP-ALM 应选 `p1p2`，不能选三维的 `p1` 调用形式。新结果路径在指定根目录下追加 `<study>/<instance>/<run_group>`，例如 `3d/R17/p1`。Windows 推荐纯英文输出路径，尤其是 Gurobi 原生日志路径。POSIX 系统使用相同 Python 参数和本系统的路径格式。

启动器拒绝非空输出目录；不得并发向同一目录启动同一任务。求解异常、依赖缺失或后置验证失败均返回非零并停止后续调用，部分输出保留供检查，不会称为运行成功。不要直接无参数运行冻结代码；其中保留了历史默认派发。二维冻结脚本的原始 `--help` 有百分号格式错误，本次未改源码，统一使用外围启动器的 `--help`。

## 查看结果和验证

```powershell
python scripts\verify_repository.py
python scripts\test_repository.py
python scripts\verify_repository.py --job-id 3d_R17_p1 --run-output C:\SCP_ALM_runs\single_3d\3d\R17\p1
```

两张正式表为 `results/local_side_scaling_results.csv`、`results/difficult_instance_results.csv`。每条结果均有最新汇总文件及字段来源；不需要重新求解即可读取。Gurobi 原始汇总没有独立绝对 Gap 字段，因此表中该单元格留空并注明，可由 UB−LB 分析得到，不能当作零。

正式相对认证区间宽度采用源码定义：`max(0, UB−LB) / max(1, |UB|)`，其中允许的界顺序误差为 1e-6；百分数再乘100。RD-ALM 必须使用 `p2_certified_*`，不能使用可能为 inf 的原始 `final_cert_gap`。SCP-LR 的宽区间不等于数值错误。有限区间也不等于达到目标 Gap 或所有内层调用达到请求精度。

二维名义时限依次为1800、2400、3000、3600秒，对应 B<600、600≤B<900、900≤B<1200、B≥1200。三维均以1800秒正式预算比较；Gurobi 使用 `baseline_time_limit`，它配置中未用于该基线的 `outer_time_limit=3600` 不应误判。结果时间没有裁剪；终止审计等可使时间超过名义预算。并行求解时间累加不等于墙钟时间。B1020、B1440 原生日志与 Model.Runtime 分别有约0.008、0.019秒差异，原因未完全确定，均保留原值并列为提示。

二维设备原生日志为 i7-14700，三维为 i7-14650HX；作者分别说明为台式机、联想笔记本。40份原生日志均报告 Gurobi13.0.1、win64、Windows 11+.0 (26200.2)。不能据此补写未记录的内存、Python或NumPy版本。

## 实例身份与浮点差异

JSON保留冻结源码输出的NaN/Infinity哨兵值，使用Python扩展JSON解析；不宣称兼容任意严格标准JSON解析器。

每个实例保留完整非 `args` 载荷；算法参数另存配置。最新二维每例三份、三维每例四份原始清单的完整数据载荷均严格一致。三维合并后的80条记录与20份原生日志完整，R17–R20亦有完整终止材料；各例同时严格匹配历史筛选入选实例。原始两种输出根目录只是路径元数据，没有改动数学实例或求解数值。

必须区分两层哈希：三维旧有块矩阵前缀哈希记录在 tail 之后、homogeneous A0 之前；仓库新增最终完整载荷、最终需求和任务周期字段哈希。**不能把旧前缀哈希误称为最终 homogeneous 矩阵的重算哈希。** 本环境没有完成完整实例矩阵重新生成。

二维旧草稿与最新载荷存在39,642个 PC1 派生浮点字段差异，最大5.684341886080802e-14。已定位到 SVD 投影及派生系数，但原始 NumPy/BLAS 信息缺失，不能断言具体环境原因。默认严格哈希检查。显式使用 `--identity-mode numerical` 时，仅二维已逐项列出的 PC1 派生浮点路径可接受绝对差异≤1e-13；其余字段、类型、结构、种子、NaN位置和哈希字符串严格匹配。不会放宽仓库文件SHA检查。三维非精确载荷不适用此模式。该阈值经过本次全部20个二维旧新载荷测试，不保证覆盖任何未来平台。它是透明的数值验收标准，不是两组实数系数定义完全相同MILP或保持全部最优解的数学证明。

## 筛选与复现边界

历史记录含400个第一阶段候选、60个第二阶段候选，460组排序/配置/原始结果已逐项核验。最终20例与第二阶段前20名、历史PowerShell入选列表、最新三维完整载荷一致。但 hunter/controller Python 程序缺失；名为stage3_1000s的第三阶段目录只有一条INTERRUPTED记录，实际config与summary预算均为600秒、运行61.04700016975403秒，RUN_CONFIG计划亦为600秒，不能按目录名推定1000秒或已完成；所谓入选CSV仅3字节BOM，不能视为完整筛选成果。因此仓库提供**固定入选实例复跑**和可验证的筛选证据，不提供虚假的全历史筛选自动复现功能。历史命令中的若干算法参数与正式重跑不同，不能替代当前配置。

## 已执行与未执行

已执行：递归ZIP/CRC和SHA核对、语法编译、140组实际解析器配置重建、40例归档身份比较、160条数值及原始审计溯源、全部命令预览、13项单元与负向测试。测试包括界顺序、Gap、种子或非白名单字段篡改、输出保护、错误退出及缺失依赖。

未执行：全套优化重跑、新机器端到端复现、Gurobi许可证/实际求解验证、Windows PowerShell运行、原始环境精确重建。一项只生成结构的轻量尝试在20秒限制内未完成首例，不能列为PASS。静态审计环境为Linux、Python3.13.5、NumPy2.3.5，未安装gurobipy。

文件清单SHA只保护已审计版本，不能把重新生成SHA当作绕过错误的方式。任何作者确认的后续修改须形成新版本清单。未擅自指定 LICENSE；公开上传不等于已授予复用许可。论文旧表未提供，未进行论文表格一致性背书。
