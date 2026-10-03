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
- [The Debt Toll Booth: A Modular Solution to Addressing Sovereign Debt Crises](https://carnegieendowment.org/research/2026/10/the-debt-toll-booth-a-modular-solution-to-addressing-sovereign-debt-crises)
- [Wieś podzielona na pół. Tędy już nie przejedziemy - krzeszowiceone.pl](https://news.google.com/atom/articles/CBMinwFBVV95cUxNaHJ5TWZmSl92bFNxemU0RW50MnEwcHFuTUR3aTduc0Z1LTdPWTdwcFhpZGJ2X2FJNnBwZU9ndHBuUHEwYUhjRm53eVU3RklINnlGRFBQdjVBdjBZMTMtRU9MYWpaVkN4Q3lTTzVKMDV0NElzRXdzdHdLQUFYQUw2WHFRZjE1bWRMMUZha3NwWE5RXzhrQklLVVpzNE5mWjDSAaQBQVVfeXFMTmZ3cG1zd2h2Nk9fdWlFbDBtRzhjMkhRU3dQVUptYm1hbkRPVkV5N2lrMHJGLXpDUFR4VkkzZUtSM3dkNllNdjRLdHpzYzViaGs2REJ5Y1M1cTZYNnFNbmE2OGtpTVM2TTZ0MHR5M3k5alYtUXF2Q3B2QVlnblh2WTVCX1B2RklHbEU2LVNHYWo1c0FWRXpQemREckhqTlFqVXVLSGk?oc=5)
- [Ostatnia stacja Drogi Żelaznej Warszawsko-Wiedeńskiej. Oto dworzec Sosnowiec Maczki w czasach swojej świetności - Dziennik Zachodni](https://news.google.com/atom/articles/CBMi6AFBVV95cUxOaXR4NDQ4U1U1M05paHd1TkhJUzJ1VV83VDZsbTF1cUh6dnV5aXBKREFZZXljb1hhOTFCSkpJcktlX0Ffa2ptOFk1ZHlHN3V5cDhEVmtJNEdUYnQ1SUdOS3J3U0d4eWMwSkdlcThIZVVtZlI4eXV3LVpMdmZFMzVvMGJpQ1ZHdzNhbktadl9BcEFrcVVDMzFIR0dYc3Rxd3hkV09CR0hCa0N6ZHJJdU9FN0lZdzVQLWFZZ0pyOWE2VU4zWTlVelhUNnZuTi1aZ3VIcUVXMHAtWFhUUDFsU2E4OGh2YVpPU0h3?oc=5)
- [Przegląd AI: 3 października 2026](https://promptowy.com/przeglad-ai-2026-10-03/)
- [Zamknięcie dnia: Agenci wymknęli się spod kontroli - i mamy dowody](https://promptowy.com/zamkniecie-dnia-agenci-wymkneli-sie-spod-kontroli-i-mamy-dowody/)
- [Co oznacza zielone kółko na WhatsApp?](https://antyweb.pl/co-oznacza-zielone-kolko-na-whatsapp)
<!--README_FEED:END-->

## 💬 Cytat z szuflady

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝The first electronic computer ENIAC weighed more than 27 tons and took up 1800 square feet.❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## Other stuff

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/travnie/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
