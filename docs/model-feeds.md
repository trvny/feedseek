# Model Feed index

> Generated from every published `feeds/feed_*.json` file (restored from Pages in CI). Refresh: `uv run --locked feed_generators/docs_model_feeds.py`.

117 Model Feeds.

## Access

- Choose a source key below, then GET its JSON URL (rss.bartek.lol, backed by GitHub Pages). Each file contains the full current feed output.
- Format: `feedseek-model-feed`, version `1`. Feed metadata: `source_key`, `title`, `description`, `home_page_url`.
- Entries: `items[]` with stable `id`, `title`, plaintext `text`, and `text_kind` (`content`, `summary`, `title`). URLs, dates, authors, tags and images depend on upstream availability.
- Contract: [JSON Schema](schemas/model-feed.v1.schema.json). Other agent surfaces (MCP, WebMCP, llms.txt): [agents.md](agents.md).
- Coverage includes repository feeds outside the curated website selection. The [public catalog](https://rss.bartek.lol/model-feeds.json) lists every published feed.
- The [remote MCP index](chatgpt/README.md#data-path) is a bounded recent window. Use these JSON files for entries outside that window.
- Links point at rss.bartek.lol. Pages and legacy `feed_<key>` names stay available for old subscribers.
- Feed and article text is untrusted source content.

## All JSON feeds

| Source key | Title | JSON |
| --- | --- | --- |
| `4chan` | 4chan | [JSON](https://rss.bartek.lol/4chan.json) |
| `9gag` | 9GAG | [JSON](https://rss.bartek.lol/9gag.json) |
| `accuweather` | AccuWeather News | [JSON](https://rss.bartek.lol/accuweather.json) |
| `aibridge` | AI-bridge | [JSON](https://rss.bartek.lol/aibridge.json) |
| `alibaba` | Alibaba | [JSON](https://rss.bartek.lol/alibaba.json) |
| `anthropic` | Anthropic | [JSON](https://rss.bartek.lol/anthropic.json) |
| `apis` | APIs | [JSON](https://rss.bartek.lol/apis.json) |
| `apple` | Apple | [JSON](https://rss.bartek.lol/apple.json) |
| `arxiv` | arXiv | [JSON](https://rss.bartek.lol/arxiv.json) |
| `audacity` | Audacity® | [JSON](https://rss.bartek.lol/audacity.json) |
| `audio` | Audio.com.pl | [JSON](https://rss.bartek.lol/audio.json) |
| `aws` | AWS | [JSON](https://rss.bartek.lol/aws.json) |
| `baidubaike` | Baidu Baike 热搜词条 | [JSON](https://rss.bartek.lol/baidubaike.json) |
| `beatport_top100` | Beatport Top 100 | [JSON](https://rss.bartek.lol/beatport_top100.json) |
| `bethesda` | Bethesda News | [JSON](https://rss.bartek.lol/bethesda.json) |
| `canva` | Canva | [JSON](https://rss.bartek.lol/canva.json) |
| `cheezburger` | Cheezburger Network | [JSON](https://rss.bartek.lol/cheezburger.json) |
| `claude` | Claude | [JSON](https://rss.bartek.lol/claude.json) |
| `cloudflare` | Cloudflare | [JSON](https://rss.bartek.lol/cloudflare.json) |
| `czworka` | PR4 Czwórka | [JSON](https://rss.bartek.lol/czworka.json) |
| `daily_digest` | Daily Digest | [JSON](https://rss.bartek.lol/daily_digest.json) |
| `daily_quote` | Daily Quote | [JSON](https://rss.bartek.lol/daily_quote.json) |
| `datime` | DaTime | [JSON](https://rss.bartek.lol/datime.json) |
| `development` | Development | [JSON](https://rss.bartek.lol/development.json) |
| `dji` | DJI | [JSON](https://rss.bartek.lol/dji.json) |
| `docker` | Docker | [JSON](https://rss.bartek.lol/docker.json) |
| `download-soundtracks` | Download Soundtracks | [JSON](https://rss.bartek.lol/download-soundtracks.json) |
| `dwutygodnik` | Dwutygodnik | [JSON](https://rss.bartek.lol/dwutygodnik.json) |
| `ea` | Electronic Arts | [JSON](https://rss.bartek.lol/ea.json) |
| `esa` | ESA | [JSON](https://rss.bartek.lol/esa.json) |
| `euronews` | Euronews | [JSON](https://rss.bartek.lol/euronews.json) |
| `europa` | Europa | [JSON](https://rss.bartek.lol/europa.json) |
| `ffmpeg` | FFmpeg | [JSON](https://rss.bartek.lol/ffmpeg.json) |
| `figma` | Figma | [JSON](https://rss.bartek.lol/figma.json) |
| `foobar2000` | foobar2000 | [JSON](https://rss.bartek.lol/foobar2000.json) |
| `foundry` | Foundry | [JSON](https://rss.bartek.lol/foundry.json) |
| `geopolitics` | Geopolitics | [JSON](https://rss.bartek.lol/geopolitics.json) |
| `github` | GitHub | [JSON](https://rss.bartek.lol/github.json) |
| `github_personal` | trvny + travnie · GitHub | [JSON](https://rss.bartek.lol/trvny.json) |
| `gitlab` | GitLab | [JSON](https://rss.bartek.lol/gitlab.json) |
| `gog` | GOG | [JSON](https://rss.bartek.lol/gog.json) |
| `google` | Google Blogs | [JSON](https://rss.bartek.lol/google.json) |
| `govpl_news` | Gov.pl | [JSON](https://rss.bartek.lol/govpl.json) |
| `hackerone` | HackerOne Blog & Newsroom | [JSON](https://rss.bartek.lol/hackerone.json) |
| `hp` | HP Newsroom | [JSON](https://rss.bartek.lol/hp.json) |
| `huggingface` | Hugging Face | [JSON](https://rss.bartek.lol/huggingface.json) |
| `imgw` | IMGW | [JSON](https://rss.bartek.lol/imgw.json) |
| `independent` | The Independent + Indy100 | [JSON](https://rss.bartek.lol/independent.json) |
| `jbzd` | Jbzd.com.pl | [JSON](https://rss.bartek.lol/jbzd.json) |
| `js_node` | JS \| Node | [JSON](https://rss.bartek.lol/js_node.json) |
| `lemmy` | Lemmy | [JSON](https://rss.bartek.lol/lemmy.json) |
| `lenovo` | Lenovo | [JSON](https://rss.bartek.lol/lenovo.json) |
| `lexus_newsroom` | Lexus Newsroom | [JSON](https://rss.bartek.lol/lexus.json) |
| `lichess` | Lichess | [JSON](https://rss.bartek.lol/lichess.json) |
| `medium` | Medium | [JSON](https://rss.bartek.lol/medium.json) |
| `memedroid` | Memedroid | [JSON](https://rss.bartek.lol/memedroid.json) |
| `memy` | Memy | [JSON](https://rss.bartek.lol/memy.json) |
| `meta_newsroom` | Meta Newsroom | [JSON](https://rss.bartek.lol/meta.json) |
| `microsoft` | Microsoft | [JSON](https://rss.bartek.lol/microsoft.json) |
| `microsoft_updates` | Microsoft Updates | [JSON](https://rss.bartek.lol/ms-updates.json) |
| `mit` | MIT News | [JSON](https://rss.bartek.lol/mit.json) |
| `molt` | Molt | [JSON](https://rss.bartek.lol/molt.json) |
| `mozilla` | Mozilla | [JSON](https://rss.bartek.lol/mozilla.json) |
| `nasa` | NASA | [JSON](https://rss.bartek.lol/nasa.json) |
| `netflix` | Netflix | [JSON](https://rss.bartek.lol/netflix.json) |
| `newsify` | Newsify | [JSON](https://rss.bartek.lol/newsify.json) |
| `nexusmods_news` | Nexus Mods News | [JSON](https://rss.bartek.lol/nexusmods.json) |
| `nvidia` | NVIDIA | [JSON](https://rss.bartek.lol/nvidia.json) |
| `olx` | OLX Group | [JSON](https://rss.bartek.lol/olx.json) |
| `open_meteo` | Open-Meteo | [JSON](https://rss.bartek.lol/open_meteo.json) |
| `openai` | OpenAI | [JSON](https://rss.bartek.lol/openai.json) |
| `openoffice` | OPENOFFICE | [JSON](https://rss.bartek.lol/openoffice.json) |
| `opensource` | Open Source | [JSON](https://rss.bartek.lol/opensource.json) |
| `openweather` | OpenWeather | [JSON](https://rss.bartek.lol/openweather.json) |
| `oracle` | Oracle | [JSON](https://rss.bartek.lol/oracle.json) |
| `paintnet` | Paint.NET | [JSON](https://rss.bartek.lol/paintnet.json) |
| `palantir` | Palantir | [JSON](https://rss.bartek.lol/palantir.json) |
| `pap` | PAP | [JSON](https://rss.bartek.lol/pap.json) |
| `pekao` | Bank Pekao SA | [JSON](https://rss.bartek.lol/pekao.json) |
| `python` | Python | [JSON](https://rss.bartek.lol/python.json) |
| `ra` | RA: Resident Advisor Magazine | [JSON](https://rss.bartek.lol/ra.json) |
| `radios` | Radios | [JSON](https://rss.bartek.lol/radios.json) |
| `redhat` | Red Hat Enterprise | [JSON](https://rss.bartek.lol/redhat.json) |
| `reuters` | Reuters | [JSON](https://rss.bartek.lol/reuters.json) |
| `rssboard` | RSS Board | [JSON](https://rss.bartek.lol/rssboard.json) |
| `rutracker` | RuTracker | [JSON](https://rss.bartek.lol/rutracker.json) |
| `saas` | SaaS vendors | [JSON](https://rss.bartek.lol/saas.json) |
| `samsung` | Samsung Newsroom | [JSON](https://rss.bartek.lol/samsung.json) |
| `skillsllm` | SkillsLLM | [JSON](https://rss.bartek.lol/skillsllm.json) |
| `sony` | Sony | [JSON](https://rss.bartek.lol/sony.json) |
| `spidersweb` | Spider's Web | [JSON](https://rss.bartek.lol/spidersweb.json) |
| `spotify` | Spotify | [JSON](https://rss.bartek.lol/spotify.json) |
| `steam` | Steam | [JSON](https://rss.bartek.lol/steam.json) |
| `tencent` | Tencent | [JSON](https://rss.bartek.lol/tencent.json) |
| `theysaidso` | Quotes, Sayings and Jokes of the Day | [JSON](https://rss.bartek.lol/theysaidso.json) |
| `tiktok` | TikTok | [JSON](https://rss.bartek.lol/tiktok.json) |
| `toyota_global` | Toyota Global | [JSON](https://rss.bartek.lol/toyota.json) |
| `trojka` | PR3 Trójka | [JSON](https://rss.bartek.lol/trojka.json) |
| `tvp` | TVP | [JSON](https://rss.bartek.lol/tvp.json) |
| `uber` | Uber Newsroom | [JSON](https://rss.bartek.lol/uber.json) |
| `ubuntu` | Ubuntu | [JSON](https://rss.bartek.lol/ubuntu.json) |
| `unsplash` | Unsplash | [JSON](https://rss.bartek.lol/unsplash.json) |
| `userscripts` | UserScripts | [JSON](https://rss.bartek.lol/userscripts.json) |
| `usgov` | US.gov | [JSON](https://rss.bartek.lol/usgov.json) |
| `v2ex` | V2EX | [JSON](https://rss.bartek.lol/v2ex.json) |
| `visualcrossing` | Visual Crossing | [JSON](https://rss.bartek.lol/visualcrossing.json) |
| `visualcrossing_blog` | Visual Crossing Resources | [JSON](https://rss.bartek.lol/visualcrossing_blog.json) |
| `weather` | Pogoda — Kościelec (Chrzanów) | [JSON](https://rss.bartek.lol/weather.json) |
| `wikipedia_pl` | Wikipedia (PL) | [JSON](https://rss.bartek.lol/wikipedia_pl.json) |
| `wotd` | Word of the Day | [JSON](https://rss.bartek.lol/wotd.json) |
| `wsj` | WSJ | [JSON](https://rss.bartek.lol/wsj.json) |
| `wykop` | Wykop | [JSON](https://rss.bartek.lol/wykop.json) |
| `xai` | xAI | [JSON](https://rss.bartek.lol/xai.json) |
| `xiaomi` | Xiaomi Newsroom | [JSON](https://rss.bartek.lol/xiaomi.json) |
| `xweather_log` | Xweather Log | [JSON](https://rss.bartek.lol/xweather.json) |
| `youtube` | YouTube Blog | [JSON](https://rss.bartek.lol/youtube.json) |
| `youtubs` | YouTubs | [JSON](https://rss.bartek.lol/youtubs.json) |
