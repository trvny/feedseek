<div align="center">

<img src="assets/banner-feedseek.svg" alt="Feedseek" width="960">

<img src="assets/icons/favicon-96x96.png" alt="Feedseek" width="72">

# Feedseek 📡

**Samoodświeżające się, ulepszane feedy RSS/Atom + JSON: zarówno tam, gdzie feedu brakuje, jak i tam, gdzie natywny da się zrobić lepiej.**

[![feeds](https://img.shields.io/badge/feeds-111-d6541a?style=flat-square&logo=rss&logoColor=white)](feeds.yaml) [![CI](https://img.shields.io/github/actions/workflow/status/trvny/feedseek/update-feeds.yml?label=CI&logo=githubactions&logoColor=white&color=d6541a&style=flat-square)](https://github.com/trvny/feedseek/actions/workflows/update-feeds.yml) [![pages](https://img.shields.io/github/deployments/trvny/feedseek/github-pages?label=pages&logo=github&logoColor=white&color=d6541a&style=flat-square)](https://trvny.github.io/feedseek/) [![last commit](https://img.shields.io/github/last-commit/trvny/feedseek?color=d6541a&logo=git&logoColor=white&style=flat-square)](https://github.com/trvny/feedseek/commits/main) [![license](https://img.shields.io/github/license/trvny/feedseek?color=d6541a&style=flat-square)](LICENSE)
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

<!-- registry-count: feeds.yaml (111 źródeł) -->
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
- [Operetka wróci do Młoszowej - Przelom.pl](https://news.google.com/atom/articles/CBMif0FVX3lxTE1zeVl6VHlCYlBqSlNRYU5TVGoxV19VSTU0a3FCckpiYjdUT0tMOEptNTRkLV92MzRXdUlINXIxajBRVWVvOVQzSkw3RVdCM3IxUFd5aVZETHNtOG1LN053dHRHUmEtaUZDeW5qTXJjUXl6WC1XdGFYYVZpRXJIUkU?oc=5)
- [Seniorzy z UTW ruszyli po wiedzę, zdrowie i przygodę - Przelom.pl](https://news.google.com/atom/articles/CBMirgFBVV95cUxPcGRwc1ludjBJSWFaZ0dWZ0JUUkxwczBoSWQ2cGVRUkgxb3NNWWo0ZnJqNW5Id1dyWkFCa1pZQVJRU3VmdXVkajlnZ0xsWHJFaDJrYUtMUmNFeVFta0otcFFSUS1UMlhrTXNhcHF4SExiTnJQZXY5YUtyY2xuSnFYV0ctcEhZcDR5bUFyUDZTdkpHbktDY2lIMFZSdVUyLWpSTkdfWGx4Rl93c1g2SVE?oc=5)
- [Amazon in talks to buy AI startup Decart for around $7 billion, WSJ reports](https://www.reuters.com/business/retail-consumer/amazon-talks-buy-ai-startup-decart-around-7-billion-wsj-reports-2026-10-11/)
- [W mijającym tygodniu odeszli od nas \[5 - 10 październik\] - Przelom.pl](https://news.google.com/atom/articles/CBMiogFBVV95cUxQRTFFRDRGbkVMMXI0Ym8yd2g1a3IwaXczZm1VaUpmbWRwaVdwd3Z0TWRlSWZOcW1IVUdPcGluV2VicHo2blVOREt5djFERnowR3dsSkFwN0FraV9HYUt1UEE5T3VXM1RqZG14bHNOVFhLMWUxenBFa2E5ZWpyaHROWERHUXVOZUVldnBfNWhnZnY1X0tnMjIydGQzeG9tQmF3NHc?oc=5)
- [Wiązanki i kwiaty na cmentarz Wszystkich Świętych 2026. Najpiękniejsze stroiki na cmentarz z żywych kwiatów 12.10.2026 - Dziennik Łódzki](https://news.google.com/atom/articles/CBMi8wFBVV95cUxObjFvTnNmTEh2c2ZWZGttUWJRX25MLU5sRHJJSWVlVWhQdjFvMjVjaFE3amdLd015THpMY2hjb3V3azJOY0xFQ1dRU3lQcjRRaTNZTzJBUEJYWGxOYS1TX3Y2M1N5V2dwQ2xLV0FSblkwaTVCZGFkU2xNdmNSRTY3WmRTal9COW95T1BfaE0zT2pBaENXTk9OU3JKaEwxRnpiZkcwOFBnX3h0ZnNDbTBmUTJEYm4wMVNQQ1pBckQzTE5GdHJwckl0b3hJbzBDaVJhX2ItZTZoMlJRTW5TUEJFOGtRT21udE5DSzBWeEE1LTJsdzg?oc=5)
- [At least 72 Sudanese artisanal miners killed in strike, rights monitor says](https://www.reuters.com/world/africa/least-72-sudanese-artisanal-miners-killed-strike-saturday-rights-monitor-says-2026-10-11/)
<!--README_FEED:END-->

## 💬 Cytat z szuflady

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝A programmer developed an operating system called TempleOS in Hospitalized for mental health problems, he believes that TempleOS is literally the Third Temple as biblically prophesied. Per God’s “instructions,” the OS uses a 640×480, 16 color display, and uses the language HolyC.❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## Other stuff

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/travnie/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
