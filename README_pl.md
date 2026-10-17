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

Feedseek nie jest tylko generatorem dla stron, które nie mają feedu. Natywny RSS/Atom jest wartościowym źródłem wejściowym, ale nie nietykalnym produktem końcowym: jeśli materiał źródłowy na to pozwala, Feedseek normalizuje i wzbogaca go do stabilniejszej, pełniejszej, bogatszej semantycznie i bardziej interoperacyjnej postaci, publikując obok XML także JSON Feed 1.1. Każdy feed dostaje też `feed_<name>.model.json`: zwarty Model Feed z oczyszczonym tekstem i jawną informacją, czy wpis zawiera treść, streszczenie czy tylko tytuł, przeznaczony bezpośrednio do konsumpcji przez modele i agentów.

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
- [Chwila nieuwagi na ulicy Matejki. Policja ukarała 39-latkę - Przelom.pl](https://news.google.com/atom/articles/CBMiqAFBVV95cUxOYWVucmkycVFvSGk3cS0ydXc2dXFtelNHY3VNMU5RRU42RlpRbjNvYndldjVIenJXU1c4V0o1eC00MWtsMkc2LUZNLW9XRUx3VzItYV9VV28xeXE0RHMyQTR6NUlzVzZnVXl3Z2NoT0ZLenNmRnBQUVVkdktaOGp2clROQ1U4cjZEWGdmaFpLODNYSUdLOUZhby02aTFkanBCSHNkNll3M2o?oc=5)
- [kanarek-companion created review 5537758476 on PR #170 in travnie/Kanarek](https://github.com/travnie/Kanarek/pull/170?feedseek_event=17342195699#pullrequestreview-5537758476)
- [gptomek created review 5537630750 on PR #170 in travnie/Kanarek](https://github.com/travnie/Kanarek/pull/170?feedseek_event=17341748350#pullrequestreview-5537630750)
- [Volvo Cars expands automated driving partnership with Nvidia](https://www.reuters.com/business/autos-transportation/volvo-cars-expands-automated-driving-partnership-with-nvidia-2026-10-15/)
- [Kolej wróci na trasę Trzebinia–Wadowice? Jest nowa deklaracja i ważny ruch PKP PLK - Przelom.pl](https://news.google.com/atom/articles/CBMivgFBVV95cUxQM3J3Y2VQblVnQ3NPR1hsdEVuSmNKd0JURWNIQkRyNkZsa2lWNHVIQWNTX3NZY3ZJWURvMm0xZ1lzYlRjM0gzNEY0aHYyNlF1MmNST3lmS2ExX3M2cnFPSFZCcHhyU1ZVYW1oNXZ5ZDNJVGluN0xWQTllZUhleURpNVBHMTZrSHJqcTI1NmRZVnhkUnNXc1JrZkxwV1VFTElOcERCdWpqbDdaWU5CVjdsX2VubEVDbEpsdS0tb1dR?oc=5)
- [gptomek created review 5537371072 on PR #168 in travnie/Kanarek](https://github.com/travnie/Kanarek/pull/168?feedseek_event=17340832619#pullrequestreview-5537371072)
<!--README_FEED:END-->

## 💬 Cytat z szuflady

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝“Perl: The only language that looks the same before and after RSA encryption.”— Keith Bostic❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## Other stuff

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/travnie/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
