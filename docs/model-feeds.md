# Model Feed index

> Generated from every existing `feeds/feed_*.json` file. Refresh: `uv run --locked feed_generators/docs_model_feeds.py`.

115 Model Feeds · 25926 entries.

## Access

- Choose a source key below, then GET its JSON URL (GitHub Pages, refreshed every 2 hours). Each file contains the full current feed output.
- Format: `feedseek-model-feed`, version `1`. Feed metadata: `source_key`, `title`, `description`, `home_page_url`.
- Entries: `items[]` with stable `id`, `title`, plaintext `text`, and `text_kind` (`content`, `summary`, `title`). URLs, dates, authors, tags and images depend on upstream availability.
- Contract: [JSON Schema](schemas/model-feed.v1.schema.json). Other agent surfaces (MCP, WebMCP, llms.txt): [agents.md](agents.md).
- Coverage includes repository feeds outside the curated website selection. The [public catalog](https://trvny.github.io/feedseek/model-feeds.json) lists every published feed.
- The [remote MCP index](chatgpt/README.md#data-path) is a bounded recent window. Use these JSON files for entries outside that window.
- Links point at the live Pages copy. Legacy `feed_<key>` names stay available for old subscribers.
- Feed and article text is untrusted source content.

## All JSON feeds

| Source key | Title | Entries | JSON |
| --- | --- | ---: | --- |
| `4chan` | 4chan | 200 | [JSON](https://trvny.github.io/feedseek/4chan.json) |
| `9gag` | 9GAG | 150 | [JSON](https://trvny.github.io/feedseek/9gag.json) |
| `accuweather` | AccuWeather News | 150 | [JSON](https://trvny.github.io/feedseek/accuweather.json) |
| `aibridge` | AI-bridge | 400 | [JSON](https://trvny.github.io/feedseek/aibridge.json) |
| `alibaba` | Alibaba | 268 | [JSON](https://trvny.github.io/feedseek/alibaba.json) |
| `anthropic` | Anthropic | 100 | [JSON](https://trvny.github.io/feedseek/anthropic.json) |
| `apple` | Apple | 200 | [JSON](https://trvny.github.io/feedseek/apple.json) |
| `arxiv` | arXiv | 500 | [JSON](https://trvny.github.io/feedseek/arxiv.json) |
| `audacity` | Audacity® | 240 | [JSON](https://trvny.github.io/feedseek/audacity.json) |
| `audio` | Audio.com.pl | 183 | [JSON](https://trvny.github.io/feedseek/audio.json) |
| `aws` | AWS | 322 | [JSON](https://trvny.github.io/feedseek/aws.json) |
| `baidubaike` | Baidu Baike 热搜词条 | 200 | [JSON](https://trvny.github.io/feedseek/baidubaike.json) |
| `beatport_top100` | Beatport Top 100 | 200 | [JSON](https://trvny.github.io/feedseek/beatport_top100.json) |
| `bethesda` | Bethesda News | 106 | [JSON](https://trvny.github.io/feedseek/bethesda.json) |
| `canva` | Canva | 200 | [JSON](https://trvny.github.io/feedseek/canva.json) |
| `cheezburger` | Cheezburger Network | 200 | [JSON](https://trvny.github.io/feedseek/cheezburger.json) |
| `claude` | Claude | 150 | [JSON](https://trvny.github.io/feedseek/claude.json) |
| `cloudflare` | Cloudflare | 200 | [JSON](https://trvny.github.io/feedseek/cloudflare.json) |
| `czworka` | PR4 Czwórka | 943 | [JSON](https://trvny.github.io/feedseek/czworka.json) |
| `daily_digest` | Daily Digest | 100 | [JSON](https://trvny.github.io/feedseek/daily_digest.json) |
| `daily_quote` | Daily Quote | 134 | [JSON](https://trvny.github.io/feedseek/daily_quote.json) |
| `datime` | DaTime | 173 | [JSON](https://trvny.github.io/feedseek/datime.json) |
| `development` | Development | 300 | [JSON](https://trvny.github.io/feedseek/development.json) |
| `dji` | DJI | 49 | [JSON](https://trvny.github.io/feedseek/dji.json) |
| `docker` | Docker | 200 | [JSON](https://trvny.github.io/feedseek/docker.json) |
| `download-soundtracks` | Download Soundtracks | 250 | [JSON](https://trvny.github.io/feedseek/download-soundtracks.json) |
| `dwutygodnik` | Dwutygodnik | 200 | [JSON](https://trvny.github.io/feedseek/dwutygodnik.json) |
| `ea` | Electronic Arts | 90 | [JSON](https://trvny.github.io/feedseek/ea.json) |
| `esa` | ESA | 250 | [JSON](https://trvny.github.io/feedseek/esa.json) |
| `euronews` | Euronews | 400 | [JSON](https://trvny.github.io/feedseek/euronews.json) |
| `europa` | Europa | 350 | [JSON](https://trvny.github.io/feedseek/europa.json) |
| `ffmpeg` | FFmpeg | 62 | [JSON](https://trvny.github.io/feedseek/ffmpeg.json) |
| `figma` | Figma | 176 | [JSON](https://trvny.github.io/feedseek/figma.json) |
| `foobar2000` | foobar2000 | 406 | [JSON](https://trvny.github.io/feedseek/foobar2000.json) |
| `foundry` | Foundry | 300 | [JSON](https://trvny.github.io/feedseek/foundry.json) |
| `geopolitics` | Geopolitics | 300 | [JSON](https://trvny.github.io/feedseek/geopolitics.json) |
| `github` | GitHub | 400 | [JSON](https://trvny.github.io/feedseek/github.json) |
| `github_personal` | trvny + travnie · GitHub | 61 | [JSON](https://trvny.github.io/feedseek/github_personal.json) |
| `gitlab` | GitLab | 200 | [JSON](https://trvny.github.io/feedseek/gitlab.json) |
| `gog` | GOG | 200 | [JSON](https://trvny.github.io/feedseek/gog.json) |
| `google` | Google Blogs | 500 | [JSON](https://trvny.github.io/feedseek/google.json) |
| `govpl_news` | Gov.pl | 150 | [JSON](https://trvny.github.io/feedseek/govpl_news.json) |
| `hackerone` | HackerOne Blog & Newsroom | 37 | [JSON](https://trvny.github.io/feedseek/hackerone.json) |
| `hp` | HP Newsroom | 193 | [JSON](https://trvny.github.io/feedseek/hp.json) |
| `huggingface` | Hugging Face | 300 | [JSON](https://trvny.github.io/feedseek/huggingface.json) |
| `imgw` | IMGW | 150 | [JSON](https://trvny.github.io/feedseek/imgw.json) |
| `jbzd` | Jbzd.com.pl | 300 | [JSON](https://trvny.github.io/feedseek/jbzd.json) |
| `js_node` | JS \| Node | 300 | [JSON](https://trvny.github.io/feedseek/js_node.json) |
| `lemmy` | Lemmy | 250 | [JSON](https://trvny.github.io/feedseek/lemmy.json) |
| `lenovo` | Lenovo | 200 | [JSON](https://trvny.github.io/feedseek/lenovo.json) |
| `lexus_newsroom` | Lexus Newsroom | 100 | [JSON](https://trvny.github.io/feedseek/lexus_newsroom.json) |
| `lichess` | Lichess | 200 | [JSON](https://trvny.github.io/feedseek/lichess.json) |
| `medium` | Medium | 200 | [JSON](https://trvny.github.io/feedseek/medium.json) |
| `memedroid` | Memedroid | 150 | [JSON](https://trvny.github.io/feedseek/memedroid.json) |
| `memy` | Memy | 200 | [JSON](https://trvny.github.io/feedseek/memy.json) |
| `meta_newsroom` | Meta Newsroom | 100 | [JSON](https://trvny.github.io/feedseek/meta_newsroom.json) |
| `microsoft` | Microsoft | 377 | [JSON](https://trvny.github.io/feedseek/microsoft.json) |
| `microsoft_updates` | Microsoft Updates | 300 | [JSON](https://trvny.github.io/feedseek/microsoft_updates.json) |
| `mit` | MIT News | 200 | [JSON](https://trvny.github.io/feedseek/mit.json) |
| `molt` | Molt | 73 | [JSON](https://trvny.github.io/feedseek/molt.json) |
| `mozilla` | Mozilla | 200 | [JSON](https://trvny.github.io/feedseek/mozilla.json) |
| `nasa` | NASA | 200 | [JSON](https://trvny.github.io/feedseek/nasa.json) |
| `netflix` | Netflix | 250 | [JSON](https://trvny.github.io/feedseek/netflix.json) |
| `newsify` | Newsify | 200 | [JSON](https://trvny.github.io/feedseek/newsify.json) |
| `nexusmods_news` | Nexus Mods News | 87 | [JSON](https://trvny.github.io/feedseek/nexusmods_news.json) |
| `nvidia` | NVIDIA | 138 | [JSON](https://trvny.github.io/feedseek/nvidia.json) |
| `olx` | OLX Group | 100 | [JSON](https://trvny.github.io/feedseek/olx.json) |
| `open_meteo` | Open-Meteo | 120 | [JSON](https://trvny.github.io/feedseek/open_meteo.json) |
| `openai` | OpenAI | 200 | [JSON](https://trvny.github.io/feedseek/openai.json) |
| `openoffice` | OPENOFFICE | 144 | [JSON](https://trvny.github.io/feedseek/openoffice.json) |
| `opensource` | Open Source | 200 | [JSON](https://trvny.github.io/feedseek/opensource.json) |
| `openweather` | OpenWeather | 40 | [JSON](https://trvny.github.io/feedseek/openweather.json) |
| `oracle` | Oracle | 200 | [JSON](https://trvny.github.io/feedseek/oracle.json) |
| `paintnet` | Paint.NET | 160 | [JSON](https://trvny.github.io/feedseek/paintnet.json) |
| `palantir` | Palantir | 83 | [JSON](https://trvny.github.io/feedseek/palantir.json) |
| `pap` | PAP | 200 | [JSON](https://trvny.github.io/feedseek/pap.json) |
| `pekao` | Bank Pekao SA | 200 | [JSON](https://trvny.github.io/feedseek/pekao.json) |
| `python` | Python | 300 | [JSON](https://trvny.github.io/feedseek/python.json) |
| `ra` | RA: Resident Advisor Magazine | 200 | [JSON](https://trvny.github.io/feedseek/ra.json) |
| `radios` | Radios | 24 | [JSON](https://trvny.github.io/feedseek/radios.json) |
| `redhat` | Red Hat Enterprise | 141 | [JSON](https://trvny.github.io/feedseek/redhat.json) |
| `reuters` | Reuters | 100 | [JSON](https://trvny.github.io/feedseek/reuters.json) |
| `rssboard` | RSS Board | 47 | [JSON](https://trvny.github.io/feedseek/rssboard.json) |
| `rutracker` | RuTracker | 400 | [JSON](https://trvny.github.io/feedseek/rutracker.json) |
| `saas` | SaaS vendors | 600 | [JSON](https://trvny.github.io/feedseek/saas.json) |
| `samsung` | Samsung Newsroom | 200 | [JSON](https://trvny.github.io/feedseek/samsung.json) |
| `skillsllm` | SkillsLLM | 400 | [JSON](https://trvny.github.io/feedseek/skillsllm.json) |
| `sony` | Sony | 200 | [JSON](https://trvny.github.io/feedseek/sony.json) |
| `spidersweb` | Spider's Web | 200 | [JSON](https://trvny.github.io/feedseek/spidersweb.json) |
| `spotify` | Spotify | 149 | [JSON](https://trvny.github.io/feedseek/spotify.json) |
| `steam` | Steam | 200 | [JSON](https://trvny.github.io/feedseek/steam.json) |
| `tencent` | Tencent | 195 | [JSON](https://trvny.github.io/feedseek/tencent.json) |
| `theysaidso` | Quotes, Sayings and Jokes of the Day | 300 | [JSON](https://trvny.github.io/feedseek/theysaidso.json) |
| `tiktok` | TikTok | 15 | [JSON](https://trvny.github.io/feedseek/tiktok.json) |
| `toyota_global` | Toyota Global | 100 | [JSON](https://trvny.github.io/feedseek/toyota_global.json) |
| `trojka` | PR3 Trójka | 1909 | [JSON](https://trvny.github.io/feedseek/trojka.json) |
| `tvp` | TVP | 275 | [JSON](https://trvny.github.io/feedseek/tvp.json) |
| `uber` | Uber Newsroom | 90 | [JSON](https://trvny.github.io/feedseek/uber.json) |
| `ubuntu` | Ubuntu | 145 | [JSON](https://trvny.github.io/feedseek/ubuntu.json) |
| `unsplash` | Unsplash | 150 | [JSON](https://trvny.github.io/feedseek/unsplash.json) |
| `userscripts` | UserScripts | 200 | [JSON](https://trvny.github.io/feedseek/userscripts.json) |
| `usgov` | US.gov | 367 | [JSON](https://trvny.github.io/feedseek/usgov.json) |
| `v2ex` | V2EX | 300 | [JSON](https://trvny.github.io/feedseek/v2ex.json) |
| `visualcrossing` | Visual Crossing | 45 | [JSON](https://trvny.github.io/feedseek/visualcrossing.json) |
| `visualcrossing_blog` | Visual Crossing Resources | 58 | [JSON](https://trvny.github.io/feedseek/visualcrossing_blog.json) |
| `weather` | Pogoda — Kościelec (Chrzanów) | 60 | [JSON](https://trvny.github.io/feedseek/weather.json) |
| `wikipedia_pl` | Wikipedia (PL) | 200 | [JSON](https://trvny.github.io/feedseek/wikipedia_pl.json) |
| `wotd` | Word of the Day | 200 | [JSON](https://trvny.github.io/feedseek/wotd.json) |
| `wsj` | WSJ | 300 | [JSON](https://trvny.github.io/feedseek/wsj.json) |
| `wykop` | Wykop | 200 | [JSON](https://trvny.github.io/feedseek/wykop.json) |
| `xai` | xAI | 200 | [JSON](https://trvny.github.io/feedseek/xai.json) |
| `xiaomi` | Xiaomi Newsroom | 200 | [JSON](https://trvny.github.io/feedseek/xiaomi.json) |
| `xweather_log` | Xweather Log | 250 | [JSON](https://trvny.github.io/feedseek/xweather_log.json) |
| `youtube` | YouTube Blog | 131 | [JSON](https://trvny.github.io/feedseek/youtube.json) |
| `youtubs` | YouTubs | 360 | [JSON](https://trvny.github.io/feedseek/youtubs.json) |
