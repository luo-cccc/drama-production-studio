# 更名与内容整理记录

整理日期：2026-11-07。当前名称为“短剧创制工作室”，规范技能标识和建议安装目录为 `drama-production-studio`，版本6.0.0。工作区检出目录可以带环境后缀，不改变包标识。前一名称为 `short-drama-factory`，原目录为 `short-drama-factory-master`。

## 本轮变更

- 统一品牌、目录、53项资源文件名、Python模块、工具示例和文档引用。
- 27份参考按故事、写作、视觉制作、斗法和审阅五组组织；3份模板与原8份示例保持可用，并新增本轮独立模拟的原文和完整制作包。
- 剧本模板保留填写结构，详细台词、声音与时长方法链接到对应参考，清除不存在的旧步骤和下游模块引用。
- 使用与维护文档分别服务实际任务和开发验证；来源清单记录新目标，摄影资料、战斗样例、代码归属与许可保留。
- 宣传图、旧横幅、广告/安装时间元数据、Python缓存及592份历史审查文件移出运行包；旧版本冗长日志与原始证据保存到包外恢复档案。
- 将旧榜单、播放量、算法比例和未经复核的法规摘要移出硬规则；仍保留的案例统一视为带日期的历史样本，不能直接当作当前平台结论。可用故事机制与明确的本地检查范围继续保留。

## 接口与数据

`SKILL.md`、`README.md`、`CHANGELOG.md`、`LICENSE`保留约定文件名。八种对话模式、原命令别名、E/V/S检查编号、CLI参数、视觉文本契约1.1及战斗JSON1.1/1.2沿用其含义，导出文件名保持契约要求。文件系统和内部模块名使用下表的新路径，原文件路径不再是当前调用位置。

## 文件更名表

