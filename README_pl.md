<div align="center">

<img src="assets/banner-feedseek.svg" alt="Feedseek" width="960">

<img src="assets/icons/favicon-96x96.png" alt="Feedseek" width="72">

# Feedseek 📡

**Samoodświeżające się, ulepszane feedy RSS/Atom + JSON: zarówno tam, gdzie feedu brakuje, jak i tam, gdzie natywny da się zrobić lepiej.**

[![feeds](https://img.shields.io/badge/feeds-109-d6541a?style=flat-square&logo=rss&logoColor=white)](feeds.yaml) [![CI](https://img.shields.io/github/actions/workflow/status/trvny/feedseek/update-feeds.yml?label=CI&logo=githubactions&logoColor=white&color=d6541a&style=flat-square)](https://github.com/trvny/feedseek/actions/workflows/update-feeds.yml) [![pages](https://img.shields.io/github/deployments/trvny/feedseek/github-pages?label=pages&logo=github&logoColor=white&color=d6541a&style=flat-square)](https://trvny.github.io/feedseek/) [![last commit](https://img.shields.io/github/last-commit/trvny/feedseek?color=d6541a&logo=git&logoColor=white&style=flat-square)](https://github.com/trvny/feedseek/commits/main) [![license](https://img.shields.io/github/license/trvny/feedseek?color=d6541a&style=flat-square)](LICENSE)
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

<!-- registry-count: feeds.yaml (109 źródeł) -->
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
- [Battery Ecosystems: A Comparative Analysis of Lithium-Ion Tech Policy](https://carnegieendowment.org/research/2026/09/battery-ecosystems-a-comparative-analysis-of-lithium-ion-tech-policy)
- [Już jutro wielkie otwarcie w Krzeszowicach. Cennik Parku Wodnego wzbudza emocje - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMiwwFBVV95cUxNaFhRTTFoLW1xWURhaGQ5NzB3MFV0RE90REJXU3FjVGUyZjVESGRxY0NyanlwcTc0VHg3Y3dCemRlMVZibmtUUUhnd3RRSXFZOEhrMXZlVHZLSEVfekNheTR2SFFEOEhIemdIZGFYNTVES244TkZyWjc0Um9mY1Q4TG0zWll4b2lCVjNYMC03aDRGVS1NaFYzeElHY2dEN1pXRC1aVUl4UG1WRUp5ZXBTb1BvdmMxWE9FUjE1Ty1sOFR4NVk?oc=5)
- [Obława w powiecie chrzanowskim. 13 osób zatrzymanych - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMioAFBVV95cUxQb1lkb3ZXUGVRQ09pRWJvdWtadk5vczJBRzZBYi02N0pXQjBHcWE0bVRRSnlsLVQ2dTdNWFp4X1JpNXZhQnVqUzkwcFcxVmZhWHVzRmZGREZQelFsczRPSWlXb2dxVzFwOS1pajcyc25tc0hXTWQyMDNlb2Zxa0RKZjRMbkFCbXFkWEdZZkdLeVNXSEp5MXZOakFTSVZWaEdF?oc=5)
- [Lipowiec wkrótce zamknięty na ponad dwa lata. Będzie wielki remont zamku - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMiwwFBVV95cUxQQ3c0RXB5NFRRZHA4QnpYVjZ2R0JSMDlKdEhudFZ6QV9xQmRuSG5BcU5KU3hNZFJlXy1fLXpISEh2VVBJdktabkQzbFNicFZVa3g4dzZQaFZBcmtYZFZjN1FyR1cyaDExR1RXazlmQ2VlMTBpOEFOVWFra1B5c1RYMWowb2FEdzY3WEJsUnllNFRmR1JfcjNxb1pDYWkycHA3NEROOWtZcjU5VzhwaHZRU21wTGREb0FNcGdSUEZQM19fMUk?oc=5)
- [US appeals court rules against Kalshi, says states can regulate prediction markets](https://www.reuters.com/business/finance/us-appeals-court-rules-against-kalshi-says-states-can-regulate-prediction-2026-09-25/)
- [Zbyt płytkie groby na cmentarzu w Jaworznie? Mieszkaniec mówi o nieprawidłowościach - jaw.pl](https://news.google.com/atom/articles/CBMiYkFVX3lxTE9LdFB4MUZtb3J4N3ZTUmh1MllxZFBHNmV1ZkxQSDgwTmlXcUJpRDhUNzZwSktHWmFMRTlScy05aXVxOWpMa1VrdzJBRFJhTHNkZGd1Szh6Z0FJSDNGQlVZMUdB?oc=5)
<!--README_FEED:END-->

## 💬 Cytat z szuflady

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝4004 was the name given to the first microprocessor by Intel.❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## Other stuff

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/travnie/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
