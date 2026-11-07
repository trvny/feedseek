# Model Feed index

> Generated from every published `feeds/feed_*.json` file (restored from Pages in CI). Refresh: `uv run --locked feed_generators/docs_model_feeds.py`.

115 Model Feeds.

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

| Source key | Title | JSON |
| --- | --- | --- |
| `4chan` | 4chan | [JSON](https://trvny.github.io/feedseek/4chan.json) |
| `9gag` | 9GAG | [JSON](https://trvny.github.io/feedseek/9gag.json) |
| `accuweather` | AccuWeather News | [JSON](https://trvny.github.io/feedseek/accuweather.json) |
| `aibridge` | AI-bridge | [JSON](https://trvny.github.io/feedseek/aibridge.json) |
| `alibaba` | Alibaba | [JSON](https://trvny.github.io/feedseek/alibaba.json) |
| `anthropic` | Anthropic | [JSON](https://trvny.github.io/feedseek/anthropic.json) |
| `apple` | Apple | [JSON](https://trvny.github.io/feedseek/apple.json) |
| `arxiv` | arXiv | [JSON](https://trvny.github.io/feedseek/arxiv.json) |
| `audacity` | Audacity® | [JSON](https://trvny.github.io/feedseek/audacity.json) |
| `audio` | Audio.com.pl | [JSON](https://trvny.github.io/feedseek/audio.json) |
| `aws` | AWS | [JSON](https://trvny.github.io/feedseek/aws.json) |
| `baidubaike` | Baidu Baike 热搜词条 | [JSON](https://trvny.github.io/feedseek/baidubaike.json) |
| `beatport_top100` | Beatport Top 100 | [JSON](https://trvny.github.io/feedseek/beatport_top100.json) |
| `bethesda` | Bethesda News | [JSON](https://trvny.github.io/feedseek/bethesda.json) |
| `canva` | Canva | [JSON](https://trvny.github.io/feedseek/canva.json) |
| `cheezburger` | Cheezburger Network | [JSON](https://trvny.github.io/feedseek/cheezburger.json) |
| `claude` | Claude | [JSON](https://trvny.github.io/feedseek/claude.json) |
| `cloudflare` | Cloudflare | [JSON](https://trvny.github.io/feedseek/cloudflare.json) |
| `czworka` | PR4 Czwórka | [JSON](https://trvny.github.io/feedseek/czworka.json) |
| `daily_digest` | Daily Digest | [JSON](https://trvny.github.io/feedseek/daily_digest.json) |
| `daily_quote` | Daily Quote | [JSON](https://trvny.github.io/feedseek/daily_quote.json) |
| `datime` | DaTime | [JSON](https://trvny.github.io/feedseek/datime.json) |
| `development` | Development | [JSON](https://trvny.github.io/feedseek/development.json) |
| `dji` | DJI | [JSON](https://trvny.github.io/feedseek/dji.json) |
| `docker` | Docker | [JSON](https://trvny.github.io/feedseek/docker.json) |
| `download-soundtracks` | Download Soundtracks | [JSON](https://trvny.github.io/feedseek/download-soundtracks.json) |
| `dwutygodnik` | Dwutygodnik | [JSON](https://trvny.github.io/feedseek/dwutygodnik.json) |
| `ea` | Electronic Arts | [JSON](https://trvny.github.io/feedseek/ea.json) |
| `esa` | ESA | [JSON](https://trvny.github.io/feedseek/esa.json) |
| `euronews` | Euronews | [JSON](https://trvny.github.io/feedseek/euronews.json) |
| `europa` | Europa | [JSON](https://trvny.github.io/feedseek/europa.json) |
| `ffmpeg` | FFmpeg | [JSON](https://trvny.github.io/feedseek/ffmpeg.json) |
| `figma` | Figma | [JSON](https://trvny.github.io/feedseek/figma.json) |
| `foobar2000` | foobar2000 | [JSON](https://trvny.github.io/feedseek/foobar2000.json) |
| `foundry` | Foundry | [JSON](https://trvny.github.io/feedseek/foundry.json) |
| `geopolitics` | Geopolitics | [JSON](https://trvny.github.io/feedseek/geopolitics.json) |
| `github` | GitHub | [JSON](https://trvny.github.io/feedseek/github.json) |
| `github_personal` | trvny + travnie · GitHub | [JSON](https://trvny.github.io/feedseek/github_personal.json) |
| `gitlab` | GitLab | [JSON](https://trvny.github.io/feedseek/gitlab.json) |
| `gog` | GOG | [JSON](https://trvny.github.io/feedseek/gog.json) |
| `google` | Google Blogs | [JSON](https://trvny.github.io/feedseek/google.json) |
| `govpl_news` | Gov.pl | [JSON](https://trvny.github.io/feedseek/govpl_news.json) |
| `hackerone` | HackerOne Blog & Newsroom | [JSON](https://trvny.github.io/feedseek/hackerone.json) |
| `hp` | HP Newsroom | [JSON](https://trvny.github.io/feedseek/hp.json) |
| `huggingface` | Hugging Face | [JSON](https://trvny.github.io/feedseek/huggingface.json) |
| `imgw` | IMGW | [JSON](https://trvny.github.io/feedseek/imgw.json) |
| `jbzd` | Jbzd.com.pl | [JSON](https://trvny.github.io/feedseek/jbzd.json) |
| `js_node` | JS \| Node | [JSON](https://trvny.github.io/feedseek/js_node.json) |
| `lemmy` | Lemmy | [JSON](https://trvny.github.io/feedseek/lemmy.json) |
| `lenovo` | Lenovo | [JSON](https://trvny.github.io/feedseek/lenovo.json) |
| `lexus_newsroom` | Lexus Newsroom | [JSON](https://trvny.github.io/feedseek/lexus_newsroom.json) |
| `lichess` | Lichess | [JSON](https://trvny.github.io/feedseek/lichess.json) |
| `medium` | Medium | [JSON](https://trvny.github.io/feedseek/medium.json) |
| `memedroid` | Memedroid | [JSON](https://trvny.github.io/feedseek/memedroid.json) |
| `memy` | Memy | [JSON](https://trvny.github.io/feedseek/memy.json) |
| `meta_newsroom` | Meta Newsroom | [JSON](https://trvny.github.io/feedseek/meta_newsroom.json) |
| `microsoft` | Microsoft | [JSON](https://trvny.github.io/feedseek/microsoft.json) |
| `microsoft_updates` | Microsoft Updates | [JSON](https://trvny.github.io/feedseek/microsoft_updates.json) |
| `mit` | MIT News | [JSON](https://trvny.github.io/feedseek/mit.json) |
| `molt` | Molt | [JSON](https://trvny.github.io/feedseek/molt.json) |
| `mozilla` | Mozilla | [JSON](https://trvny.github.io/feedseek/mozilla.json) |
| `nasa` | NASA | [JSON](https://trvny.github.io/feedseek/nasa.json) |
| `netflix` | Netflix | [JSON](https://trvny.github.io/feedseek/netflix.json) |
| `newsify` | Newsify | [JSON](https://trvny.github.io/feedseek/newsify.json) |
| `nexusmods_news` | Nexus Mods News | [JSON](https://trvny.github.io/feedseek/nexusmods_news.json) |
| `nvidia` | NVIDIA | [JSON](https://trvny.github.io/feedseek/nvidia.json) |
| `olx` | OLX Group | [JSON](https://trvny.github.io/feedseek/olx.json) |
| `open_meteo` | Open-Meteo | [JSON](https://trvny.github.io/feedseek/open_meteo.json) |
| `openai` | OpenAI | [JSON](https://trvny.github.io/feedseek/openai.json) |
| `openoffice` | OPENOFFICE | [JSON](https://trvny.github.io/feedseek/openoffice.json) |
| `opensource` | Open Source | [JSON](https://trvny.github.io/feedseek/opensource.json) |
| `openweather` | OpenWeather | [JSON](https://trvny.github.io/feedseek/openweather.json) |
| `oracle` | Oracle | [JSON](https://trvny.github.io/feedseek/oracle.json) |
| `paintnet` | Paint.NET | [JSON](https://trvny.github.io/feedseek/paintnet.json) |
| `palantir` | Palantir | [JSON](https://trvny.github.io/feedseek/palantir.json) |
| `pap` | PAP | [JSON](https://trvny.github.io/feedseek/pap.json) |
| `pekao` | Bank Pekao SA | [JSON](https://trvny.github.io/feedseek/pekao.json) |
| `python` | Python | [JSON](https://trvny.github.io/feedseek/python.json) |
| `ra` | RA: Resident Advisor Magazine | [JSON](https://trvny.github.io/feedseek/ra.json) |
| `radios` | Radios | [JSON](https://trvny.github.io/feedseek/radios.json) |
| `redhat` | Red Hat Enterprise | [JSON](https://trvny.github.io/feedseek/redhat.json) |
| `reuters` | Reuters | [JSON](https://trvny.github.io/feedseek/reuters.json) |
| `rssboard` | RSS Board | [JSON](https://trvny.github.io/feedseek/rssboard.json) |
| `rutracker` | RuTracker | [JSON](https://trvny.github.io/feedseek/rutracker.json) |
| `saas` | SaaS vendors | [JSON](https://trvny.github.io/feedseek/saas.json) |
| `samsung` | Samsung Newsroom | [JSON](https://trvny.github.io/feedseek/samsung.json) |
| `skillsllm` | SkillsLLM | [JSON](https://trvny.github.io/feedseek/skillsllm.json) |
| `sony` | Sony | [JSON](https://trvny.github.io/feedseek/sony.json) |
| `spidersweb` | Spider's Web | [JSON](https://trvny.github.io/feedseek/spidersweb.json) |
| `spotify` | Spotify | [JSON](https://trvny.github.io/feedseek/spotify.json) |
| `steam` | Steam | [JSON](https://trvny.github.io/feedseek/steam.json) |
| `tencent` | Tencent | [JSON](https://trvny.github.io/feedseek/tencent.json) |
| `theysaidso` | Quotes, Sayings and Jokes of the Day | [JSON](https://trvny.github.io/feedseek/theysaidso.json) |
| `tiktok` | TikTok | [JSON](https://trvny.github.io/feedseek/tiktok.json) |
| `toyota_global` | Toyota Global | [JSON](https://trvny.github.io/feedseek/toyota_global.json) |
| `trojka` | PR3 Trójka | [JSON](https://trvny.github.io/feedseek/trojka.json) |
| `tvp` | TVP | [JSON](https://trvny.github.io/feedseek/tvp.json) |
| `uber` | Uber Newsroom | [JSON](https://trvny.github.io/feedseek/uber.json) |
| `ubuntu` | Ubuntu | [JSON](https://trvny.github.io/feedseek/ubuntu.json) |
| `unsplash` | Unsplash | [JSON](https://trvny.github.io/feedseek/unsplash.json) |
| `userscripts` | UserScripts | [JSON](https://trvny.github.io/feedseek/userscripts.json) |
| `usgov` | US.gov | [JSON](https://trvny.github.io/feedseek/usgov.json) |
| `v2ex` | V2EX | [JSON](https://trvny.github.io/feedseek/v2ex.json) |
| `visualcrossing` | Visual Crossing | [JSON](https://trvny.github.io/feedseek/visualcrossing.json) |
| `visualcrossing_blog` | Visual Crossing Resources | [JSON](https://trvny.github.io/feedseek/visualcrossing_blog.json) |
| `weather` | Pogoda — Kościelec (Chrzanów) | [JSON](https://trvny.github.io/feedseek/weather.json) |
| `wikipedia_pl` | Wikipedia (PL) | [JSON](https://trvny.github.io/feedseek/wikipedia_pl.json) |
| `wotd` | Word of the Day | [JSON](https://trvny.github.io/feedseek/wotd.json) |
| `wsj` | WSJ | [JSON](https://trvny.github.io/feedseek/wsj.json) |
| `wykop` | Wykop | [JSON](https://trvny.github.io/feedseek/wykop.json) |
| `xai` | xAI | [JSON](https://trvny.github.io/feedseek/xai.json) |
| `xiaomi` | Xiaomi Newsroom | [JSON](https://trvny.github.io/feedseek/xiaomi.json) |
| `xweather_log` | Xweather Log | [JSON](https://trvny.github.io/feedseek/xweather_log.json) |
| `youtube` | YouTube Blog | [JSON](https://trvny.github.io/feedseek/youtube.json) |
| `youtubs` | YouTubs | [JSON](https://trvny.github.io/feedseek/youtubs.json) |
