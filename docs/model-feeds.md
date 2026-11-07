# Model Feed index

> Generated from every existing `feeds/feed_*.json` file. Refresh: `uv run --locked feed_generators/docs_model_feeds.py`.

115 Model Feeds · 25926 entries.

## Access

- Choose a source key below, then GET its JSON URL (GitHub Pages, refreshed every 2 hours). Each file contains the full current feed output.
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
| `4chan` | 4chan | 200 | [JSON](https://trvny.github.io/feedseek/feed_4chan.json) |
| `9gag` | 9GAG | 150 | [JSON](https://trvny.github.io/feedseek/feed_9gag.json) |
| `accuweather` | AccuWeather News | 150 | [JSON](https://trvny.github.io/feedseek/feed_accuweather.json) |
| `aibridge` | AI-bridge | 400 | [JSON](https://trvny.github.io/feedseek/feed_aibridge.json) |
| `alibaba` | Alibaba | 268 | [JSON](https://trvny.github.io/feedseek/feed_alibaba.json) |
| `anthropic` | Anthropic | 100 | [JSON](https://trvny.github.io/feedseek/feed_anthropic.json) |
| `apple` | Apple | 200 | [JSON](https://trvny.github.io/feedseek/feed_apple.json) |
| `arxiv` | arXiv | 500 | [JSON](https://trvny.github.io/feedseek/feed_arxiv.json) |
| `audacity` | Audacity® | 240 | [JSON](https://trvny.github.io/feedseek/feed_audacity.json) |
| `audio` | Audio.com.pl | 183 | [JSON](https://trvny.github.io/feedseek/feed_audio.json) |
| `aws` | AWS | 322 | [JSON](https://trvny.github.io/feedseek/feed_aws.json) |
| `baidubaike` | Baidu Baike 热搜词条 | 200 | [JSON](https://trvny.github.io/feedseek/feed_baidubaike.json) |
| `beatport_top100` | Beatport Top 100 | 200 | [JSON](https://trvny.github.io/feedseek/feed_beatport_top100.json) |
| `bethesda` | Bethesda News | 106 | [JSON](https://trvny.github.io/feedseek/feed_bethesda.json) |
| `canva` | Canva | 200 | [JSON](https://trvny.github.io/feedseek/feed_canva.json) |
| `cheezburger` | Cheezburger Network | 200 | [JSON](https://trvny.github.io/feedseek/feed_cheezburger.json) |
| `claude` | Claude | 150 | [JSON](https://trvny.github.io/feedseek/feed_claude.json) |
| `cloudflare` | Cloudflare | 200 | [JSON](https://trvny.github.io/feedseek/feed_cloudflare.json) |
| `czworka` | PR4 Czwórka | 943 | [JSON](https://trvny.github.io/feedseek/feed_czworka.json) |
| `daily_digest` | Daily Digest | 100 | [JSON](https://trvny.github.io/feedseek/feed_daily_digest.json) |
| `daily_quote` | Daily Quote | 134 | [JSON](https://trvny.github.io/feedseek/feed_daily_quote.json) |
| `datime` | DaTime | 173 | [JSON](https://trvny.github.io/feedseek/feed_datime.json) |
| `development` | Development | 300 | [JSON](https://trvny.github.io/feedseek/feed_development.json) |
| `dji` | DJI | 49 | [JSON](https://trvny.github.io/feedseek/feed_dji.json) |
| `docker` | Docker | 200 | [JSON](https://trvny.github.io/feedseek/feed_docker.json) |
| `download-soundtracks` | Download Soundtracks | 250 | [JSON](https://trvny.github.io/feedseek/feed_download-soundtracks.json) |
| `dwutygodnik` | Dwutygodnik | 200 | [JSON](https://trvny.github.io/feedseek/feed_dwutygodnik.json) |
| `ea` | Electronic Arts | 90 | [JSON](https://trvny.github.io/feedseek/feed_ea.json) |
| `esa` | ESA | 250 | [JSON](https://trvny.github.io/feedseek/feed_esa.json) |
| `euronews` | Euronews | 400 | [JSON](https://trvny.github.io/feedseek/feed_euronews.json) |
| `europa` | Europa | 350 | [JSON](https://trvny.github.io/feedseek/feed_europa.json) |
| `ffmpeg` | FFmpeg | 62 | [JSON](https://trvny.github.io/feedseek/feed_ffmpeg.json) |
| `figma` | Figma | 176 | [JSON](https://trvny.github.io/feedseek/feed_figma.json) |
| `foobar2000` | foobar2000 | 406 | [JSON](https://trvny.github.io/feedseek/feed_foobar2000.json) |
| `foundry` | Foundry | 300 | [JSON](https://trvny.github.io/feedseek/feed_foundry.json) |
| `geopolitics` | Geopolitics | 300 | [JSON](https://trvny.github.io/feedseek/feed_geopolitics.json) |
| `github` | GitHub | 400 | [JSON](https://trvny.github.io/feedseek/feed_github.json) |
| `github_personal` | trvny + travnie · GitHub | 61 | [JSON](https://trvny.github.io/feedseek/feed_github_personal.json) |
| `gitlab` | GitLab | 200 | [JSON](https://trvny.github.io/feedseek/feed_gitlab.json) |
| `gog` | GOG | 200 | [JSON](https://trvny.github.io/feedseek/feed_gog.json) |
| `google` | Google Blogs | 500 | [JSON](https://trvny.github.io/feedseek/feed_google.json) |
| `govpl_news` | Gov.pl | 150 | [JSON](https://trvny.github.io/feedseek/feed_govpl_news.json) |
| `hackerone` | HackerOne Blog & Newsroom | 37 | [JSON](https://trvny.github.io/feedseek/feed_hackerone.json) |
| `hp` | HP Newsroom | 193 | [JSON](https://trvny.github.io/feedseek/feed_hp.json) |
| `huggingface` | Hugging Face | 300 | [JSON](https://trvny.github.io/feedseek/feed_huggingface.json) |
| `imgw` | IMGW | 150 | [JSON](https://trvny.github.io/feedseek/feed_imgw.json) |
| `jbzd` | Jbzd.com.pl | 300 | [JSON](https://trvny.github.io/feedseek/feed_jbzd.json) |
| `js_node` | JS \| Node | 300 | [JSON](https://trvny.github.io/feedseek/feed_js_node.json) |
| `lemmy` | Lemmy | 250 | [JSON](https://trvny.github.io/feedseek/feed_lemmy.json) |
| `lenovo` | Lenovo | 200 | [JSON](https://trvny.github.io/feedseek/feed_lenovo.json) |
| `lexus_newsroom` | Lexus Newsroom | 100 | [JSON](https://trvny.github.io/feedseek/feed_lexus_newsroom.json) |
| `lichess` | Lichess | 200 | [JSON](https://trvny.github.io/feedseek/feed_lichess.json) |
| `medium` | Medium | 200 | [JSON](https://trvny.github.io/feedseek/feed_medium.json) |
| `memedroid` | Memedroid | 150 | [JSON](https://trvny.github.io/feedseek/feed_memedroid.json) |
| `memy` | Memy | 200 | [JSON](https://trvny.github.io/feedseek/feed_memy.json) |
| `meta_newsroom` | Meta Newsroom | 100 | [JSON](https://trvny.github.io/feedseek/feed_meta_newsroom.json) |
| `microsoft` | Microsoft | 377 | [JSON](https://trvny.github.io/feedseek/feed_microsoft.json) |
| `microsoft_updates` | Microsoft Updates | 300 | [JSON](https://trvny.github.io/feedseek/feed_microsoft_updates.json) |
| `mit` | MIT News | 200 | [JSON](https://trvny.github.io/feedseek/feed_mit.json) |
| `molt` | Molt | 73 | [JSON](https://trvny.github.io/feedseek/feed_molt.json) |
| `mozilla` | Mozilla | 200 | [JSON](https://trvny.github.io/feedseek/feed_mozilla.json) |
| `nasa` | NASA | 200 | [JSON](https://trvny.github.io/feedseek/feed_nasa.json) |
| `netflix` | Netflix | 250 | [JSON](https://trvny.github.io/feedseek/feed_netflix.json) |
| `newsify` | Newsify | 200 | [JSON](https://trvny.github.io/feedseek/feed_newsify.json) |
| `nexusmods_news` | Nexus Mods News | 87 | [JSON](https://trvny.github.io/feedseek/feed_nexusmods_news.json) |
| `nvidia` | NVIDIA | 138 | [JSON](https://trvny.github.io/feedseek/feed_nvidia.json) |
| `olx` | OLX Group | 100 | [JSON](https://trvny.github.io/feedseek/feed_olx.json) |
| `open_meteo` | Open-Meteo | 120 | [JSON](https://trvny.github.io/feedseek/feed_open_meteo.json) |
| `openai` | OpenAI | 200 | [JSON](https://trvny.github.io/feedseek/feed_openai.json) |
| `openoffice` | OPENOFFICE | 144 | [JSON](https://trvny.github.io/feedseek/feed_openoffice.json) |
| `opensource` | Open Source | 200 | [JSON](https://trvny.github.io/feedseek/feed_opensource.json) |
| `openweather` | OpenWeather | 40 | [JSON](https://trvny.github.io/feedseek/feed_openweather.json) |
| `oracle` | Oracle | 200 | [JSON](https://trvny.github.io/feedseek/feed_oracle.json) |
| `paintnet` | Paint.NET | 160 | [JSON](https://trvny.github.io/feedseek/feed_paintnet.json) |
| `palantir` | Palantir | 83 | [JSON](https://trvny.github.io/feedseek/feed_palantir.json) |
| `pap` | PAP | 200 | [JSON](https://trvny.github.io/feedseek/feed_pap.json) |
| `pekao` | Bank Pekao SA | 200 | [JSON](https://trvny.github.io/feedseek/feed_pekao.json) |
| `python` | Python | 300 | [JSON](https://trvny.github.io/feedseek/feed_python.json) |
| `ra` | RA: Resident Advisor Magazine | 200 | [JSON](https://trvny.github.io/feedseek/feed_ra.json) |
| `radios` | Radios | 24 | [JSON](https://trvny.github.io/feedseek/feed_radios.json) |
| `redhat` | Red Hat Enterprise | 141 | [JSON](https://trvny.github.io/feedseek/feed_redhat.json) |
| `reuters` | Reuters | 100 | [JSON](https://trvny.github.io/feedseek/feed_reuters.json) |
| `rssboard` | RSS Board | 47 | [JSON](https://trvny.github.io/feedseek/feed_rssboard.json) |
| `rutracker` | RuTracker | 400 | [JSON](https://trvny.github.io/feedseek/feed_rutracker.json) |
| `saas` | SaaS vendors | 600 | [JSON](https://trvny.github.io/feedseek/feed_saas.json) |
| `samsung` | Samsung Newsroom | 200 | [JSON](https://trvny.github.io/feedseek/feed_samsung.json) |
| `skillsllm` | SkillsLLM | 400 | [JSON](https://trvny.github.io/feedseek/feed_skillsllm.json) |
| `sony` | Sony | 200 | [JSON](https://trvny.github.io/feedseek/feed_sony.json) |
| `spidersweb` | Spider's Web | 200 | [JSON](https://trvny.github.io/feedseek/feed_spidersweb.json) |
| `spotify` | Spotify | 149 | [JSON](https://trvny.github.io/feedseek/feed_spotify.json) |
| `steam` | Steam | 200 | [JSON](https://trvny.github.io/feedseek/feed_steam.json) |
| `tencent` | Tencent | 195 | [JSON](https://trvny.github.io/feedseek/feed_tencent.json) |
| `theysaidso` | Quotes, Sayings and Jokes of the Day | 300 | [JSON](https://trvny.github.io/feedseek/feed_theysaidso.json) |
| `tiktok` | TikTok | 15 | [JSON](https://trvny.github.io/feedseek/feed_tiktok.json) |
| `toyota_global` | Toyota Global | 100 | [JSON](https://trvny.github.io/feedseek/feed_toyota_global.json) |
| `trojka` | PR3 Trójka | 1909 | [JSON](https://trvny.github.io/feedseek/feed_trojka.json) |
| `tvp` | TVP | 275 | [JSON](https://trvny.github.io/feedseek/feed_tvp.json) |
| `uber` | Uber Newsroom | 90 | [JSON](https://trvny.github.io/feedseek/feed_uber.json) |
| `ubuntu` | Ubuntu | 145 | [JSON](https://trvny.github.io/feedseek/feed_ubuntu.json) |
| `unsplash` | Unsplash | 150 | [JSON](https://trvny.github.io/feedseek/feed_unsplash.json) |
| `userscripts` | UserScripts | 200 | [JSON](https://trvny.github.io/feedseek/feed_userscripts.json) |
| `usgov` | US.gov | 367 | [JSON](https://trvny.github.io/feedseek/feed_usgov.json) |
| `v2ex` | V2EX | 300 | [JSON](https://trvny.github.io/feedseek/feed_v2ex.json) |
| `visualcrossing` | Visual Crossing | 45 | [JSON](https://trvny.github.io/feedseek/feed_visualcrossing.json) |
| `visualcrossing_blog` | Visual Crossing Resources | 58 | [JSON](https://trvny.github.io/feedseek/feed_visualcrossing_blog.json) |
| `weather` | Pogoda — Kościelec (Chrzanów) | 60 | [JSON](https://trvny.github.io/feedseek/feed_weather.json) |
| `wikipedia_pl` | Wikipedia (PL) | 200 | [JSON](https://trvny.github.io/feedseek/feed_wikipedia_pl.json) |
| `wotd` | Word of the Day | 200 | [JSON](https://trvny.github.io/feedseek/feed_wotd.json) |
| `wsj` | WSJ | 300 | [JSON](https://trvny.github.io/feedseek/feed_wsj.json) |
| `wykop` | Wykop | 200 | [JSON](https://trvny.github.io/feedseek/feed_wykop.json) |
| `xai` | xAI | 200 | [JSON](https://trvny.github.io/feedseek/feed_xai.json) |
| `xiaomi` | Xiaomi Newsroom | 200 | [JSON](https://trvny.github.io/feedseek/feed_xiaomi.json) |
| `xweather_log` | Xweather Log | 250 | [JSON](https://trvny.github.io/feedseek/feed_xweather_log.json) |
| `youtube` | YouTube Blog | 131 | [JSON](https://trvny.github.io/feedseek/feed_youtube.json) |
| `youtubs` | YouTubs | 360 | [JSON](https://trvny.github.io/feedseek/feed_youtubs.json) |
