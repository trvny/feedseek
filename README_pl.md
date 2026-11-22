<div align="center">

<img src="assets/banner-feedseek.svg" alt="Feedseek" width="960">

<img src="assets/icons/favicon-96x96.png" alt="Feedseek" width="72">

# Feedseek :satellite_antenna:

**Samoodświeżające się, ulepszane feedy RSS/Atom + JSON oraz dedykowane Model Feeds dla LLM-ów i agentów: zarówno tam, gdzie feedu brakuje, jak i tam, gdzie natywny da się zrobić lepiej.**

[![feeds](https://img.shields.io/badge/feeds-118-d6541a?style=flat-square&logo=rss&logoColor=white)](feeds.yaml) [![CI](https://img.shields.io/github/actions/workflow/status/trvny/feedseek/update-feeds.yml?label=CI&logo=githubactions&logoColor=white&style=flat-square)](https://github.com/trvny/feedseek/actions/workflows/update-feeds.yml) [![pages](https://img.shields.io/github/deployments/trvny/feedseek/github-pages?label=pages&logo=github&logoColor=white&style=flat-square)](https://rss.bartek.lol/) [![last commit](https://img.shields.io/github/last-commit/trvny/feedseek?color=d6541a&logo=git&logoColor=white&style=flat-square)](https://github.com/trvny/feedseek/commits/main) [![license](https://img.shields.io/github/license/trvny/feedseek?color=d6541a&logo=opensourceinitiative&logoColor=white&style=flat-square)](https://spdx.org/licenses/MIT)
<a href="https://deepwiki.com/trvny/feedseek"><picture><source srcset="https://img.shields.io/badge/DeepWiki-trvny%2Ffeedseek-blue.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAyCAYAAAAnWDnqAAAAAXNSR0IArs4c6QAAA05JREFUaEPtmUtyEzEQhtWTQyQLHNak2AB7ZnyXZMEjXMGeK/AIi+QuHrMnbChYY7MIh8g01fJoopFb0uhhEqqcbWTp06/uv1saEDv4O3n3dV60RfP947Mm9/SQc0ICFQgzfc4CYZoTPAswgSJCCUJUnAAoRHOAUOcATwbmVLWdGoH//PB8mnKqScAhsD0kYP3j/Yt5LPQe2KvcXmGvRHcDnpxfL2zOYJ1mFwrryWTz0advv1Ut4CJgf5uhDuDj5eUcAUoahrdY/56ebRWeraTjMt/00Sh3UDtjgHtQNHwcRGOC98BJEAEymycmYcWwOprTgcB6VZ5JK5TAJ+fXGLBm3FDAmn6oPPjR4rKCAoJCal2eAiQp2x0vxTPB3ALO2CRkwmDy5WohzBDwSEFKRwPbknEggCPB/imwrycgxX2NzoMCHhPkDwqYMr9tRcP5qNrMZHkVnOjRMWwLCcr8ohBVb1OMjxLwGCvjTikrsBOiA6fNyCrm8V1rP93iVPpwaE+gO0SsWmPiXB+jikdf6SizrT5qKasx5j8ABbHpFTx+vFXp9EnYQmLx02h1QTTrl6eDqxLnGjporxl3NL3agEvXdT0WmEost648sQOYAeJS9Q7bfUVoMGnjo4AZdUMQku50McDcMWcBPvr0SzbTAFDfvJqwLzgxwATnCgnp4wDl6Aa+Ax283gghmj+vj7feE2KBBRMW3FzOpLOADl0Isb5587h/U4gGvkt5v60Z1VLG8BhYjbzRwyQZemwAd6cCR5/XFWLYZRIMpX39AR0tjaGGiGzLVyhse5C9RKC6ai42ppWPKiBagOvaYk8lO7DajerabOZP46Lby5wKjw1HCRx7p9sVMOWGzb/vA1hwiWc6jm3MvQDTogQkiqIhJV0nBQBTU+3okKCFDy9WwferkHjtxib7t3xIUQtHxnIwtx4mpg26/HfwVNVDb4oI9RHmx5WGelRVlrtiw43zboCLaxv46AZeB3IlTkwouebTr1y2NjSpHz68WNFjHvupy3q8TFn3Hos2IAk4Ju5dCo8B3wP7VPr/FGaKiG+T+v+TQqIrOqMTL1VdWV1DdmcbO8KXBz6esmYWYKPwDL5b5FA1a0hwapHiom0r/cKaoqr+27/XcrS5UwSMbQAAAABJRU5ErkJggg==" type="image/svg+xml"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></picture></a>  
[![Web reader](https://img.shields.io/badge/Web%20reader-open-222222?style=flat-square&logo=githubpages&logoColor=white)](https://rss.bartek.lol/reader/)  
[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/) [![uv](https://img.shields.io/badge/uv-DE5FE9?style=flat-square&logo=uv&logoColor=white)](https://docs.astral.sh/uv/)

**Polski** · [English](README.md) · [简体中文](README_zh.md)  

[**:satellite_antenna: Feedy**](https://rss.bartek.lol/) · [**:book: Czytnik**](https://rss.bartek.lol/reader/) · [**:card_file_box: Rejestr**](feeds.yaml) · [**:robot: LLMs**](docs/model-feeds.md) · [**:compass: Technicznie**](docs/)  

</div>

Feedseek wyszukuje albo buduje feedy, normalizuje wpisy, usuwa duplikaty i publikuje wynik przez GitHub Pages. Harmonogram odświeża źródła co dwie godziny, a awaria jednego serwisu nie powinna wywracać pozostałych.

Feedseek nie jest tylko generatorem dla stron, które nie mają feedu. Natywny RSS/Atom jest wartościowym źródłem wejściowym, ale nie nietykalnym produktem końcowym: jeśli materiał źródłowy na to pozwala, Feedseek normalizuje i wzbogaca go do stabilniejszej, pełniejszej, bogatszej semantycznie i bardziej interoperacyjnej postaci, publikując obok XML jeden plik `feed_<name>.json`: zwarty Model Feed z oczyszczonym tekstem, kanonicznymi linkami, datami i jawnym oznaczeniem, czy wpis zawiera treść, streszczenie czy tylko tytuł. Model Feed zastąpił dawną parę JSON Feed 1.1 i `.model.json`; służy bezpośrednio modelom i agentom.

Celem jest wykorzystywanie możliwości RSS, Atom i JSON Feed tak dobrze, jak pozwalają dane źródłowe: trwałe identyfikatory, kanoniczne linki, prawdziwe daty publikacji i aktualizacji, użyteczne metadane, pochodzenie, kategorie oraz media. Scrapery i adaptery API uzupełniają braki natywnych źródeł. Nieudane albo puste pobranie nie zastępuje ostatniego poprawnego feedu.

## Feedy [![XML](https://img.shields.io/badge/XML-005FAD?logo=xml&logoColor=fff&style=plastic)](https://www.w3.org/XML/)

<!-- registry-count: feeds.yaml (118 źródeł) -->
Pełna tabela źródeł i bezpośrednich plików feedów znajduje się w [angielskim README](README.md#feeds-), a wygodniejszy interfejs do przeglądania i subskrypcji na [stronie Feedseek](https://rss.bartek.lol/).

- **Rejestr:** [`feeds.yaml`](feeds.yaml)
- **Wygenerowane XML/JSON/Model Feed:** [`feeds/`](feeds/)
- **Indeks źródeł:** [`docs/sources.md`](docs/sources.md)
- **Notatki o poszczególnych feedach:** [`docs/feeds.md`](docs/feeds.md)

## Dokumentacja

- [Pipeline, enrichment, użycie lokalne i układ repozytorium](docs/architecture.md)
- [Źródła i kompromisy poszczególnych feedów](docs/feeds.md)
- [Działanie i utrzymanie cache](docs/cache.md)
- [Wygenerowany indeks źródeł](docs/sources.md)
- [Dostęp dla LLM i agentów: zdalny serwer MCP, WebMCP, llms.txt, JSON Schema Model Feed](docs/agents.md)

Androidowy czytnik/player tych feedów to osobny projekt: **[travnie/kanarek](https://github.com/travnie/kanarek)**.

## [Licencja](LICENSE)

[![Licencja](https://www.shieldcn.dev/github/license/trvny/feedseek.svg?variant=branded&size=xm&mode=light&theme=neutral&font=jetbrains-mono)](https://spdx.org/licenses/MIT)  [THIRD_PARTY_NOTICES](docs/THIRD_PARTY_NOTICES.md)

## 📰 Mininewsy

<!--README_FEED:START-->
- [Like A Complete \(Known\) Unknown? A Brief History of Nuclear Weaponization](https://carnegieendowment.org/research/2026/11/a-brief-history-of-nuclear-weaponization)
- [Cyber Statecraft and the Middle Ground](https://carnegieendowment.org/research/2026/11/cyber-statecraft-and-the-middle-ground)
- [Murder at Mount Hood | Post Mortem](https://www.cbsnews.com/video/112126-48-hours-post-mortem-episode-5/)
- [Zostań policjantem! Promocja zawodu podczas Powiatowego Dnia Przedsiębiorczości - Przegląd Olkuski](https://news.google.com/atom/articles/CBMirgFBVV95cUxQU2hUWGVXeWQtTDdoN2hERXlkYmZrUnBLZ1UxcTRqdTJVSW1fV0FfTDcyN1V1dEs5VGlPN0R1QjZFV2g5QUgxTnVMaHFLQThkS2ZNbkI2ODFnYk04LVdCVXhGazJBUUxRLVR6aEpJek1yMERIR2tyZmdkeVItU3djZG1YTWRFNjFwUThiQ0VyNHhQaWRReVd6WnBGU1NQT0xRZDdHMlFyOUhxYzBjUFE?oc=5)
- [Jest decyzja dla drugiego etapu drogi do Jaworzna - Przegląd Olkuski](https://news.google.com/atom/articles/CBMihAFBVV95cUxON1FrUnhmRU95cGl1ZDk2SFp4SFlzSVA3UzRrQ09vSEFldEdUVTFLUDRzN19TbmhVYk4yR1ZFRkFOYlY1b0lKbkV3aDBGZmRBVGxoR0JoWUhBZmI3TUVudk0tQzdpdGxlM2o5TEtJS0lxMEpkdTRDc05rMm1TSDk1bWdrVFQ?oc=5)
- [Jets urged to get 1st-round pick involved on offense to help end TD drought](https://www.sportingnews.com/us/nfl/new-york-jets/news/jets-urged-get-1st-round-pick-involved-help-end-td-drought/a00fb6698aa10c5b3e3f2767)
<!--README_FEED:END-->

## 💬 Cytat z szuflady

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝In 2012, the founder of McAfee Antivirus, John McAfee was asked if he personally uses McAfee anti-virus, he replied by saying “I take it off,” and that “It’s too annoying.”❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## Other stuff

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/travnie/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