| 原路径 | 当前路径 |
|---|---|
| `references/emotion-flow-roundtrip.md` | [references/story/story-engine.md](../references/story/story-engine.md) |
| `references/hongguo-beat-sheet.md` | [references/story/series-structure.md](../references/story/series-structure.md) |
| `references/genre-map.md` | [references/story/genre-selection.md](../references/story/genre-selection.md) |
| `references/character-bible.md` | [references/story/character-design.md](../references/story/character-design.md) |
| `references/first-three-eps-beat-card.md` | [references/story/opening-episodes.md](../references/story/opening-episodes.md) |
| `references/golden-3s-hook-library.md` | [references/story/opening-hooks.md](../references/story/opening-hooks.md) |
| `references/cliffhanger-master-formulas.md` | [references/story/episode-endings.md](../references/story/episode-endings.md) |
| `references/webnovel-adaptation.md` | [references/story/novel-adaptation.md](../references/story/novel-adaptation.md) |
| `references/mechanism-imitation.md` | [references/story/story-reinvention.md](../references/story/story-reinvention.md) |
| `references/continuity-ledger.md` | [references/story/continuity-management.md](../references/story/continuity-management.md) |
| `references/craft-quality-layer.md` | [references/writing/scene-craft.md](../references/writing/scene-craft.md) |
| `references/dialogue-doctor-anti-ai.md` | [references/writing/dialogue-craft.md](../references/writing/dialogue-craft.md) |
| `references/inner-monologue-vo.md` | [references/writing/voiceover-design.md](../references/writing/voiceover-design.md) |
| `references/conflict-modes.md` | [references/writing/conflict-design.md](../references/writing/conflict-design.md) |
| `references/visual-directing-layer.md` | [references/production/storyboard-workflow.md](../references/production/storyboard-workflow.md) |
| `references/visual-assets.md` | [references/production/asset-prompts.md](../references/production/asset-prompts.md) |
| `references/visual-timing.md` | [references/production/timing-and-sync.md](../references/production/timing-and-sync.md) |
| `references/visual-production.md` | [references/production/camera-and-delivery.md](../references/production/camera-and-delivery.md) |
| `references/visual-state.md` | [references/production/production-state.md](../references/production/production-state.md) |
| `references/camera-reference.md` | [references/production/camera-language.md](../references/production/camera-language.md) |
| `references/combat-mechanics.md` | [references/fight/fight-mechanics.md](../references/fight/fight-mechanics.md) |
| `references/combat-staging.md` | [references/fight/fight-choreography.md](../references/fight/fight-choreography.md) |
| `references/combat-contract.md` | [references/fight/fight-data-contract.md](../references/fight/fight-data-contract.md) |
| `references/screenplay-compliance-rules.md` | [references/review/content-review.md](../references/review/content-review.md) |
| `references/script-doctor-protocol.md` | [references/review/revision-protocol.md](../references/review/revision-protocol.md) |
| `references/protective-counterexamples.md` | [references/review/review-exceptions.md](../references/review/review-exceptions.md) |
| `references/skill-eval-protocol.md` | [references/review/evaluation-method.md](../references/review/evaluation-method.md) |
| `scripts/validate_episode.py` | [scripts/check_episode.py](../scripts/check_episode.py) |
| `scripts/validate_series.py` | [scripts/check_series.py](../scripts/check_series.py) |
| `scripts/visual_checks.py` | [scripts/check_storyboard.py](../scripts/check_storyboard.py) |
| `scripts/combat_contract.py` | [scripts/fight_contract.py](../scripts/fight_contract.py) |
| `scripts/run_checks.py` | [scripts/verify_package.py](../scripts/verify_package.py) |
| `templates/episode-format.md` | [templates/screenplay-template.md](../templates/screenplay-template.md) |
| `templates/ledger.md` | [templates/project-ledger-template.md](../templates/project-ledger-template.md) |
| `templates/visual-package.md` | [templates/storyboard-package-template.md](../templates/storyboard-package-template.md) |
| `examples/ep01-longwang-demo.md` | [examples/screenplay-standard.md](../examples/screenplay-standard.md) |
| `examples/long-format-3min-demo.md` | [examples/screenplay-extended.md](../examples/screenplay-extended.md) |
| `examples/ep01-visual-package-demo.md` | [examples/storyboard-scene.md](../examples/storyboard-scene.md) |
| `examples/visual-source.md` | [examples/storyboard-source.md](../examples/storyboard-source.md) |
| `examples/combat/01-sword-and-body.json` | [examples/fight/sword-duel.json](../examples/fight/sword-duel.json) |
| `examples/combat/02-formation-rescue.json` | [examples/fight/formation-rescue.json](../examples/fight/formation-rescue.json) |
| `examples/combat/03-aerial-avatar.json` | [examples/fight/aerial-manifestation.json](../examples/fight/aerial-manifestation.json) |
| `examples/combat/04-illusion-and-breath.json` | [examples/fight/illusion-counterplay.json](../examples/fight/illusion-counterplay.json) |
| `tests/test_visual_checks.py` | [tests/test_storyboard_checks.py](../tests/test_storyboard_checks.py) |
| `tests/test_series_visual.py` | [tests/test_series_continuity.py](../tests/test_series_continuity.py) |
| `tests/test_combat_contract.py` | [tests/test_fight_contract.py](../tests/test_fight_contract.py) |
| `tests/test_unified_cli.py` | [tests/test_episode_cli.py](../tests/test_episode_cli.py) |
| `tests/test_package_contracts.py` | [tests/test_skill_package.py](../tests/test_skill_package.py) |
| `docs/integration-sources.md` | [docs/source-attribution.md](source-attribution.md) |
| `docs/integration-sources.json` | [docs/source-manifest.json](source-manifest.json) |
| `docs/xianxia-source-notices.md` | [docs/upstream-notices.md](upstream-notices.md) |
| `docs/integration-review-2026-11-07.md` | [docs/verification.md](verification.md) |
| `.sosoclaw-market.json` | [package-manifest.json](../package-manifest.json) |

完整机器映射见[名称映射](name-map.json)。来源清单中的原包路径、通知内的引用和历史版本名属于归属材料，按原始身份保留。

## 恢复与历史证据

整理前已创建完整ZIP并校验657个文件及SHA-256清单。恢复档案位于本地项目父目录的 `.skill-archives/drama-production-studio/` 下，包含 `before-reorganization.zip`、`backup-manifest.json` 与重命名计划；具体归档时间目录由本轮交付记录提供。需要历史失败日志或原模拟时，从ZIP按清单提取到包外目录，不把历史SKILL副本再放进运行包。

当前包的使用、检查和来源说明均可独立阅读；包外档案仅供恢复和历史审计，不是运行依赖。新的检查证据与迁移验证结果见[验证记录](verification.md)。

工作区检出目录可以带环境后缀；包身份以 `SKILL.md` 和 `package-manifest.json` 的规范名称为准。
