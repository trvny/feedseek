<div align="center">

<img src="assets/banner-feedseek.svg" alt="Feedseek" width="960">

<img src="assets/icons/favicon-96x96.png" alt="Feedseek" width="72">

# Feedseek 📡

**Samoodświeżające się, ulepszane feedy RSS/Atom + JSON oraz dedykowane Model Feeds dla LLM-ów i agentów: zarówno tam, gdzie feedu brakuje, jak i tam, gdzie natywny da się zrobić lepiej.**

[![feeds](https://img.shields.io/badge/feeds-112-d6541a?style=flat-square&logo=rss&logoColor=white)](feeds.yaml) [![CI](https://img.shields.io/github/actions/workflow/status/trvny/feedseek/update-feeds.yml?label=CI&logo=githubactions&logoColor=white&color=d6541a&style=flat-square)](https://github.com/trvny/feedseek/actions/workflows/update-feeds.yml) [![pages](https://img.shields.io/github/deployments/trvny/feedseek/github-pages?label=pages&logo=github&logoColor=white&color=d6541a&style=flat-square)](https://trvny.github.io/feedseek/) [![last commit](https://img.shields.io/github/last-commit/trvny/feedseek?color=d6541a&logo=git&logoColor=white&style=flat-square)](https://github.com/trvny/feedseek/commits/main) [![license](https://img.shields.io/github/license/trvny/feedseek?color=d6541a&style=flat-square)](LICENSE)
<a href="https://deepwiki.com/trvny/feedseek"><img src="https://deepwiki.com/badge.svg" alt="DeepWiki"></a>  
[![GitHubPages](https://img.shields.io/badge/-222222?style=for-the-badge&logo=githubpages&logoColor=white)](https://trvny.github.io/feedseek/)  
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) [![uv](https://img.shields.io/badge/uv-DE5FE9?style=flat-square&logo=uv&logoColor=white)](https://astral.sh)

**Polski** · [English](README.md) · [简体中文](README_zh.md)  

[**📡 Feedy**](https://trvny.github.io/feedseek/) · [**📖 Czytnik**](https://trvny.github.io/feedseek/reader/) · [**🗂 Rejestr**](feeds.yaml) · [**🧭 Technicznie**](docs/)  

</div>

Feedseek wyszukuje albo buduje feedy, normalizuje wpisy, usuwa duplikaty i publikuje wynik przez GitHub Pages. Harmonogram odświeża źródła co dwie godziny, a awaria jednego serwisu nie powinna wywracać pozostałych.

Feedseek nie jest tylko generatorem dla stron, które nie mają feedu. Natywny RSS/Atom jest wartościowym źródłem wejściowym, ale nie nietykalnym produktem końcowym: jeśli materiał źródłowy na to pozwala, Feedseek normalizuje i wzbogaca go do stabilniejszej, pełniejszej, bogatszej semantycznie i bardziej interoperacyjnej postaci, publikując obok XML jeden plik `feed_<name>.json`: zwarty Model Feed z oczyszczonym tekstem, kanonicznymi linkami, datami i jawnym oznaczeniem, czy wpis zawiera treść, streszczenie czy tylko tytuł. Model Feed zastąpił dawną parę JSON Feed 1.1 i `.model.json`; służy bezpośrednio modelom i agentom.

Celem jest wykorzystywanie możliwości RSS, Atom i JSON Feed tak dobrze, jak pozwalają dane źródłowe: trwałe identyfikatory, kanoniczne linki, prawdziwe daty publikacji i aktualizacji, użyteczne metadane, pochodzenie, kategorie oraz media. Scrapery i adaptery API uzupełniają braki natywnych źródeł. Nieudane albo puste pobranie nie zastępuje ostatniego poprawnego feedu.

## Feedy

<!-- registry-count: feeds.yaml (112 źródeł) -->
Pełna tabela źródeł i bezpośrednich plików feedów znajduje się w [angielskim README](README.md#feeds-), a wygodniejszy interfejs do przeglądania i subskrypcji na [stronie Feedseek](https://trvny.github.io/feedseek/).

- **Rejestr:** [`feeds.yaml`](feeds.yaml)
- **Wygenerowane XML/JSON/Model Feed:** [`feeds/`](feeds/)
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
- [Star History Monthly October 2026 | Execution](https://www.star-history.com/blog/execution)
- [Time for Saudi Clarity on Normalization with Israel](https://carnegieendowment.org/research/2026/10/time-for-saudi-clarity-on-normalization-with-israel)
- [Pożar pociągu w Balinie. Iskry zapaliły benzynę w 1909 r. - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMioAFBVV95cUxPV1JPdk93VlQtRjY4bVoxQ0ljXzcxX3cwWXhvM2ZHSUE0VDdjNlhTR0xQSzlMa0tnYXItbHBieXBmUkVyajN6R1BWamRHU19sTC02Q3oxRXpRcWphS3V1LU1fcWJCN0FVMDg0Qm12Nk0tWTdMRVhRU0ZEWVM1ZGxRd3ZXQm1pdEJsRWhNZWtFSVMyOUdXTVRqdWVDc1czX3NB?oc=5)
- [Serbia's Vucic concedes defeat to student led movement in parliamentary election](https://www.reuters.com/world/europe/serbias-vucic-concedes-defeat-student-led-movement-parliamentary-election-2026-10-25/)
- [Będzie duży przełom w polityce Serbii? Zamknięto lokale wyborcze - Radio Zet](https://news.google.com/atom/articles/CBMiogFBVV95cUxPUXJYdUlWWGtzZnhBRTcwOTA0Sy1wRjBhYnVpRmxjWUhYbGNHS0hsOGNDMnl6RUdxZTNwY2dUWjhYc2MyanBNa2RxS09xQm5hT3JvSXk0OGZ0VHNYb3F0SUdNX1N4ZWdBdEZ5Z0ppVnB5U2FnNU10Z2ZLXzdYNVdOcnF5Wk1VczFzM2RwNE05Q0ttWk96VnFkLUxSWTJFakc1LXc?oc=5)
- [Komisje bez kamer. Czego obawiają się krzeszowiccy radni? - krzeszowiceone.pl](https://news.google.com/atom/articles/CBMiqAFBVV95cUxQMWZFUDVHWkNUVXU2V3NyUGZwcnVUZGF2MEFXRllQcldzd0dBeWY3WkhnQ3R2UGFhVzRXUmkyMWNRQ1VxZXFmVWhOS2c3MnhjcEJsdWpsUkVmemE5anFzUFlDMy16Wk02OTVQM0ppd0NOT2dTb1g5MmdUb090dXZuWGtJdFdoV19yS1o0X3hmcTNVX294Rl9fT3VPVFhGTGVxVnVKQlczcULSAa4BQVVfeXFMT0p4SHVfX2VsRmxFdzdFRmtkU19UVVFxcENYN0VSUTAtVUNoMWo1ZjJ5Q2owbkNxc1VncDhhVWpwUFdNd1Y5WTFYNTNDbDJDdGxxWFZDMDFmR1VweTBLbXhtSkc1eGkwdVpmM3V3VUVrN0tIZzRueFBfSnB6MXgwZ3hzb2gxMjRvUDZVUGI2SDc0UDN2cUVsaUIzU1N4WHV5c0V1ZW9RcW1ZVi1SOVJB?oc=5)
<!--README_FEED:END-->

## 💬 Cytat z szuflady

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝All the domain names such as Google, Log In or Sign Up were free until 1995, but now everyone has to pay for every new domain name.❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## Other stuff

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/travnie/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
