<div align="center">

<img src="assets/banner-feedseek.svg" alt="Feedseek" width="960">

<img src="assets/icons/favicon-96x96.png" alt="Feedseek" width="72">

# Feedseek 📡

**Samoodświeżające się, ulepszane feedy RSS/Atom + JSON: zarówno tam, gdzie feedu brakuje, jak i tam, gdzie natywny da się zrobić lepiej.**

[![feeds](https://img.shields.io/badge/feeds-107-d6541a?style=flat-square&logo=rss&logoColor=white)](feeds.yaml) [![CI](https://img.shields.io/github/actions/workflow/status/trvny/feedseek/update-feeds.yml?label=CI&logo=githubactions&logoColor=white&color=d6541a&style=flat-square)](https://github.com/trvny/feedseek/actions/workflows/update-feeds.yml) [![pages](https://img.shields.io/github/deployments/trvny/feedseek/github-pages?label=pages&logo=github&logoColor=white&color=d6541a&style=flat-square)](https://trvny.github.io/feedseek/) [![last commit](https://img.shields.io/github/last-commit/trvny/feedseek?color=d6541a&logo=git&logoColor=white&style=flat-square)](https://github.com/trvny/feedseek/commits/main) [![license](https://img.shields.io/github/license/trvny/feedseek?color=d6541a&style=flat-square)](LICENSE)
<a href="https://deepwiki.com/trvny/feedseek"><img src="https://deepwiki.com/badge.svg" alt="DeepWiki"></a>  
[![GitHubPages](https://img.shields.io/badge/-222222?style=for-the-badge&logo=githubpages&logoColor=white)](https://trvny.github.io/feedseek/)  
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) [![uv](https://img.shields.io/badge/uv-DE5FE9?style=flat-square&logo=uv&logoColor=white)](https://astral.sh)

**Polski** · [English](README.md) · [简体中文](README_zh.md)  

[**📡 Feedy**](https://trvny.github.io/feedseek/) · [**📖 Czytnik**](https://trvny.github.io/feedseek/reader/) · [**🗂 Rejestr**](feeds.yaml) · [**🧭 Technicznie**](docs/)  

</div>

Feedseek wyszukuje albo buduje feedy, normalizuje wpisy, usuwa duplikaty i publikuje wynik przez GitHub Pages. Harmonogram odświeża źródła co dwie godziny, a awaria jednego serwisu nie powinna wywracać pozostałych.

Feedseek nie jest tylko generatorem dla stron, które nie mają feedu. Natywny RSS/Atom jest wartościowym źródłem wejściowym, ale nie nietykalnym produktem końcowym: jeśli materiał źródłowy na to pozwala, Feedseek normalizuje i wzbogaca go do stabilniejszej, pełniejszej, bogatszej semantycznie i bardziej interoperacyjnej postaci, publikując obok XML także JSON Feed 1.1.

Celem jest wykorzystywanie możliwości RSS, Atom i JSON Feed tak dobrze, jak pozwalają dane źródłowe: trwałe identyfikatory, kanoniczne linki, prawdziwe daty publikacji i aktualizacji, użyteczne metadane, pochodzenie, kategorie oraz media. Scrapery i adaptery API uzupełniają braki natywnych źródeł. Nieudane albo puste pobranie nie zastępuje ostatniego poprawnego feedu.

## Feedy

<!-- registry-count: feeds.yaml (107 źródeł) -->
Pełna tabela źródeł i bezpośrednich plików feedów znajduje się w [angielskim README](README.md#feeds-), a wygodniejszy interfejs do przeglądania i subskrypcji na [stronie Feedseek](https://trvny.github.io/feedseek/).

- **Rejestr:** [`feeds.yaml`](feeds.yaml)
- **Wygenerowane XML/JSON:** [`feeds/`](feeds/)
- **Indeks źródeł:** [`docs/sources.md`](docs/sources.md)
- **Notatki o poszczególnych feedach:** [`docs/feeds.md`](docs/feeds.md)

## Dokumentacja

- [Pipeline, enrichment, użycie lokalne i układ repozytorium](docs/architecture.md)
- [Źródła i kompromisy poszczególnych feedów](docs/feeds.md)
- [Działanie i utrzymanie cache](docs/cache.md)
- [Wygenerowany indeks źródeł](docs/sources.md)

Androidowy czytnik/player tych feedów to osobny projekt: **[travnie/kanarek](https://github.com/travnie/kanarek)**.

## [Licencja](LICENSE)

[![Licencja](https://www.shieldcn.dev/github/license/trvny/feedseek.svg?variant=branded&size=xm&mode=light&theme=neutral&font=jetbrains-mono)](https://spdx.org/licenses/MIT)  [THIRD_PARTY_NOTICES](docs/THIRD_PARTY_NOTICES.md)

## 📰 Mininewsy

<!--README_FEED:START-->
- [Episode 2: Financing War in the Grey Zone](https://www.rusi.org/podcasts/suspicious-transaction-report/episode-2-financing-war-grey-zone)
- [Rozkochów zachwycił jury. Jest wysokie miejsce i nagroda - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMipAFBVV95cUxPY0tiLU1SOHViRk1TcWtxZXltVWoyVlJYTmJ0NW1wa0ppN1p6cnlWOEE1NWtzYjRyYXRhN29KbmJKLW5pcHp6emJMTkJIVmJzd1d0d2duVEdHU0JuMXR6aEJ1bWFMeTJhSWd2QUE3Z3ZHSko2d2pRZ0tPRVF3aDdQczc1Z2Fiek9kVjhWbldTODJ3NlJUUGFFVkNTSFU5S0JiY1FSTQ?oc=5)
- [Recenzja Trails in the Sky 2nd Chapter. Must play dla fanów dobrych jRPG](https://antyweb.pl/recenzja-trails-in-the-sky-2nd-chapter-must-play-dla-fanow-dobrych-jrpg)
- [Ostrzeżenie pierwszego stopnia dla Chrzanowa i okolic. Uwaga na gestą mgłę - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMivAFBVV95cUxOZmdOeF9uQS13NWZsLUoxN1k2QWVSQWtJUkFKU3FtMEF0YjVWbnJqTjVqbnladUhfcWkwNFFjSG5nWHVDbGhkUmdHNzk1emx1QWstR0VJYUdUMGotTlVlOXZob2JmZ1ZteHN3Z3JxRWNqb2FtWmRYME81UXNhWXFBc1FWVERMSXN2MHRTY3N2cWdKY3k5UUItc19mTG84Zi1WaGEyNU1UNDRTUlFPWUpKa3RtbTRoWFZvT2VaOQ?oc=5)
- [PLLuM: polski model językowy państwa. Co to jest, gdzie działa i czym różni się od Bielika](https://promptowy.com/pllum/)
- [Jensen Huang: kim jest szef Nvidii, ile jest wart i jak zbudował najcenniejszą firmę świata](https://promptowy.com/jensen-huang/)
<!--README_FEED:END-->

## 💬 Cytat z szuflady

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝The first word spoken on the internet was “lo”. It was supposed to be “login” but the computer crashed after the first two letters.❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## Other stuff

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/travnie/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
