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
- [Oto "genetyczny ChatGPT". Tak wygląda potężna broń naukowców](https://antyweb.pl/genetyczny-chatgpt)
- [Nowy Park Wodny niedaleko Krakowa! Już gotowy, otwarcie we wrześniu. Basen w Krzeszowicach czeka jeszcze na cennik - Dziennik Polski](https://news.google.com/atom/articles/CBMi7AFBVV95cUxNSHZ3aldwaXJYUHJIekxWem1WaEhBaEdfbm8waUFrdU1tanhwVmNuMGkyME53NlNyNzRRbXk1MWlzT0dqam9maExBV1NnbEJ0MHNIX2NKUzdUejlObEI1ZFNyYVUzWkU4UDZGd21la3c0VGxDeF9Yd1VZV3NPVnNRVm8tYTRlX0duNkVUd2loUHZEaVZoN0NrWkJVSFp5TnFqTXJsTnF4X1RBYVg1dHVMVmZrbU52alNHT2p3Mk9Na3pCREYwS01GWG1OUFBLUjVNbm5WOGxtMzQzRDVLRUZDVUo3c0lzTWhoWkN2Ng?oc=5)
- [Procesory Apple M5 Ultra i M6 biją nowe rekordy. Brak im konkurencji](https://antyweb.pl/procesory-apple-m5-ultra-i-m6-bija-nowe-rekordy-brak-im-konkurencji)
- [9-latek wydał 446 tysięcy złotych na reklamy swoich filmików. Policzyłem, co za te pieniądze dostał](https://promptowy.com/9-latek-118-tysiecy-dolarow-reklamy-youtube/)
- [Kolejowa inwestycja za 147 mln zł w Jaworznie. Projekt wrócił do procedowania - jaw.pl](https://news.google.com/atom/articles/CBMiZEFVX3lxTE01elNJOWxVbWprdjNNbkxJR0VLRkdlREZvV2FiODQwSS0zU3hQMGxkT291M0dMc0RhSjZMcjVNU3BGNXJXcGNrZGhqMFdxazR5cl9qdXZNWGRQMDRJcEhEelZIWU0?oc=5)
- [Degradation with Gemini 3.8 Flash](https://www.githubstatus.com/incidents/nlxnbqnkdzdl)
<!--README_FEED:END-->

## 💬 Cytat z szuflady

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝HDMI charges its licensed manufacturers $10,000 per year plus $0.15 per cable, reduced to $0.05 if the HDMI logo is on the socket.❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## Other stuff

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/travnie/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
