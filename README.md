# 短剧创制工作室

**drama-production-studio · 8.0.0**

在同一个 Skill 中完成短剧策划、剧本、资产图词、导演分镜、关键帧和逐段视频提示词，并处理仙侠斗法、连续性和返修。可以从创意开始，也可以把定稿的一场直接转为制作稿。

## 开始使用

在对话中说明素材、交付范围和已有制作条件。例如：

> 用短剧创制工作室，把下面的定稿场景做成完整制作包。台词和结局不改，视频16:9，单次生成不超过30秒，按剧本内容判断每段多长，一次交齐资产、分镜、关键帧与所有段的视频提示词。

只需要剧本时直接说明“只写剧本”；需要局部返修时指定影响范围。已有的 `/立项大纲`、`/全剧大纲`、`/分集规划`、`/写剧本`、`/剧本医生`、`/极速短剧`、`/合规审核`、`/连写` 等指令继续可用。自然语言同样有效。

唯一技能入口是 [SKILL.md](SKILL.md)。包的规范标识和建议安装目录均为 `drama-production-studio`；从归档或工作区检出时目录可以带环境后缀，只要 `SKILL.md` 与 `package-manifest.json` 保持规范标识。参考、模板、工具与示例随包保留。

## 阅读导航

| 文档 | 内容 |
|---|---|
| [使用指南](docs/usage.md) | 请求示例、交付范围、检查命令和文件导出 |
| [内容地图](docs/content-map.md) | 28份参考、3份模板、11份示例和5个工具的用途 |
| [维护说明](docs/maintenance.md) | 规则职责、回归方法与可移植性检查 |
| [更名与整理记录](docs/migration.md) | 新旧名称、清理范围和恢复说明 |
| [验证记录](docs/verification.md) | 当前版本实际运行结果、使用模拟复测和未测范围 |
| [来源归属](docs/source-attribution.md) | 来源能力、代码、摄影资料、示例及许可边界 |
| [版本变化](CHANGELOG.md) | 当前变化及整合基线 |

## 本地检查

工具使用Python标准库，无需访问原始来源目录。下面命令在包根运行；当前验证环境与结果见验证记录。

```powershell
python -X utf8 -B scripts/check_episode.py examples/screenplay-standard.md --format standard
python -X utf8 -B scripts/check_episode.py examples/storyboard-scene.md --scope visual --source examples/storyboard-source.md
python -X utf8 -B scripts/check_episode.py examples/storyboard-content-segmented.md --scope visual --source examples/storyboard-source.md
python -X utf8 -B scripts/check_episode.py --combat-json examples/fight/sword-duel.json
python -X utf8 -B scripts/verify_package.py --output 检查记录.json
```

检查器区分完整剧本和独立场景。两个视觉示例均为18秒完整场景，不是标准时长的整集示例；`storyboard-content-segmented.md`演示按内容把同一场拆成8+10秒，三段6秒示例保留作短窗口2.0示例。斗法JSON只支持1.2契约，是可选存档形式，普通用户无需填写。

2.0包另由V16检查分段策略、候选比较和每段时长依据；V16只查记录与硬边界，不判断叙事合理性。

文字结构、状态和时码检查不证明实际片长或媒体效果。目标时长、估算预算、试读测量和实际媒体分别记录；本包不会因交付提示词而自动调用媒体生成。

## 目录

```text
drama-production-studio/
├── SKILL.md
├── package-manifest.json
├── references/
│   ├── story/
│   ├── writing/
│   ├── production/
│   ├── fight/
│   └── review/
├── templates/
├── scripts/
├── examples/
├── tests/
└── docs/
```

原项目的MIT文本见 [LICENSE](LICENSE)。吸收的第三方资料按来源说明分别归属，根许可证不重新授权未声明许可的来源内容。
