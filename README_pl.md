<div align="center">

<img src="assets/banner-feedseek.svg" alt="Feedseek" width="960">

<img src="assets/icons/favicon-96x96.png" alt="Feedseek" width="72">

# Feedseek 📡

**Samoodświeżające się, ulepszane feedy RSS/Atom + JSON: zarówno tam, gdzie feedu brakuje, jak i tam, gdzie natywny da się zrobić lepiej.**

[![feeds](https://img.shields.io/badge/feeds-106-d6541a?style=flat-square&logo=rss&logoColor=white)](feeds.yaml) [![CI](https://img.shields.io/github/actions/workflow/status/trvny/feedseek/update-feeds.yml?label=CI&logo=githubactions&logoColor=white&color=d6541a&style=flat-square)](https://github.com/trvny/feedseek/actions/workflows/update-feeds.yml) [![pages](https://img.shields.io/github/deployments/trvny/feedseek/github-pages?label=pages&logo=github&logoColor=white&color=d6541a&style=flat-square)](https://trvny.github.io/feedseek/) [![last commit](https://img.shields.io/github/last-commit/trvny/feedseek?color=d6541a&logo=git&logoColor=white&style=flat-square)](https://github.com/trvny/feedseek/commits/main) [![license](https://img.shields.io/github/license/trvny/feedseek?color=d6541a&style=flat-square)](LICENSE)
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

<!-- registry-count: feeds.yaml (106 źródeł) -->
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

Androidowy czytnik/player tych feedów to osobny projekt: **[twojstar/kanarek](https://github.com/twojstar/kanarek)**.

## [Licencja](LICENSE)

[![Licencja](https://www.shieldcn.dev/github/license/trvny/feedseek.svg?variant=branded&size=xm&mode=light&theme=neutral&font=jetbrains-mono)](https://spdx.org/licenses/MIT)  [THIRD_PARTY_NOTICES](docs/THIRD_PARTY_NOTICES.md)

## 📰 Mininewsy

<!--README_FEED:START-->
- [RUSI Reflects: The Mecca Agreement: From US Primacy to Regional Agency](https://www.rusi.org/news-and-comment/rusi-reflects/rusi-reflects-mecca-agreement-us-primacy-regional-agency)
- [Libiążanin w „Szansie na sukces” - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMigwFBVV95cUxPbjMxVUtESjNJd0YxaldtTHJQU0x1RU00clQ2YS1qNW1YcjQ1d0NqSXhNYnlIaHpRSndha3VHUE5YbkxNT1VSbTRtRVQ3V0ZnVjdPV2cySFZxMzZIYlhoTmZsdF9GT2x1NXVYXzFBdFhxaUlsTmlVVkxZeWExMzEzTno5TQ?oc=5)
- [Nie będzie wody, możliwe też zmętnienie. Wodociągi podają termin prac - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMitAFBVV95cUxORm4zX25MdWdPaFNMMjNIU1ZnMXJQb1RsTWZaWTBkaTdpVHJYZV9GcW9Ya05kYWxUT1pLcHNlVnFjZlozSmxLOU1rTDZkMGQ4RnBUYmJlam1Pakdqd0JIejRmRjVHXzFqV2dzVExyblVobGhmSE5oV0FYbmNCLW9sbXA2TFZDS196LVRVNUVOS0UtQUg0SENWTUh2X1VwTm5fbmhtTHdiRnNuTHRTT1kxemx6TEE?oc=5)
- [Brak koncentracji i za duża prędkość. Pięć wypadków w powiecie oświęcimskim w jeden dzień - oswiecimonline.pl](https://news.google.com/atom/articles/CBMiuwFBVV95cUxNUmJKVEotNDZYN1VHNFVEMWVLbGpVOUlZcFZfcTZmSXdLNjl0YWNLamRaRnFLVGVaR0dPUC1ldnkwbHIyM1ZLR1AyTGZXWGd0QTh3T0Q5MzVSYnpOVUFuYVVjTmtPYTh4aWFCWkNtQ2U3YVNTZFBPSHJ1cm4yakZ0dTRMRFpyZV9oTHRxUEk2X0pLaUxzc3lTNG1nSDd3bjFWTEZsVFI5Uk1GNEhFRjNpTVNfWUtMWWpLT0Rj?oc=5)
- [Nie żyje były radny i sołtys - Przelom.pl - portal ziemi chrzanowskiej](https://news.google.com/atom/articles/CBMihAFBVV95cUxQS0ZBd0dkN0pKM3d0OThoNE1VZURsUno0VjcxRmlWMDBDdml2ZW54UWw5U1pjTXZTZUhZRF9jclpvUm9DLVlQb3h5eWFtM0tCV1VQUDgwZURzWmpRd1hjblFYV05KTXhrRXZlc2FLbVllX19YRW5hdk5iTXZfU3JrWEEzSlE?oc=5)
- [Nie pijcie tej wody. Arsen, ołów i nikiel w wodach podziemnych w Bolesławiu - Radio Kraków](https://news.google.com/atom/articles/CBMizgFBVV95cUxON3hhdXRpNFVUdEpOY0pBckhiQUFXbmZCdDM1TXdfeU9kMnBxTXRHT25sNnBBYW15SkZHMHJIVF9fWHRuRV81RFRKY0o4Wm9rbnBkNFZKekNkTUVpdFpWdzY0bnZqNXRoVWtRY1pYTFFNdkNUcW1ieHB5dmNPSGJWTDJUVG1SSDJ2bWM4MFJjOGdtTmE2cnVQTzRhV3BvYm02V2lGcWMydkFXV1pWVFFjT0FLNHRzRHBWazNNTXdKai1zLWJ2eXBRNFQzazZoUQ?oc=5)
<!--README_FEED:END-->

## 💬 Cytat z szuflady

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝Work out your own salvation. Do not depend on others. — Buddha❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## Other stuff

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/twojstar/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
