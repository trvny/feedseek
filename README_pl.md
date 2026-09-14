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
- [RUSI Reflects: The Mecca Agreement: From US Primacy to Regional Agency](https://www.rusi.org/news-and-comment/rusi-reflects/rusi-reflects-mecca-agreement-us-primacy-regional-agency)
- [W Płokach znów tłumy pielgrzymów. Wieczorem niebo rozświetlą fajerwerki \(WIDEO,ZDJĘCIA\) - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMixAFBVV95cUxQaC1GaFhPX2pHZFJfamMxZzF2YmhfQm80Skc0dXpKUjhacjhsVG1zTVJIVlVsZTBCeURHbHVpb1hxcFZQUnp5UFVsRjkzWUNrUnZad19lR25McVM3aUFOejdxR3FyYVhUaFlFZXJBdjFvUXhkQ3RXZVJNVEZabFhNMm1xbE04QnpfeHhVa29ibGFOeS1vaFRTc0hDV2MyM2tYTHFDcDRkbEFOZVAzVy1paHU4OW8tRmJOd0ZJV3lPSHgtMXRt?oc=5)
- [Dokąd trafia drewno z lokalnych lasów? Znamy największego odbiorcę - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMiywFBVV95cUxONzNnUVJJRFJGLUVFWDZZejZTRzM0LV9faTRmSm5sV3hqQWM0OFExRjZwMXk0VW9LUlVreUVjMTFmUTdGQmdKUWNIdDVXTDA2WE82YjhtY2dSWFMtNGhoU1hYNTQtVV9PdEJONTctTno5bHdjN09JTHpVQWl2b21DQm8yclA0U0lET3R3OUhYeUZnXzhUR0VycW5TR3dWMFBySXFvaGF6Ukprb2xZckd4OE1NOE5oRnBGNXg4dXAtZVJaVW8wMzZ1Z2ZfOA?oc=5)
- [Trump says he is removing U.S. tariffs on Irish whiskey](https://www.reuters.com/world/us/trump-says-he-is-lifting-tariffs-irish-whiskey-2026-09-13/)
- [Ahead of Fed meeting, Trump says US should have world's lowest interest rate](https://www.reuters.com/business/ahead-fed-meeting-trump-says-us-should-have-worlds-lowest-interest-rate-2026-09-13/)
- [Trump says he will consider request to release more 9/11 records](https://www.reuters.com/world/us/trump-says-hell-consider-whether-release-more-911-records-2026-09-13/)
<!--README_FEED:END-->

## 💬 Cytat z szuflady

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝When you don't know what you believe, everything becomes an argument. Everything is debatable. But when you stand for something, decisions are obvious. — Anonymous❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## Other stuff

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/travnie/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
