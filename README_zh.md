<div align="center">

<img src="assets/banner-feedseek.svg" alt="Feedseek" width="960">

<img src="assets/icons/favicon-96x96.png" alt="Feedseek" width="72">

# Feedseek :satellite_antenna:

**自动更新并增强 RSS/Atom + JSON feed，并为 LLM 与 agent 生成专用 Model Feed：既为没有 feed 的网站补齐，也把已有的原生 feed 做得更好。**

[![feeds](https://img.shields.io/badge/feeds-117-d6541a?style=flat-square&logo=rss&logoColor=white)](feeds.yaml) [![CI](https://img.shields.io/github/actions/workflow/status/trvny/feedseek/update-feeds.yml?label=CI&logo=githubactions&logoColor=white&style=flat-square)](https://github.com/trvny/feedseek/actions/workflows/update-feeds.yml) [![pages](https://img.shields.io/github/deployments/trvny/feedseek/github-pages?label=pages&logo=github&logoColor=white&style=flat-square)](https://trvny.github.io/feedseek/) [![last commit](https://img.shields.io/github/last-commit/trvny/feedseek?color=d6541a&logo=git&logoColor=white&style=flat-square)](https://github.com/trvny/feedseek/commits/main) [![license](https://img.shields.io/github/license/trvny/feedseek?color=d6541a&logo=opensourceinitiative&logoColor=white&style=flat-square)](https://spdx.org/licenses/MIT)
<a href="https://deepwiki.com/trvny/feedseek"><picture><source srcset="https://img.shields.io/badge/DeepWiki-trvny%2Ffeedseek-blue.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAyCAYAAAAnWDnqAAAAAXNSR0IArs4c6QAAA05JREFUaEPtmUtyEzEQhtWTQyQLHNak2AB7ZnyXZMEjXMGeK/AIi+QuHrMnbChYY7MIh8g01fJoopFb0uhhEqqcbWTp06/uv1saEDv4O3n3dV60RfP947Mm9/SQc0ICFQgzfc4CYZoTPAswgSJCCUJUnAAoRHOAUOcATwbmVLWdGoH//PB8mnKqScAhsD0kYP3j/Yt5LPQe2KvcXmGvRHcDnpxfL2zOYJ1mFwrryWTz0advv1Ut4CJgf5uhDuDj5eUcAUoahrdY/56ebRWeraTjMt/00Sh3UDtjgHtQNHwcRGOC98BJEAEymycmYcWwOprTgcB6VZ5JK5TAJ+fXGLBm3FDAmn6oPPjR4rKCAoJCal2eAiQp2x0vxTPB3ALO2CRkwmDy5WohzBDwSEFKRwPbknEggCPB/imwrycgxX2NzoMCHhPkDwqYMr9tRcP5qNrMZHkVnOjRMWwLCcr8ohBVb1OMjxLwGCvjTikrsBOiA6fNyCrm8V1rP93iVPpwaE+gO0SsWmPiXB+jikdf6SizrT5qKasx5j8ABbHpFTx+vFXp9EnYQmLx02h1QTTrl6eDqxLnGjporxl3NL3agEvXdT0WmEost648sQOYAeJS9Q7bfUVoMGnjo4AZdUMQku50McDcMWcBPvr0SzbTAFDfvJqwLzgxwATnCgnp4wDl6Aa+Ax283gghmj+vj7feE2KBBRMW3FzOpLOADl0Isb5587h/U4gGvkt5v60Z1VLG8BhYjbzRwyQZemwAd6cCR5/XFWLYZRIMpX39AR0tjaGGiGzLVyhse5C9RKC6ai42ppWPKiBagOvaYk8lO7DajerabOZP46Lby5wKjw1HCRx7p9sVMOWGzb/vA1hwiWc6jm3MvQDTogQkiqIhJV0nBQBTU+3okKCFDy9WwferkHjtxib7t3xIUQtHxnIwtx4mpg26/HfwVNVDb4oI9RHmx5WGelRVlrtiw43zboCLaxv46AZeB3IlTkwouebTr1y2NjSpHz68WNFjHvupy3q8TFn3Hos2IAk4Ju5dCo8B3wP7VPr/FGaKiG+T+v+TQqIrOqMTL1VdWV1DdmcbO8KXBz6esmYWYKPwDL5b5FA1a0hwapHiom0r/cKaoqr+27/XcrS5UwSMbQAAAABJRU5ErkJggg==" type="image/svg+xml"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></picture></a>  
[![Web reader](https://img.shields.io/badge/Web%20reader-open-222222?style=flat-square&logo=githubpages&logoColor=white)](https://trvny.github.io/feedseek/reader/)  
[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/) [![uv](https://img.shields.io/badge/uv-DE5FE9?style=flat-square&logo=uv&logoColor=white)](https://docs.astral.sh/uv/)

[Polski](README_pl.md) · [English](README.md) · **简体中文**  

[**:satellite_antenna: Feeds**](https://trvny.github.io/feedseek/) · [**:book: Reader**](https://trvny.github.io/feedseek/reader/) · [**:card_file_box: Registry**](feeds.yaml) · [**:compass: Internals**](docs/)  

</div>

Feedseek 会发现已有 feed，或在必要时构建新的 feed；随后统一条目格式、去重，并通过 GitHub Pages 发布结果。计划工作流每两小时刷新来源，同时把单个来源的故障隔离开，避免一个网站出问题拖垮全部 feed。

Feedseek 不只是为没有 feed 的网站生成替代品。原生 RSS/Atom 是很有价值的上游输入，但并不是不可改动的最终产品：只要源数据允许，Feedseek 就会继续规范化和增强它，生成更稳定、更完整、语义更丰富、兼容性更好的 feed，并在 XML 旁只发布一个 `feed_<name>.json` Model Feed，包含规范化纯文本、规范链接、日期和内容类型标记，供 LLM 与 agent 直接使用。它取代了之前分别发布的 JSON Feed 1.1 和 `.model.json` 文件。

目标是在源数据允许的范围内尽可能充分利用 RSS、Atom 和 JSON Feed 的能力，包括稳定的条目标识、规范链接、可信的发布时间与更新时间、有用的元数据、来源信息、分类和媒体。抓取器和 API adapter 用来补齐原生来源留下的缺口。失败或空的抓取结果不会覆盖最后一次成功生成的 feed。

灵感来自 [Olshansk/rss-feeds](https://github.com/Olshansk/rss-feeds) 与 [rss-bridge/rss-bridge](https://github.com/rss-bridge/rss-bridge)。

## Feeds [![XML](https://img.shields.io/badge/XML-005FAD?logo=xml&logoColor=fff&style=plastic)](https://www.w3.org/XML/)

Feed 列表会持续变化，因此中文 README 不复制整张动态表。当前完整清单请直接查看：

- [Feeds 页面](https://trvny.github.io/feedseek/)
- [源注册表 `feeds.yaml`](feeds.yaml)
- [自动生成的来源清单](docs/sources.md)

每个输出 feed 都可以从 GitHub Pages 或仓库中的 `feeds/` 目录访问。网站 favicon 在渲染时从 Google favicon 服务或 DuckDuckGo 获取，不会把这些图片提交进仓库。

## 文档

- [流水线、enrichment、本地使用方式与仓库结构](docs/architecture.md)
- [各 feed 的来源与设计取舍](docs/feeds.md)
- [缓存行为与维护](docs/cache.md)
- [自动生成的来源清单](docs/sources.md)
- [LLM 与智能体接入：远程 MCP 服务器、WebMCP、llms.txt、Model Feed JSON Schema](docs/agents.md)

这些 feed 对应的 Android 阅读器/播放器位于 **[travnie/kanarek](https://github.com/travnie/kanarek)**。

## [许可证](LICENSE)

[![License](https://www.shieldcn.dev/github/license/trvny/feedseek.svg?variant=branded&size=xm&mode=light&theme=neutral&font=jetbrains-mono)](https://spdx.org/licenses/MIT)    [THIRD_PARTY_NOTICES](docs/THIRD_PARTY_NOTICES.md)

## 📰 小新闻

<!--README_FEED:START-->
- [Trust but Verify: Implementing Frontier AI Policy in California and Beyond](https://carnegieendowment.org/research/2026/11/trust-but-verify-implementing-frontier-ai-policy-in-california-and-beyond)
- [Promises Made, Promises Unmet: The NPP’s Struggle to Reform Sri Lanka](https://carnegieendowment.org/research/2026/11/promises-made-promises-unmet-the-npps-struggle-to-reform-sri-lanka)
- [W Filipowicach zagrają cztery kapele - zakliczyninfo.pl](https://news.google.com/atom/articles/CBMijAFBVV95cUxPOXdxVjVMdHc0YUw2akRlZlJZREw0WUVmeHdvbDNqNUo5cnNRM1ZWUm9aSEJzSUlKNU1hSkF2anlwUm5sTGpzTHN1NG9wZXhhSGJYbHB6RWhUaUxlQ3FOTnlwNmloNnJLNnJnbjVmYzJ6RWFqMGdvZ3VzVjJNQUZ4SU9qUzFINjBIQ25BSQ?oc=5)
- [Product of the Day — A Magical Bag Of Holding Except The Only Thing It Can Hold Is Infinite Fedoras](https://anycrap.shop/product/a-magical-bag-of-holding-except-the-only-thing-it-can-hold-is-infinite-fedoras)
- [Cat Fact of the Day](https://catfact.ninja/)
- [Joke of the Day](https://djtech.net/humor/things_to_think_about.htm)
<!--README_FEED:END-->

## 💬 抽屉里的引语

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝More than 80% of the emails sent daily are spams.❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## 其他项目

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/travnie/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
