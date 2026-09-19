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
- [Recasting American Power in Latin America](https://carnegieendowment.org/research/2026/09/recasting-american-power-in-latin-america)
- [Kopalnia, która zbudowała Libiąż - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMijAFBVV95cUxNbGFTQUJOTE1oVDQzT3B4TDNQQlYwblNLZnNIa2dOUTlDMV9YTUdkeThmSTlTWjRnaFZySERoSjZPeVF2eVVxb0drNl8yQmdPeWRDazVRUnRwYV9seVRoVUotN3FIbklfZVd5NjNxMTMzMEtlOTlYb3BPTmRybkZITTljZXZNVUtacWVDYQ?oc=5)
- [Co łączy salezjanów w Oświęcimiu z Juliuszem Słowackim? Niezwykła historia - Gazeta Krakowska](https://news.google.com/atom/articles/CBMiuAFBVV95cUxNd3VELWw1UkxOeG1VOHMtbF82R0N3OVp6amp2Mnd0Mi0wMGxQNGtEaUtNekhvdjltR2lWYUxKQW4yNGpoaFhxNk5oamIzMlNlM1VycXRZTkN3c1NsZktVdjVqTXExamc0LXpId3QwYU5hOENCbWg5MFA5ZUJ6cE5ocWNmeTVhN0xpNm9tMWNhNUpUQVpDVGoxWGgxbTI0WkpIcGRBVTY4MVRiakFXaS0tSWF4RmQ4MTdE?oc=5)
- [Janina znów trzęsie powiatem. Gdzie teraz trwa wydobycie? - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMirgFBVV95cUxPSnhkRndIdkFSNmdMeXVyRFJoS19tWDFfekFEN1k4TXBpQ1hyTTUwb09rRFZBVjdhbVBfLU9lUmU5UnprUWtYZExYeVJUVFZZUHFKdl9LMWhHaUdaWWxwbDQwakppZWNSTlNMQnB1WHZQWTA1RTBva1p6N092alk2NE51dmMtUmh3UkE3aHg4cEQxeXc0YXZGQjN2TXNOM0RuQjhOSnlmcWJHODlzT3c?oc=5)
- [Turkey says it could help meet Saudi military needs under defence pact](https://www.reuters.com/business/aerospace-defense/turkey-says-it-could-help-meet-saudi-military-needs-under-defence-pact-2026-09-19/)
- [Slovak PM Fico says some in West seek war between Russia and NATO](https://www.reuters.com/world/slovak-pm-fico-says-some-west-seek-war-between-russia-nato-2026-09-19/)
<!--README_FEED:END-->

## 💬 Cytat z szuflady

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝My passion has been to build an enduring company where people were motivated to make great products; the products, not the profits, were the motivation. Sculley flipped these priorities to where the goal was to make money. It's a subtle difference, but it ends up meaning everything. — Steve Jobs❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## Other stuff

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/travnie/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
