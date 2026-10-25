<div align="center">

<img src="assets/banner-feedseek.svg" alt="Feedseek" width="960">

<img src="assets/icons/favicon-96x96.png" alt="Feedseek" width="72">

# Feedseek 📡

**自动更新并增强 RSS/Atom + JSON feed，并为 LLM 与 agent 生成专用 Model Feed：既为没有 feed 的网站补齐，也把已有的原生 feed 做得更好。**

[![feeds](https://img.shields.io/badge/feeds-112-d6541a?style=flat-square&logo=rss&logoColor=white)](feeds.yaml) [![CI](https://img.shields.io/github/actions/workflow/status/trvny/feedseek/update-feeds.yml?label=CI&logo=githubactions&logoColor=white&color=d6541a&style=flat-square)](https://github.com/trvny/feedseek/actions/workflows/update-feeds.yml) [![pages](https://img.shields.io/github/deployments/trvny/feedseek/github-pages?label=pages&logo=github&logoColor=white&color=d6541a&style=flat-square)](https://trvny.github.io/feedseek/) [![last commit](https://img.shields.io/github/last-commit/trvny/feedseek?color=d6541a&logo=git&logoColor=white&style=flat-square)](https://github.com/trvny/feedseek/commits/main) [![license](https://img.shields.io/github/license/trvny/feedseek?color=d6541a&style=flat-square)](LICENSE)
<a href="https://deepwiki.com/trvny/feedseek"><img src="https://deepwiki.com/badge.svg" alt="DeepWiki"></a>  
[![GitHubPages](https://img.shields.io/badge/-222222?style=for-the-badge&logo=githubpages&logoColor=white)](https://trvny.github.io/feedseek/)  
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) [![uv](https://img.shields.io/badge/uv-DE5FE9?style=flat-square&logo=uv&logoColor=white)](https://astral.sh)

[Polski](README_pl.md) · [English](README.md) · **简体中文**  

[**📡 Feeds**](https://trvny.github.io/feedseek/) · [**📖 Reader**](https://trvny.github.io/feedseek/reader/) · [**🗂 Registry**](feeds.yaml) · [**🧭 Internals**](docs/)  

</div>

Feedseek 会发现已有 feed，或在必要时构建新的 feed；随后统一条目格式、去重，并通过 GitHub Pages 发布结果。计划工作流每两小时刷新来源，同时把单个来源的故障隔离开，避免一个网站出问题拖垮全部 feed。

Feedseek 不只是为没有 feed 的网站生成替代品。原生 RSS/Atom 是很有价值的上游输入，但并不是不可改动的最终产品：只要源数据允许，Feedseek 就会继续规范化和增强它，生成更稳定、更完整、语义更丰富、兼容性更好的 feed，并在 XML 旁只发布一个 `feed_<name>.json` Model Feed，包含规范化纯文本、规范链接、日期和内容类型标记，供 LLM 与 agent 直接使用。它取代了之前分别发布的 JSON Feed 1.1 和 `.model.json` 文件。

目标是在源数据允许的范围内尽可能充分利用 RSS、Atom 和 JSON Feed 的能力，包括稳定的条目标识、规范链接、可信的发布时间与更新时间、有用的元数据、来源信息、分类和媒体。抓取器和 API adapter 用来补齐原生来源留下的缺口。失败或空的抓取结果不会覆盖最后一次成功生成的 feed。

灵感来自 [Olshansk/rss-feeds](https://github.com/Olshansk/rss-feeds) 与 [rss-bridge/rss-bridge](https://github.com/rss-bridge/rss-bridge)。

## Feeds ![XML](https://img.shields.io/badge/XML-005FAD?logo=xml&logoColor=fff&style=plastic)

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

这些 feed 对应的 Android 阅读器/播放器位于 **[travnie/kanarek](https://github.com/travnie/kanarek)**。

## [许可证](LICENSE)

[![License](https://www.shieldcn.dev/github/license/trvny/feedseek.svg?variant=branded&size=xm&mode=light&theme=neutral&font=jetbrains-mono)](https://spdx.org/licenses/MIT)    [THIRD_PARTY_NOTICES](docs/THIRD_PARTY_NOTICES.md)

## 📰 小新闻

<!--README_FEED:START-->
- [Star History Monthly October 2026 | Execution](https://www.star-history.com/blog/execution)
- [Time for Saudi Clarity on Normalization with Israel](https://carnegieendowment.org/research/2026/10/time-for-saudi-clarity-on-normalization-with-israel)
- [Pożar pociągu w Balinie. Iskry zapaliły benzynę w 1909 r. - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMioAFBVV95cUxPV1JPdk93VlQtRjY4bVoxQ0ljXzcxX3cwWXhvM2ZHSUE0VDdjNlhTR0xQSzlMa0tnYXItbHBieXBmUkVyajN6R1BWamRHU19sTC02Q3oxRXpRcWphS3V1LU1fcWJCN0FVMDg0Qm12Nk0tWTdMRVhRU0ZEWVM1ZGxRd3ZXQm1pdEJsRWhNZWtFSVMyOUdXTVRqdWVDc1czX3NB?oc=5)
- [Serbia's Vucic concedes defeat to student led movement in parliamentary election](https://www.reuters.com/world/europe/serbias-vucic-concedes-defeat-student-led-movement-parliamentary-election-2026-10-25/)
- [Będzie duży przełom w polityce Serbii? Zamknięto lokale wyborcze - Radio Zet](https://news.google.com/atom/articles/CBMiogFBVV95cUxPUXJYdUlWWGtzZnhBRTcwOTA0Sy1wRjBhYnVpRmxjWUhYbGNHS0hsOGNDMnl6RUdxZTNwY2dUWjhYc2MyanBNa2RxS09xQm5hT3JvSXk0OGZ0VHNYb3F0SUdNX1N4ZWdBdEZ5Z0ppVnB5U2FnNU10Z2ZLXzdYNVdOcnF5Wk1VczFzM2RwNE05Q0ttWk96VnFkLUxSWTJFakc1LXc?oc=5)
- [Komisje bez kamer. Czego obawiają się krzeszowiccy radni? - krzeszowiceone.pl](https://news.google.com/atom/articles/CBMiqAFBVV95cUxQMWZFUDVHWkNUVXU2V3NyUGZwcnVUZGF2MEFXRllQcldzd0dBeWY3WkhnQ3R2UGFhVzRXUmkyMWNRQ1VxZXFmVWhOS2c3MnhjcEJsdWpsUkVmemE5anFzUFlDMy16Wk02OTVQM0ppd0NOT2dTb1g5MmdUb090dXZuWGtJdFdoV19yS1o0X3hmcTNVX294Rl9fT3VPVFhGTGVxVnVKQlczcULSAa4BQVVfeXFMT0p4SHVfX2VsRmxFdzdFRmtkU19UVVFxcENYN0VSUTAtVUNoMWo1ZjJ5Q2owbkNxc1VncDhhVWpwUFdNd1Y5WTFYNTNDbDJDdGxxWFZDMDFmR1VweTBLbXhtSkc1eGkwdVpmM3V3VUVrN0tIZzRueFBfSnB6MXgwZ3hzb2gxMjRvUDZVUGI2SDc0UDN2cUVsaUIzU1N4WHV5c0V1ZW9RcW1ZVi1SOVJB?oc=5)
<!--README_FEED:END-->

## 💬 抽屉里的引语

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝All the domain names such as Google, Log In or Sign Up were free until 1995, but now everyone has to pay for every new domain name.❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## 其他项目

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/travnie/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
