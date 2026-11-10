# 内容地图

从[技能入口](../SKILL.md)按任务读取资料。每份参考解释自身职责，模板展示填法，示例展示真实可检查的产物。

## 故事结构

| 文件 | 内容 |
|---|---|
| [character-design.md](../references/story/character-design.md) | 人物设计与角色记录 |
| [continuity-management.md](../references/story/continuity-management.md) | 跨集事实与连续性管理 |
| [episode-endings.md](../references/story/episode-endings.md) | 分集结尾与悬念卡点 |
| [genre-selection.md](../references/story/genre-selection.md) | 题材选择与故事发动机 |
| [novel-adaptation.md](../references/story/novel-adaptation.md) | 小说改编与覆盖规划 |
| [opening-episodes.md](../references/story/opening-episodes.md) | 开篇三集设计 |
| [opening-hooks.md](../references/story/opening-hooks.md) | 开场钩子与观看动机 |
| [series-structure.md](../references/story/series-structure.md) | 全剧架构、分集节奏与发行卡点 |
| [story-engine.md](../references/story/story-engine.md) | 情绪契约与单元回合 |
| [story-reinvention.md](../references/story/story-reinvention.md) | 故事机制提炼与原创重构 |

## 剧本写作

| 文件 | 内容 |
|---|---|
| [conflict-design.md](../references/writing/conflict-design.md) | 五种冲突骨架与叙事承载 |
| [dialogue-craft.md](../references/writing/dialogue-craft.md) | 台词设计与表达复核 |
| [scene-craft.md](../references/writing/scene-craft.md) | 场景工艺与阶段兑现 |
| [voiceover-design.md](../references/writing/voiceover-design.md) | 独白旁白与声音通道 |

## 视觉制作

| 文件 | 内容 |
|---|---|
| [asset-prompts.md](../references/production/asset-prompts.md) | 资产图词与单时刻关键帧 |
| [camera-and-delivery.md](../references/production/camera-and-delivery.md) | 摄影执行与模型提交 |
| [camera-language.md](../references/production/camera-language.md) | 摄影语言与提示词参考 |
| [production-state.md](../references/production/production-state.md) | 项目状态、覆盖与返修 |
| [segment-planning.md](../references/production/segment-planning.md) | 内容驱动的分段与时长判断：内容闭合、生产闭合、关联图谱、八步决策与记录 |
| [storyboard-workflow.md](../references/production/storyboard-workflow.md) | 视觉制作与分镜流程 |
| [timing-and-sync.md](../references/production/timing-and-sync.md) | 内容预算与声画同步 |

## 斗法设计

| 文件 | 内容 |
|---|---|
| [fight-choreography.md](../references/fight/fight-choreography.md) | 斗法编舞与视听执行 |
| [fight-data-contract.md](../references/fight/fight-data-contract.md) | 斗法JSON数据契约（1.2） |
| [fight-mechanics.md](../references/fight/fight-mechanics.md) | 斗法机制与能力条件 |

## 审阅与修订

| 文件 | 内容 |
|---|---|
| [content-review.md](../references/review/content-review.md) | 剧本与视觉内容审阅 |
| [evaluation-method.md](../references/review/evaluation-method.md) | 技能评测与真实使用验证 |
| [review-exceptions.md](../references/review/review-exceptions.md) | 保护性例外与检查复核 |
| [revision-protocol.md](../references/review/revision-protocol.md) | 审阅问题卡与修订规程 |

## 模板

| 文件 | 用途 |
|---|---|
| [剧本](../templates/screenplay-template.md) | 标准、漫剧和长档完整单集填写结构。 |
| [项目台账](../templates/project-ledger-template.md) | 故事四账、回合、热/冷状态及同项目视觉制作账。 |
| [视觉制作包](../templates/storyboard-package-template.md) | 文本契约2.0，预算、分段决策、镜头、帧、各段母稿与证据；不兼容旧版。 |

## 示例

| 文件 | 覆盖范围 |
|---|---|
| [标准单集](../examples/screenplay-standard.md) | 标准档整集剧本。 |
| [长档单集](../examples/screenplay-extended.md) | 双回合与中段小钩。 |
| [场景原文](../examples/storyboard-source.md) / [完整制作包](../examples/storyboard-scene.md) | 18秒完整场景，三段，每段6秒；保留作短窗口2.0示例。 |
| [内容驱动分段](../examples/storyboard-content-segmented.md) | 同一18秒场景按内容拆8+10，2.0分段决策、依据、段内多镜与逐段母稿。 |
| [忠实斗法原文](../examples/faithful-fight-source.md) / [完整制作包](../examples/faithful-fight-scene.md) | 6秒短窗口2.0示例：两段、无对白、单次接触与无伤罢手。 |
| [剑与近战](../examples/fight/sword-duel.json) | 剑斗、身体接点与攻防。 |
| [阵法救援](../examples/fight/formation-rescue.json) | 阵法、救援目标与资源支出。 |
| [御空法相](../examples/fight/aerial-manifestation.json) | 空间尺度、御空与法相。 |
| [幻术反制](../examples/fight/illusion-counterplay.json) | 所知/实际、判断与呼吸。 |

## 工具与测试

| 文件 | 用途 |
|---|---|
| [check_episode.py](../scripts/check_episode.py) | 单集与视觉制作包的统一校验入口，也支持可选战斗JSON。 |
| [check_series.py](../scripts/check_series.py) | 故事台账与视觉连续性。 |
| [check_storyboard.py](../scripts/check_storyboard.py) | 内部V1～V16检查，含2.0分段决策记录。 |
| [fight_contract.py](../scripts/fight_contract.py) | 内部JSON1.2校验与六项同源导出。 |
| [verify_package.py](../scripts/verify_package.py) | 总检与输入SHA证据。 |

五份测试文件覆盖视觉、连续性、战斗契约、CLI与包结构；运行方法见[维护说明](maintenance.md)。机器检查不代替[内容审阅](../references/review/revision-protocol.md)或实际媒体观察。
