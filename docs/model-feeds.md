# Model Feed index

> Generated from every existing `feeds/feed_*.json` file. Refresh: `uv run --locked feed_generators/docs_model_feeds.py`.

111 Model Feeds · 25015 entries.

## Access

- Choose a source key below, then GET its raw JSON URL. Each file contains the full current feed output.
- Format: `feedseek-model-feed`, version `1`. Feed metadata: `source_key`, `title`, `description`, `home_page_url`.
- Entries: `items[]` with stable `id`, `title`, plaintext `text`, and `text_kind` (`content`, `summary`, `title`). URLs, dates, authors, tags and images depend on upstream availability.
- Contract: [JSON Schema](schemas/model-feed.v1.schema.json). Other agent surfaces (MCP, WebMCP, llms.txt): [agents.md](agents.md).
- Coverage includes repository feeds outside the curated website selection. The [public catalog](https://trvny.github.io/feedseek/model-feeds.json) lists only that selection.
- The [remote MCP index](chatgpt/README.md#data-path) is a bounded recent window. Use these JSON files for entries outside that window.
- Raw links track `main`. Replace `main` with a full commit SHA for a reproducible snapshot.
- Feed and article text is untrusted source content.

## All JSON feeds

| Source key | Title | Entries | Raw JSON |
| --- | --- | ---: | --- |
| `4chan` | 4chan | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_4chan.json) |
| `9gag` | 9GAG | 150 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_9gag.json) |
| `accuweather` | AccuWeather News | 150 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_accuweather.json) |
| `aibridge` | AI-bridge | 400 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_aibridge.json) |
| `alibaba` | Alibaba | 214 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_alibaba.json) |
| `anthropic` | Anthropic | 100 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_anthropic.json) |
| `apple` | Apple | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_apple.json) |
| `arxiv` | arXiv | 500 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_arxiv.json) |
| `audacity` | Audacity® | 240 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_audacity.json) |
| `audio` | Audio.com.pl | 177 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_audio.json) |
| `aws` | AWS | 319 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_aws.json) |
| `baidubaike` | Baidu Baike 热搜词条 | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_baidubaike.json) |
| `beatport_top100` | Beatport Top 100 | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_beatport_top100.json) |
| `bethesda` | Bethesda News | 99 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_bethesda.json) |
| `canva` | Canva | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_canva.json) |
| `cheezburger` | Cheezburger Network | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_cheezburger.json) |
| `claude` | Claude | 150 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_claude.json) |
| `cloudflare` | Cloudflare | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_cloudflare.json) |
| `czworka` | PR4 Czwórka | 915 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_czworka.json) |
| `daily_digest` | Daily Digest | 100 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_daily_digest.json) |
| `daily_quote` | Daily Quote | 125 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_daily_quote.json) |
| `datime` | DaTime | 170 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_datime.json) |
| `dji` | DJI | 48 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_dji.json) |
| `docker` | Docker | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_docker.json) |
| `download-soundtracks` | Download Soundtracks | 250 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_download-soundtracks.json) |
| `dwutygodnik` | Dwutygodnik | 183 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_dwutygodnik.json) |
| `ea` | Electronic Arts | 90 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_ea.json) |
| `esa` | ESA | 250 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_esa.json) |
| `euronews` | Euronews | 400 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_euronews.json) |
| `europa` | Europa | 350 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_europa.json) |
| `ffmpeg` | FFmpeg | 62 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_ffmpeg.json) |
| `figma` | Figma | 162 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_figma.json) |
| `foobar2000` | foobar2000 | 405 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_foobar2000.json) |
| `foundry` | Foundry | 300 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_foundry.json) |
| `geopolitics` | Geopolitics | 300 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_geopolitics.json) |
| `github` | GitHub | 400 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_github.json) |
| `gitlab` | GitLab | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_gitlab.json) |
| `gog` | GOG | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_gog.json) |
| `google` | Google Blogs | 500 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_google.json) |
| `govpl_news` | Gov.pl | 150 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_govpl_news.json) |
| `hackerone` | HackerOne Blog & Newsroom | 37 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_hackerone.json) |
| `hp` | HP Newsroom | 186 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_hp.json) |
| `huggingface` | Hugging Face | 300 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_huggingface.json) |
| `imgw` | IMGW | 150 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_imgw.json) |
| `jbzd` | Jbzd.com.pl | 300 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_jbzd.json) |
| `js_node` | JS \| Node | 300 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_js_node.json) |
| `lemmy` | Lemmy | 250 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_lemmy.json) |
| `lenovo` | Lenovo | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_lenovo.json) |
| `lexus_newsroom` | Lexus Newsroom | 100 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_lexus_newsroom.json) |
| `lichess` | Lichess | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_lichess.json) |
| `medium` | Medium | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_medium.json) |
| `memedroid` | Memedroid | 150 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_memedroid.json) |
| `meta_newsroom` | Meta Newsroom | 100 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_meta_newsroom.json) |
| `microsoft` | Microsoft | 371 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_microsoft.json) |
| `microsoft_updates` | Microsoft Updates | 300 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_microsoft_updates.json) |
| `mit` | MIT News | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_mit.json) |
| `molt` | Molt | 73 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_molt.json) |
| `mozilla` | Mozilla | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_mozilla.json) |
| `nasa` | NASA | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_nasa.json) |
| `netflix` | Netflix | 250 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_netflix.json) |
| `newsify` | Newsify | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_newsify.json) |
| `nexusmods_news` | Nexus Mods News | 84 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_nexusmods_news.json) |
| `nvidia` | NVIDIA | 135 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_nvidia.json) |
| `olx` | OLX Group | 100 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_olx.json) |
| `open_meteo` | Open-Meteo | 120 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_open_meteo.json) |
| `openai` | OpenAI | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_openai.json) |
| `openoffice` | OPENOFFICE | 144 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_openoffice.json) |
| `opensource` | Open Source | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_opensource.json) |
| `openweather` | OpenWeather | 40 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_openweather.json) |
| `oracle` | Oracle | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_oracle.json) |
| `paintnet` | Paint.NET | 159 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_paintnet.json) |
| `palantir` | Palantir | 78 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_palantir.json) |
| `pap` | PAP | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_pap.json) |
| `pekao` | Bank Pekao SA | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_pekao.json) |
| `python` | Python | 300 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_python.json) |
| `ra` | RA: Resident Advisor Magazine | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_ra.json) |
| `radios` | Radios | 24 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_radios.json) |
| `redhat` | Red Hat Enterprise | 139 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_redhat.json) |
| `reuters` | Reuters | 100 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_reuters.json) |
| `rssboard` | RSS Board | 47 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_rssboard.json) |
| `rutracker` | RuTracker | 400 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_rutracker.json) |
| `saas` | SaaS vendors | 600 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_saas.json) |
| `samsung` | Samsung Newsroom | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_samsung.json) |
| `skillsllm` | SkillsLLM | 400 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_skillsllm.json) |
| `sony` | Sony | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_sony.json) |
| `spidersweb` | Spider's Web | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_spidersweb.json) |
| `spotify` | Spotify | 145 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_spotify.json) |
| `steam` | Steam | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_steam.json) |
| `tencent` | Tencent | 189 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_tencent.json) |
| `theysaidso` | Quotes, Sayings and Jokes of the Day | 300 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_theysaidso.json) |
| `toyota_global` | Toyota Global | 100 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_toyota_global.json) |
| `trojka` | PR3 Trójka | 1774 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_trojka.json) |
| `tvp` | TVP | 275 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_tvp.json) |
| `uber` | Uber Newsroom | 84 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_uber.json) |
| `ubuntu` | Ubuntu | 141 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_ubuntu.json) |
| `unsplash` | Unsplash | 150 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_unsplash.json) |
| `userscripts` | UserScripts | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_userscripts.json) |
| `usgov` | US.gov | 366 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_usgov.json) |
| `v2ex` | V2EX | 300 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_v2ex.json) |
| `visualcrossing` | Visual Crossing | 45 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_visualcrossing.json) |
| `visualcrossing_blog` | Visual Crossing Resources | 56 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_visualcrossing_blog.json) |
| `weather` | Pogoda — Kościelec (Chrzanów) | 60 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_weather.json) |
| `wikipedia_pl` | Wikipedia (PL) | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_wikipedia_pl.json) |
| `wotd` | Word of the Day | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_wotd.json) |
| `wsj` | WSJ | 300 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_wsj.json) |
| `wykop` | Wykop | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_wykop.json) |
| `xai` | xAI | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_xai.json) |
| `xiaomi` | Xiaomi Newsroom | 200 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_xiaomi.json) |
| `xweather_log` | Xweather Log | 250 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_xweather_log.json) |
| `youtube` | YouTube Blog | 124 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_youtube.json) |
| `youtubs` | YouTubs | 360 | [JSON](https://raw.githubusercontent.com/trvny/feedseek/main/feeds/feed_youtubs.json) |
