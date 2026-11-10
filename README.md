<div align="center">

<img src="assets/banner-feedseek.svg" alt="Feedseek" width="960">

<img src="assets/icons/favicon-96x96.png" alt="Feedseek" width="96">
</div>

> [!WARNING]
> ⚠️ Feeds migrated from repo to pages `https://trvny.github.io/feedseek/{feed}.xml`

<div align="center">

# Feedseek :satellite:

**Self-updating, enhanced RSS/Atom feeds with a single LLM-friendly JSON Model Feed for each source. Built both where feeds are missing and where native feeds can be made better.**

[![feeds](https://img.shields.io/badge/feeds-117-d6541a?style=flat-square&logo=rss&logoColor=white)](feeds.yaml) [![CI](https://img.shields.io/github/actions/workflow/status/trvny/feedseek/update-feeds.yml?label=CI&logo=githubactions&logoColor=white&style=flat-square)](https://github.com/trvny/feedseek/actions/workflows/update-feeds.yml) [![pages](https://img.shields.io/github/deployments/trvny/feedseek/github-pages?label=pages&logo=github&logoColor=white&style=flat-square)](https://trvny.github.io/feedseek/) [![last commit](https://img.shields.io/github/last-commit/trvny/feedseek?color=d6541a&logo=git&logoColor=white&style=flat-square)](https://github.com/trvny/feedseek/commits/main) [![license](https://img.shields.io/github/license/trvny/feedseek?color=d6541a&logo=opensourceinitiative&logoColor=white&style=flat-square)](https://spdx.org/licenses/MIT)  
<a href="https://deepwiki.com/trvny/feedseek"><img src="https://img.shields.io/badge/DeepWiki-feedseek-blue.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAyCAYAAAAnWDnqAAAAAXNSR0IArs4c6QAAA05JREFUaEPtmUtyEzEQhtWTQyQLHNak2AB7ZnyXZMEjXMGeK/AIi+QuHrMnbChYY7MIh8g01fJoopFb0uhhEqqcbWTp06/uv1saEDv4O3n3dV60RfP947Mm9/SQc0ICFQgzfc4CYZoTPAswgSJCCUJUnAAoRHOAUOcATwbmVLWdGoH//PB8mnKqScAhsD0kYP3j/Yt5LPQe2KvcXmGvRHcDnpxfL2zOYJ1mFwrryWTz0advv1Ut4CJgf5uhDuDj5eUcAUoahrdY/56ebRWeraTjMt/00Sh3UDtjgHtQNHwcRGOC98BJEAEymycmYcWwOprTgcB6VZ5JK5TAJ+fXGLBm3FDAmn6oPPjR4rKCAoJCal2eAiQp2x0vxTPB3ALO2CRkwmDy5WohzBDwSEFKRwPbknEggCPB/imwrycgxX2NzoMCHhPkDwqYMr9tRcP5qNrMZHkVnOjRMWwLCcr8ohBVb1OMjxLwGCvjTikrsBOiA6fNyCrm8V1rP93iVPpwaE+gO0SsWmPiXB+jikdf6SizrT5qKasx5j8ABbHpFTx+vFXp9EnYQmLx02h1QTTrl6eDqxLnGjporxl3NL3agEvXdT0WmEost648sQOYAeJS9Q7bfUVoMGnjo4AZdUMQku50McDcMWcBPvr0SzbTAFDfvJqwLzgxwATnCgnp4wDl6Aa+Ax283gghmj+vj7feE2KBBRMW3FzOpLOADl0Isb5587h/U4gGvkt5v60Z1VLG8BhYjbzRwyQZemwAd6cCR5/XFWLYZRIMpX39AR0tjaGGiGzLVyhse5C9RKC6ai42ppWPKiBagOvaYk8lO7DajerabOZP46Lby5wKjw1HCRx7p9sVMOWGzb/vA1hwiWc6jm3MvQDTogQkiqIhJV0nBQBTU+3okKCFDy9WwferkHjtxib7t3xIUQtHxnIwtx4mpg26/HfwVNVDb4oI9RHmx5WGelRVlrtiw43zboCLaxv46AZeB3IlTkwouebTr1y2NjSpHz68WNFjHvupy3q8TFn3Hos2IAk4Ju5dCo8B3wP7VPr/FGaKiG+T+v+TQqIrOqMTL1VdWV1DdmcbO8KXBz6esmYWYKPwDL5b5FA1a0hwapHiom0r/cKaoqr+27/XcrS5UwSMbQAAAABJRU5ErkJggg==" alt="DeepWiki"></a>  
[![Web reader](https://img.shields.io/badge/-Reader-222222?style=flat-square&logo=githubpages&logoColor=white)](https://trvny.github.io/feedseek/reader/)  
[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/) [![uv](https://img.shields.io/badge/uv-DE5FE9?style=flat-square&logo=uv&logoColor=white)](https://docs.astral.sh/uv/)

![CodeRabbit](https://img.shields.io/coderabbit/prs/github/trvny/feedseek?utm_source=oss&utm_medium=github&utm_campaign=trvny%2Ffeedseek&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews) <a href="https://app.deepsource.com/gh/trvny/feedseek/" target="_blank"><img alt="DeepSource" title="DeepSource" src="https://app.deepsource.com/gh/trvny/feedseek.svg/?label=active+issues&show_trend=false&token=m5erK7VaWqc3WCLPHGbP4D4N"/></a> <a href="https://app.codacy.com/gh/trvny/feedseek/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade"><img src="https://app.codacy.com/project/badge/Grade/8dcad571fe644ec58f37b28283cf5f0b"/></a>

[Polski](README_pl.md) · **English** · [简体中文](README_zh.md)  

[**:satellite: Feeds**](https://trvny.github.io/feedseek/) · [**:book: Reader**](https://trvny.github.io/feedseek/reader/) · [**:card_file_box: Registry**](feeds.yaml) · [**:robot: LLMs**](docs/model-feeds.md) · [**:compass: Internals**](docs/)

</div>

Feedseek discovers or builds feeds, normalizes entries, deduplicates them and publishes the generated output through GitHub Pages. The scheduled workflow refreshes sources every two hours, while source failures are isolated so one broken site does not sink the rest.

Feedseek is not only a generator for sites that lack feeds. Native RSS/Atom is a valuable upstream input, not an untouchable final product: when the source material allows it, Feedseek normalizes and enriches it into a more stable, complete, expressive and interoperable feed, with a single compact LLM-friendly JSON Model Feed alongside the XML. Its `feed_<name>.json` sibling provides normalized plaintext, explicit text-kind metadata, canonical links and timestamps for LLM and agent consumption. It replaces the previous JSON Feed 1.1 and `.model.json` pair.

The goal is to use the useful semantics of RSS, Atom and JSON Feed as fully as the source allows: durable identity, canonical links, truthful publication/update dates, useful metadata, provenance, categories and media. Scraping and API adapters fill gaps that native sources leave behind. A failed or empty fetch does not replace the last known-good feed.

Inspired by [Olshansk/rss-feeds](https://github.com/Olshansk/rss-feeds) & [rss-bridge/rss-bridge](https://github.com/rss-bridge/rss-bridge).

## Feeds [![XML](https://img.shields.io/badge/XML-005FAD?logo=xml&logoColor=fff&style=plastic)](https://www.w3.org/XML/)

| Source ![rss](https://www.mozilla.org/media/img/trademarks/feed-icon-28x28.e077f1f611f0.png) | Feed <img src="assets/icons/rss-file-color-green.png" width="24" align="top"> |
| ------ | ---- |
| <img src="https://www.google.com/s2/favicons?domain=jbzd.com.pl&sz=32" width="16" height="16" align="absmiddle" alt=""> [Jbzd.com.pl](https://jbzd.com.pl/) | [jbzd.xml](https://trvny.github.io/feedseek/jbzd.xml) |
| <img src="https://www.google.com/s2/favicons?domain=wykop.pl&sz=32" width="16" height="16" align="absmiddle" alt=""> [Wykop](https://wykop.pl/) | [wykop.xml](https://trvny.github.io/feedseek/wykop.xml) |
| <img src="https://www.google.com/s2/favicons?domain=9gag.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [9GAG](https://9gag.com/) | [9gag.xml](https://trvny.github.io/feedseek/9gag.xml) |
| <img src="https://www.google.com/s2/favicons?domain=4chan.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [4chan](https://www.4chan.org/) | [4chan.xml](https://trvny.github.io/feedseek/4chan.xml) |
| <img src="https://www.google.com/s2/favicons?domain=join-lemmy.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [Lemmy](https://join-lemmy.org/) | [lemmy.xml](https://trvny.github.io/feedseek/lemmy.xml) |
| <img src="https://www.google.com/s2/favicons?domain=cheezburger.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Cheezburger Network](https://www.cheezburger.com/) | [cheezburger.xml](https://trvny.github.io/feedseek/cheezburger.xml) |
| <img src="https://www.google.com/s2/favicons?domain=memedroid.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Memedroid](https://www.memedroid.com/) | [memedroid.xml](https://trvny.github.io/feedseek/memedroid.xml) |
| <img src="https://www.google.com/s2/favicons?domain=memy.pl&sz=32" width="16" height="16" align="absmiddle" alt=""> [Memy (Memy.pl · Jeja.pl · Kwejk.pl)](https://memy.pl/) | [memy.xml](https://trvny.github.io/feedseek/memy.xml) |
| <img src="https://www.google.com/s2/favicons?domain=beatport.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Beatport Top 100](https://www.beatport.com/top-100) | [beatport_top100.xml](https://trvny.github.io/feedseek/beatport_top100.xml) |
| <img src="https://icons.duckduckgo.com/ip3/ra.co.ico" width="16" height="16" align="absmiddle" alt=""> [RA (Resident Advisor)](https://ra.co/magazine) | [ra.xml](https://trvny.github.io/feedseek/ra.xml) |
| <img src="https://www.google.com/s2/favicons?domain=audio.com.pl&sz=32" width="16" height="16" align="absmiddle" alt=""> [Audio.com.pl](https://audio.com.pl/) | [audio.xml](https://trvny.github.io/feedseek/audio.xml) |
| <img src="https://www.google.com/s2/favicons?domain=audacityteam.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [Audacity®](https://www.audacityteam.org/blog/) | [audacity.xml](https://trvny.github.io/feedseek/audacity.xml) |
| <img src="https://www.google.com/s2/favicons?domain=spotify.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Spotify (newsroom + developers)](https://newsroom.spotify.com/) | [spotify.xml](https://trvny.github.io/feedseek/spotify.xml) |
| <img src="https://www.google.com/s2/favicons?domain=netflix.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Netflix](https://about.netflix.com/) | [netflix.xml](https://trvny.github.io/feedseek/netflix.xml) |
| <img src="https://www.google.com/s2/favicons?domain=foobar2000.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [foobar2000](https://www.foobar2000.org/news) | [foobar2000.xml](https://trvny.github.io/feedseek/foobar2000.xml) |
| <img src="https://icons.duckduckgo.com/ip3/viewbits.com.ico" width="16" height="16" align="absmiddle" alt=""> [Daily Digest](https://api.viewbits.com/) | [daily_digest.xml](https://trvny.github.io/feedseek/daily_digest.xml) |
| <img src="https://www.google.com/s2/favicons?domain=gist.github.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Daily Quote](https://gist.github.com/trvny/167d2271e3cf7d21e118aa7d906a7d2c) | [daily_quote.xml](https://trvny.github.io/feedseek/daily_quote.xml) |
| <img src="https://www.google.com/s2/favicons?domain=theysaidso.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Quotes, Sayings & Jokes of the Day](https://theysaidso.com/) | [theysaidso.xml](https://trvny.github.io/feedseek/theysaidso.xml) |
| <img src="https://www.google.com/s2/favicons?domain=dictionary.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Word of the Day (Dictionary.com,MW,AWAD,TFD)](https://www.dictionary.com/e/word-of-the-day/) | [wotd.xml](https://trvny.github.io/feedseek/wotd.xml) |
| <img src="https://www.google.com/s2/favicons?domain=unsplash.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Unsplash (log + wallpapers)](https://unsplash.com/blog/) | [unsplash.xml](https://trvny.github.io/feedseek/unsplash.xml) |
| <img src="https://www.google.com/s2/favicons?domain=gov.pl&sz=32" width="16" height="16" align="absmiddle" alt=""> [Gov.pl](https://www.gov.pl/) | [govpl_news.xml](https://trvny.github.io/feedseek/govpl_news.xml) |
| <img src="https://www.google.com/s2/favicons?domain=usa.gov&sz=32" width="16" height="16" align="absmiddle" alt=""> [US.gov](https://www.usa.gov/) | [usgov.xml](https://trvny.github.io/feedseek/usgov.xml) |
| <img src="https://www.google.com/s2/favicons?domain=open-meteo.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Open-Meteo](https://open-meteo.com/) | [open_meteo.xml](https://trvny.github.io/feedseek/open_meteo.xml) |
| <img src="https://www.google.com/s2/favicons?domain=openweathermap.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [OpenWeather](https://openweathermap.org/city/3093133) | [openweather.xml](https://trvny.github.io/feedseek/openweather.xml) |
| <img src="https://www.google.com/s2/favicons?domain=visualcrossing.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Visual Crossing](https://www.visualcrossing.com/) | [visualcrossing.xml](https://trvny.github.io/feedseek/visualcrossing.xml) |
| <img src="https://www.google.com/s2/favicons?domain=imgw.pl&sz=32" width="16" height="16" align="absmiddle" alt=""> [IMGW](https://danepubliczne.imgw.pl/) | [imgw.xml](https://trvny.github.io/feedseek/imgw.xml) |
| <img src="https://www.google.com/s2/favicons?domain=weather.trfny.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Weather — Kościelec](https://weather.trfny.com/) | [weather.xml](https://trvny.github.io/feedseek/weather.xml) |
| <img src="https://www.google.com/s2/favicons?domain=accuweather.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [AccuWeather News](https://www.accuweather.com/en/weather-news) | [accuweather.xml](https://trvny.github.io/feedseek/accuweather.xml) |
| <img src="https://www.google.com/s2/favicons?domain=xweather.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Xweather Log](https://www.xweather.com/blog) | [xweather_log.xml](https://trvny.github.io/feedseek/xweather_log.xml) |
| <img src="https://www.google.com/s2/favicons?domain=visualcrossing.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Visual Crossing Blog](https://www.visualcrossing.com/resources/) | [visualcrossing_blog.xml](https://trvny.github.io/feedseek/visualcrossing_blog.xml) |
| <img src="https://www.google.com/s2/favicons?domain=reuters.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Reuters](https://www.reuters.com/) | [reuters.xml](https://trvny.github.io/feedseek/reuters.xml) |
| <img src="https://www.google.com/s2/favicons?domain=newsify.today&sz=32" width="16" height="16" align="absmiddle" alt=""> [Newsify](https://newsify.today/polish/PL) | [newsify.xml](https://trvny.github.io/feedseek/newsify.xml) |
| <img src="https://www.google.com/s2/favicons?domain=wsj.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [WSJ](https://www.wsj.com/news/latest-headlines?mod=wsjfooter) | [wsj.xml](https://trvny.github.io/feedseek/wsj.xml) |
| <img src="https://www.google.com/s2/favicons?domain=euronews.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Euronews](https://www.euronews.com/) | [euronews.xml](https://trvny.github.io/feedseek/euronews.xml) |
| <img src="https://www.google.com/s2/favicons?domain=europa.eu&sz=32" width="16" height="16" align="absmiddle" alt=""> [Europa (UE)](https://european-union.europa.eu/) | [europa.xml](https://trvny.github.io/feedseek/europa.xml) |
| <img src="https://www.google.com/s2/favicons?domain=understandingwar.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [Geopolitics (ISW;RUSI;CSIS;Carnegie)](https://understandingwar.org/research/) | [geopolitics.xml](https://trvny.github.io/feedseek/geopolitics.xml) |
| <img src="https://www.google.com/s2/favicons?domain=pap.pl&sz=32" width="16" height="16" align="absmiddle" alt=""> [PAP](https://www.pap.pl/) | [pap.xml](https://trvny.github.io/feedseek/pap.xml) |
| <img src="https://www.google.com/s2/favicons?domain=reddit.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [MultiReddit[OFF]](https://old.reddit.com/) | `multireddit.xml` — disabled, not published |
| <img src="https://www.google.com/s2/favicons?domain=spidersweb.pl&sz=32" width="16" height="16" align="absmiddle" alt=""> [Spider's Web](https://spidersweb.pl/) | [spidersweb.xml](https://trvny.github.io/feedseek/spidersweb.xml) |
| <img src="https://www.google.com/s2/favicons?domain=wikipedia.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [Wikipedia (PL)](https://pl.wikipedia.org/) | [wikipedia_pl.xml](https://trvny.github.io/feedseek/wikipedia_pl.xml) |
| <img src="https://www.google.com/s2/favicons?domain=baike.baidu.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Baidu Baike 热搜词条](https://baike.baidu.com/) | [baidubaike.xml](https://trvny.github.io/feedseek/baidubaike.xml) |
| <img src="https://www.google.com/s2/favicons?domain=tvp.pl&sz=32" width="16" height="16" align="absmiddle" alt=""> [TVP](https://www.tvp.pl/) | [tvp.xml](https://trvny.github.io/feedseek/tvp.xml) |
| <img src="https://icons.duckduckgo.com/ip3/trojka.polskieradio.pl.ico" width="16" height="16" align="absmiddle" alt=""> [Polskie Radio – Trójka](https://trojka.polskieradio.pl/) | [trojka.xml](https://trvny.github.io/feedseek/trojka.xml) |
| <img src="https://www.google.com/s2/favicons?domain=polskieradio.pl&sz=32" width="16" height="16" align="absmiddle" alt=""> [Polskie Radio – Czwórka](https://www.polskieradio.pl/10,czworka) | [czworka.xml](https://trvny.github.io/feedseek/czworka.xml) |
| <img src="https://www.google.com/s2/favicons?domain=olx.pl&sz=32" width="16" height="16" align="absmiddle" alt=""> [OLX Group (OLX/OTOMOTO/Otodom)](https://www.olx.pl/) | [olx.xml](https://trvny.github.io/feedseek/olx.xml) |
| <img src="https://www.google.com/s2/favicons?domain=toyota.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Toyota Global](https://pressroom.toyota.com/) | [toyota_global.xml](https://trvny.github.io/feedseek/toyota_global.xml) |
| <img src="https://www.google.com/s2/favicons?domain=lexus.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Lexus Newsroom](https://pressroom.lexus.com/) | [lexus_newsroom.xml](https://trvny.github.io/feedseek/lexus_newsroom.xml) |
| <img src="https://www.google.com/s2/favicons?domain=foundryco.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Foundry (CSO,PCWorld)](https://foundryco.com/sitemap/) | [foundry.xml](https://trvny.github.io/feedseek/foundry.xml) |
| <img src="https://www.google.com/s2/favicons?domain=lenovo.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Lenovo StoryHub](https://news.lenovo.com/) | [lenovo.xml](https://trvny.github.io/feedseek/lenovo.xml) |
| <img src="https://www.google.com/s2/favicons?domain=nvidia.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [NVIDIA (newsroom, blogs + GeForce drivers)](https://nvidianews.nvidia.com/) | [nvidia.xml](https://trvny.github.io/feedseek/nvidia.xml) |
| <img src="https://www.google.com/s2/favicons?domain=dji.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [DJI](https://www.dji.com/pl/mobile/media-center/announcements) | [dji.xml](https://trvny.github.io/feedseek/dji.xml) |
| <img src="https://www.google.com/s2/favicons?domain=hp.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [HP Newsroom](https://www.hp.com/us-en/newsroom.html) | [hp.xml](https://trvny.github.io/feedseek/hp.xml) |
| <img src="https://www.google.com/s2/favicons?domain=mi.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Xiaomi Newsroom](https://www.mi.com/global/discover/newsroom) | [xiaomi.xml](https://trvny.github.io/feedseek/xiaomi.xml) |
| <img src="https://www.google.com/s2/favicons?domain=samsung.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Samsung Newsroom (global/PL)](https://news.samsung.com/global/) | [samsung.xml](https://trvny.github.io/feedseek/samsung.xml) |
| <img src="https://www.google.com/s2/favicons?domain=sony.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Sony Corp](https://www.sony.com/en/SonyInfo/News/Press/) | [sony.xml](https://trvny.github.io/feedseek/sony.xml) |
| <img src="https://www.google.com/s2/favicons?domain=apple.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Apple Newsroom](https://www.apple.com/pl/newsroom/) | [apple.xml](https://trvny.github.io/feedseek/apple.xml) |
| <img src="https://www.google.com/s2/favicons?domain=microsoft.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Microsoft Blogs](https://blogs.microsoft.com/) | [microsoft.xml](https://trvny.github.io/feedseek/microsoft.xml) |
| <img src="https://www.google.com/s2/favicons?domain=redhat.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Red Hat Enterprise](https://www.redhat.com/en/) | [redhat.xml](https://trvny.github.io/feedseek/redhat.xml) |
| <img src="https://www.google.com/s2/favicons?domain=ubuntu.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Ubuntu](https://ubuntu.com/blog) | [ubuntu.xml](https://trvny.github.io/feedseek/ubuntu.xml) |
| <img src="https://www.google.com/s2/favicons?domain=oracle.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Oracle](https://blogs.oracle.com/) | [oracle.xml](https://trvny.github.io/feedseek/oracle.xml) |
| <img src="https://www.google.com/s2/favicons?domain=microsoft.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Microsoft Updates (Windows/Office/Copilot)](https://support.microsoft.com/en-us/windows) | [microsoft_updates.xml](https://trvny.github.io/feedseek/microsoft_updates.xml) |
| <img src="https://www.google.com/s2/favicons?domain=blog.google&sz=32" width="16" height="16" align="absmiddle" alt=""> [Google (combined)](https://blog.google/) | [google.xml](https://trvny.github.io/feedseek/google.xml) |
| <img src="https://www.google.com/s2/favicons?domain=blog.youtube&sz=32" width="16" height="16" align="absmiddle" alt=""> [YouTube Blog](https://blog.youtube/) | [youtube.xml](https://trvny.github.io/feedseek/youtube.xml) |
| <img src="https://www.google.com/s2/favicons?domain=tiktok.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [TikTok](https://newsroom.tiktok.com/) | [tiktok.xml](https://trvny.github.io/feedseek/tiktok.xml) |
| <img src="https://www.google.com/s2/favicons?domain=mozilla.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [Mozilla](https://blog.mozilla.org/) | [mozilla.xml](https://trvny.github.io/feedseek/mozilla.xml) |
| <img src="https://www.google.com/s2/favicons?domain=meta.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Meta Newsroom](https://about.fb.com/news/) | [meta_newsroom.xml](https://trvny.github.io/feedseek/meta_newsroom.xml) |
| <img src="https://www.google.com/s2/favicons?domain=thinkingmachines.ai&sz=32" width="16" height="16" align="absmiddle" alt=""> [AI-bridge (combined AI sources)](https://thinkingmachines.ai/blog/) | [aibridge.xml](https://trvny.github.io/feedseek/aibridge.xml) |
| <img src="https://www.google.com/s2/favicons?domain=anthropic.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Anthropic](https://www.anthropic.com/) | [anthropic.xml](https://trvny.github.io/feedseek/anthropic.xml) |
| <img src="https://www.google.com/s2/favicons?domain=claude.ai&sz=32" width="16" height="16" align="absmiddle" alt=""> [Claude](https://claude.com/blog) | [claude.xml](https://trvny.github.io/feedseek/claude.xml) |
| <img src="https://www.google.com/s2/favicons?domain=openai.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [OpenAI](https://openai.com/news/) | [openai.xml](https://trvny.github.io/feedseek/openai.xml) |
| <img src="https://www.google.com/s2/favicons?domain=x.ai&sz=32" width="16" height="16" align="absmiddle" alt=""> [xAI](https://x.ai/news) | [xai.xml](https://trvny.github.io/feedseek/xai.xml) |
| <img src="https://www.google.com/s2/favicons?domain=alibabacloud.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Alibaba](https://www.alibabacloud.com/en/press-room/press-release) | [alibaba.xml](https://trvny.github.io/feedseek/alibaba.xml) |
| <img src="https://www.google.com/s2/favicons?domain=huggingface.co&sz=32" width="16" height="16" align="absmiddle" alt=""> [Hugging Face](https://huggingface.co/) | [huggingface.xml](https://trvny.github.io/feedseek/huggingface.xml) |
| <img src="https://www.google.com/s2/favicons?domain=skillsllm.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [LLM & MCP / Skills ecosystem](https://skillsllm.com/) | [skillsllm.xml](https://trvny.github.io/feedseek/skillsllm.xml) |
| <img src="https://www.google.com/s2/favicons?domain=rust-lang.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [Development (Rust, Django, React Native & more)](https://blog.rust-lang.org/) | [development.xml](https://trvny.github.io/feedseek/development.xml) |
| <img src="https://www.google.com/s2/favicons?domain=moltbook.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Molt](https://www.moltbook.com/) | [molt.xml](https://trvny.github.io/feedseek/molt.xml) |
| <img src="https://www.google.com/s2/favicons?domain=uber.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Uber Newsroom](https://www.uber.com/us/en/newsroom/) | [uber.xml](https://trvny.github.io/feedseek/uber.xml) |
| <img src="https://www.google.com/s2/favicons?domain=tencent.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Tencent](https://www.tencent.com/newsroom/) | [tencent.xml](https://trvny.github.io/feedseek/tencent.xml) |
| <img src="https://www.google.com/s2/favicons?domain=aws.amazon.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [AWS](https://aws.amazon.com/blogs/) | [aws.xml](https://trvny.github.io/feedseek/aws.xml) |
| <img src="https://www.google.com/s2/favicons?domain=onlyoffice.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [OPENOFFICE](https://www.onlyoffice.com/blog) | [openoffice.xml](https://trvny.github.io/feedseek/openoffice.xml) |
| <img src="https://www.google.com/s2/favicons?domain=hashicorp.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [SaaS vendors](https://www.hashicorp.com/blog) | [saas.xml](https://trvny.github.io/feedseek/saas.xml) |
| <img src="https://www.google.com/s2/favicons?domain=palantir.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Palantir](https://www.palantir.com/newsroom/) | [palantir.xml](https://trvny.github.io/feedseek/palantir.xml) |
| <img src="https://www.google.com/s2/favicons?domain=cloudflare.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Cloudflare (log/community/research)](https://blog.cloudflare.com/) | [cloudflare.xml](https://trvny.github.io/feedseek/cloudflare.xml) |
| <img src="https://www.google.com/s2/favicons?domain=docker.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Docker](https://www.docker.com/blog/) | [docker.xml](https://trvny.github.io/feedseek/docker.xml) |
| <img src="https://www.google.com/s2/favicons?domain=gitlab.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [GitLab](https://about.gitlab.com/) | [gitlab.xml](https://trvny.github.io/feedseek/gitlab.xml) |
| <img src="https://www.google.com/s2/favicons?domain=github.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [GitHub (tooling,trending)](https://github.blog/) | [github.xml](https://trvny.github.io/feedseek/github.xml) |
| <img src="https://www.google.com/s2/favicons?domain=github.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [trvny + travnie · GitHub milestones](https://github.com/trvny) | [github_personal.xml](https://trvny.github.io/feedseek/github_personal.xml) |
| <img src="https://www.google.com/s2/favicons?domain=canva.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Canva](https://www.canva.com/newsroom/news/) | [canva.xml](https://trvny.github.io/feedseek/canva.xml) |
| <img src="https://www.google.com/s2/favicons?domain=figma.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Figma](https://www.figma.com/newsroom/?lang=pl-pl) | [figma.xml](https://trvny.github.io/feedseek/figma.xml) |
| <img src="https://www.google.com/s2/favicons?domain=paint.net&sz=32" width="16" height="16" align="absmiddle" alt=""> [Paint.NET](https://blog.paint.net/) | [paintnet.xml](https://trvny.github.io/feedseek/paintnet.xml) |
| <img src="https://www.google.com/s2/favicons?domain=greasespot.net&sz=32" width="16" height="16" align="absmiddle" alt=""> [UserScripts (Violentmonkey/Tampermonkey/Grease/Sleazy)](https://www.greasespot.net/) | [userscripts.xml](https://trvny.github.io/feedseek/userscripts.xml) |
| <img src="https://www.google.com/s2/favicons?domain=nexusmods.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Nexus Mods News](https://www.nexusmods.com/news) | [nexusmods_news.xml](https://trvny.github.io/feedseek/nexusmods_news.xml) |
| <img src="https://www.google.com/s2/favicons?domain=bethesda.net&sz=32" width="16" height="16" align="absmiddle" alt=""> [Bethesda](https://bethesda.net/pl-PL/news) | [bethesda.xml](https://trvny.github.io/feedseek/bethesda.xml) |
| <img src="https://www.google.com/s2/favicons?domain=ea.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Electronic Arts](https://www.ea.com/pl-pl/news) | [ea.xml](https://trvny.github.io/feedseek/ea.xml) |
| <img src="https://www.google.com/s2/favicons?domain=steampowered.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Steam](https://store.steampowered.com/news/) | [steam.xml](https://trvny.github.io/feedseek/steam.xml) |
| <img src="https://www.google.com/s2/favicons?domain=gog.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [GOG pressroom](https://www.gog.com/blog) | [gog.xml](https://trvny.github.io/feedseek/gog.xml) |
| <img src="https://www.google.com/s2/favicons?domain=nasa.gov&sz=32" width="16" height="16" align="absmiddle" alt=""> [NASA](https://www.nasa.gov/) | [nasa.xml](https://trvny.github.io/feedseek/nasa.xml) |
| <img src="https://www.google.com/s2/favicons?domain=esa.int&sz=32" width="16" height="16" align="absmiddle" alt=""> [ESA](https://www.esa.int/) | [esa.xml](https://trvny.github.io/feedseek/esa.xml) |
| <img src="https://www.google.com/s2/favicons?domain=pekao.com.pl&sz=32" width="16" height="16" align="absmiddle" alt=""> [Bank Pekao SA](https://www.pekao.com.pl/) | [pekao.xml](https://trvny.github.io/feedseek/pekao.xml) |
| <img src="https://www.google.com/s2/favicons?domain=creativecommons.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [Open Sources (CC/OSI/SPDX/OGC/RFC/IETF)](https://creativecommons.org/blog/) | [opensource.xml](https://trvny.github.io/feedseek/opensource.xml) |
| <img src="https://www.google.com/s2/favicons?domain=hackerone.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [HackerOne](https://www.hackerone.com/blog) | [hackerone.xml](https://trvny.github.io/feedseek/hackerone.xml) |
| <img src="https://www.google.com/s2/favicons?domain=python.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [Python (combined ecosystem)](https://www.python.org/) | [python.xml](https://trvny.github.io/feedseek/python.xml) |
| <img src="https://www.google.com/s2/favicons?domain=nodejs.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [JS \| Node (ecosystem)](https://nodejs.org/) | [js_node.xml](https://trvny.github.io/feedseek/js_node.xml) |
| <img src="https://www.google.com/s2/favicons?domain=arxiv.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [arXiv (+LessWrong;80,000Hours)](https://arxiv.org/) | [arxiv.xml](https://trvny.github.io/feedseek/arxiv.xml) |
| <img src="https://www.google.com/s2/favicons?domain=rssboard.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [RSS Boards](https://www.rssboard.org/) | [rssboard.xml](https://trvny.github.io/feedseek/rssboard.xml) |
| <img src="https://www.google.com/s2/favicons?domain=v2ex.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [V2EX + sspai](https://www.v2ex.com/) | [v2ex.xml](https://trvny.github.io/feedseek/v2ex.xml) |
| <img src="https://www.google.com/s2/favicons?domain=medium.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Medium](https://medium.com/) | [medium.xml](https://trvny.github.io/feedseek/medium.xml) |
| <img src="https://www.google.com/s2/favicons?domain=lichess.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [Lichess](https://lichess.org/blog) | [lichess.xml](https://trvny.github.io/feedseek/lichess.xml) |
| <img src="https://www.google.com/s2/favicons?domain=tunein.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Radios (TuneIn;Maxi Italo;Electro Swing)](https://tunein.com/) | [radios.xml](https://trvny.github.io/feedseek/radios.xml) |
| <img src="https://www.google.com/s2/favicons?domain=timeanddate.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [DaTime (timeanddate;Office Holidays)](https://www.timeanddate.com/news/) | [datime.xml](https://trvny.github.io/feedseek/datime.xml) |
| <img src="https://www.google.com/s2/favicons?domain=news.mit.edu&sz=32" width="16" height="16" align="absmiddle" alt=""> [MIT News](https://news.mit.edu/) | [mit.xml](https://trvny.github.io/feedseek/mit.xml) |
| <img src="https://www.google.com/s2/favicons?domain=dwutygodnik.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Dwutygodnik](https://www.dwutygodnik.com/) | [dwutygodnik.xml](https://trvny.github.io/feedseek/dwutygodnik.xml) |
| <img src="https://www.google.com/s2/favicons?domain=ffmpeg.org&sz=32" width="16" height="16" align="absmiddle" alt=""> [FFmpeg](https://ffmpeg.org/) | [ffmpeg.xml](https://trvny.github.io/feedseek/ffmpeg.xml) |
| <img src="https://www.google.com/s2/favicons?domain=download-soundtracks.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [Download Soundtracks](https://download-soundtracks.com/) | [download-soundtracks.xml](https://trvny.github.io/feedseek/download-soundtracks.xml) |
| <img src="https://www.google.com/s2/favicons?domain=youtube.com&sz=32" width="16" height="16" align="absmiddle" alt=""> [YouTubs (selected channels, no Shorts)](https://www.youtube.com/) | [youtubs.xml](https://trvny.github.io/feedseek/youtubs.xml) |
| <img src="https://www.google.com/s2/favicons?domain=1337x.to&sz=32" width="16" height="16" align="absmiddle" alt=""> [1337x Trending[OFF]](https://1337x.to/trending) | `1337x.xml` — disabled, not published |
| <img src="https://icons.duckduckgo.com/ip3/rutracker.org.ico" width="16" height="16" align="absmiddle" alt=""> [RuTracker](https://rutracker.org/) | [rutracker.xml](https://trvny.github.io/feedseek/rutracker.xml) |

> Favicons are pulled live from Google's favicon service
> (`https://www.google.com/s2/favicons?domain=<host>`) or DuckDuckGo (`https://icons.duckduckgo.com/ip3/.ico`); no images are committed
> to the repo.

## Documentation

- [Pipeline, enrichment, local usage and repository layout](docs/architecture.md)
- [Per-feed sources and design trade-offs](docs/feeds.md)
- [Cache behavior and maintenance](docs/cache.md)
- [Generated source inventory](docs/sources.md)
- [Generated index of every Model Feed JSON](docs/model-feeds.md)
- [LLM & agent access: remote MCP server, WebMCP, llms.txt, Model Feed JSON Schema](docs/agents.md)

The Android reader/player for these feeds lives in **[travnie/kanarek](https://github.com/travnie/kanarek)**.

## [License](LICENSE)

[![License](https://www.shieldcn.dev/github/license/trvny/feedseek.svg?variant=branded&size=xm&mode=light&theme=neutral&font=jetbrains-mono)](https://spdx.org/licenses/MIT)    [THIRD_PARTY_NOTICES](docs/THIRD_PARTY_NOTICES.md)

## 📰 Mini news

<!--README_FEED:START-->
- [Trust but Verify: Implementing Frontier AI Policy in California and Beyond](https://carnegieendowment.org/research/2026/11/trust-but-verify-implementing-frontier-ai-policy-in-california-and-beyond)
- [Promises Made, Promises Unmet: The NPP’s Struggle to Reform Sri Lanka](https://carnegieendowment.org/research/2026/11/promises-made-promises-unmet-the-npps-struggle-to-reform-sri-lanka)
- [homeassistant-ai/ha-mcp](https://github.com/homeassistant-ai/ha-mcp)
- [garrytan/gbrain](https://github.com/garrytan/gbrain)
- [anthropics/claude-quickstarts](https://github.com/anthropics/claude-quickstarts)
- [google-deepmind/mujoco](https://github.com/google-deepmind/mujoco)
<!--README_FEED:END-->

## 💬 Quote from the drawer

<!-- markdownlint-disable MD033 -->
<!--STARTS_HERE_QUOTE_README-->
<i>❝All the passions die with the years; self-love alone never dies. — Voltaire❞</i>
<!--ENDS_HERE_QUOTE_README-->
<!-- markdownlint-enable MD033 -->

## Other stuff

[![kanarek](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-kanarek.svg)](https://github.com/travnie/kanarek) [![tvpi](https://raw.githubusercontent.com/trvny/.github/main/assets/profile/pin-tvpi.svg)](https://github.com/trvny/tvpi)
