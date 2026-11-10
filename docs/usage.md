# 使用指南

## 以交付范围提出请求

| 场景 | 可直接使用的请求 |
|---|---|
| 原创短剧 | “做一部40集长档家庭短剧，先给立项、人物和全剧结构。” |
| 只写正文 | “接现有台账写第3集，只要剧本，不做视觉包。” |
| 定稿场转分镜 | “原文照录，制作完整18秒场景，视频16:9，模型单次生成0–30秒之间任意时长，按剧本内容判断每段多长，一次交齐全部提示词。” |
| 分段判断 | “模型支持0–30秒之间任意时长，不要默认30秒也不均分；按事件链、动作相位、话轮和稳定边界说明为什么这样分段。” |
| 斗法设计 | “在既定能力和结局下设计这场斗法，交攻防设计、资产、镜头、关键帧、全部视频母稿和审阅。” |
| 局部返修 | “只改第2段的镜位，动作、台词与段界不变，同步更新受影响的帧和母稿。” |
| 继续与恢复 | “沿上次项目继续下一未覆盖段”；如状态缺失，提供项目目录或已有产物。 |
| 重发 | “逐字重发第2段原版母稿”，按实际历史文件复送，不推进剧情覆盖。 |

已有制作参数直接沿用，缺少模型名称可先做平台无关母稿。完整制作的范围由用户决定；单场不被强套整剧立项、付费墙或整集字数。视频比例与人物/场景/道具资产版式分别设置。

## 文件交付

剧本项目以源文与同一项目台账保存事实；制作包附预算、事件链、导演镜头、关键帧、逐段母稿、状态和检查范围。若拆文件，索引应能定位全场和全部段，不要求用户自行拼接差异片段。示例格式见[剧本模板](../templates/screenplay-template.md)、[台账模板](../templates/project-ledger-template.md)、[视觉包模板](../templates/storyboard-package-template.md)。

首次人物图词包含身份母图及同轮四视图；默认母图9:16半身，四视图横版、上脸1/3与下方无头正侧背2/3。原文必要的信件、门牌或刻字按揭示时机保留；“无文字”只用于排除额外水印和说明，不能删掉剧情证据。

## 检查命令

在技能包根运行，项目文件可换为绝对路径。Windows使用 `python`；其他系统按环境使用 `python3`。校验器使用标准库，不需要模型或媒体服务。

```powershell
# 完整单集
python -X utf8 -B scripts/check_episode.py examples/screenplay-standard.md --format standard
python -X utf8 -B scripts/check_episode.py examples/screenplay-extended.md --format long
# 定稿短场：不套整集E阈值；--source对应精确原文
python -X utf8 -B scripts/check_episode.py examples/storyboard-scene.md --scope visual --source examples/storyboard-source.md
# 2.0内容驱动分段示例：同一场拆8+10，检查V16分段依据
python -X utf8 -B scripts/check_episode.py examples/storyboard-content-segmented.md --scope visual --source examples/storyboard-source.md
# 新交付必须有制作包时
python -X utf8 -B scripts/check_episode.py 项目/单集制作稿.md --require-visual
# 有全剧上下文的连续性台账
python -X utf8 -B scripts/check_series.py 项目/台账.md --episodes 40 --script-dir 项目/剧本
```

同一文件含多个视觉包并共用整篇源文时，每包写 `【源文行范围】：起行–止行`，从1起算且不重叠；单包恰好覆盖全部原文时可省略。工具退出码：0为无FAIL（可能仍有WARN/NOTE），1为检查失败，2为用法或输入错误。实际问题需结合原文核对。

## 可选战斗存档与导出

```powershell
python -X utf8 -B scripts/check_episode.py --combat-json examples/fight/sword-duel.json
python -X utf8 -B scripts/check_episode.py --combat-json examples/fight/sword-duel.json --export 新交付目录
```

存档只支持JSON契约1.2；1.1旧存档不再兼容，须升级后重交。导出产生 `project.json` 与设计、资产、分镜、关键帧、视频提示词、审阅六份Markdown。目标必须尚不存在；已有文件或目录不会被覆盖。内部工具不替用户推导动作，也不要求日常自然语言制作先填JSON。字段和数值语义见[斗法数据契约](../references/fight/fight-data-contract.md)。

## 评估结果的含义

E检查剧本的结构和粗估，V检查视觉包结构、显式状态、时轴及对白，S检查系列台账。V16只检查2.0的分段决策记录、能力范围、段长依据和边界记录，不判断叙事合理性；未给源文不宣称完成逐字保真。台词识别之外的动作、揭示和结果需语义复核；平台能力、实际输入和媒体观察另外记录。

视觉文本契约当前为2.0：只接受2.0包，不再兼容1.1/1.2旧包，旧包须按2.0重交。【单次生成时长能力】、分段策略、分段决策表、每段【分段依据】和段内多镜母稿写法为必填。分段判断按[分段决策](../references/production/segment-planning.md)：模型支持0–30秒之间任意时长，但每段长度由内容关联、自然时长和稳定边界决定，不默认取上限、不均分。

制作预算先计话轮、动作、阅读、停顿及顺并行关系，再核目标时长。E16的粗估×1.20不能当试读结果；没有试读或测量时写ESTIMATED。真实发布要求按当时官方材料核对，本地扫描不表示平台已审核。
