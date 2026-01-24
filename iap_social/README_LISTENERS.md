# Notion & Mastodon Listeners

Auto-create posts from a Notion **Post Queue** and auto-reply to **Mastodon mentions**.

---

## 5. Notion API listener → Auto-create posts

Polls a Notion database for rows with **Status = Pending**, generates posts (RAG + OpenRouter), optionally posts to Mastodon, then updates **Status** to **Generated** or **Posted**.

### Setup

1. **Create a Notion database** (table) with these properties (names must match):

   | Property | Type   | Values / notes |
   |----------|--------|----------------|
   | **Name** | Title  | Optional label |
   | **Platform** | Select | `twitter`, `linkedin`, `instagram`, `facebook` |
   | **Type** | Select | `general`, `product`, `technology`, `use_case`, `announcement`, `educational` |
   | **Topic** | Text | Optional focus |
   | **Status** | Select | `Pending`, `Generated`, `Posted` |

2. **Share** the database with your Notion integration.

3. **Copy the database ID** from the URL:
   `https://notion.so/...?v=XXXXXXXX` or `.../XXXXXXXX?pvs=4`  
   The hex block (with or without dashes) is the ID.

4. **Add to `.env`**:
   ```bash
   NOTION_POST_QUEUE_DATABASE_ID=your_database_id
   ```

5. **Run**:
   ```bash
   # Process pending rows once (generate only)
   python notion_listener.py

   # Generate + post to Mastodon
   python notion_listener.py --post-mastodon

   # Poll every 60s
   python notion_listener.py --post-mastodon --interval 60
   ```

Add rows with **Status = Pending** and the desired **Platform** / **Type** / **Topic**. The listener will generate a post, store it in SQLite, and optionally publish to Mastodon.

---

## 6. Mastodon comments listener → Auto-reply to mentions

Polls Mastodon **notifications** for **mentions**, generates replies with AI (Widvid context), posts each reply, and records it so we never reply twice.

### Setup

1. **`.env`** must include:
   - `MASTODON_ACCESS_TOKEN`
   - `MASTODON_INSTANCE` (e.g. `https://mastodon.social`)
   - `OPENROUTER_API_KEY`

2. **Run**:
   ```bash
   # Process mentions once
   python mastodon_listener.py

   # Poll every 90s
   python mastodon_listener.py --interval 90
   ```

Replied-to notification IDs are stored in `mastodon_replied` (SQLite). Uses the same Widvid/Notion context as post generation where available.

---

## Running both

Run each listener in its own process (e.g. two terminals or two systemd units):

```bash
python notion_listener.py --post-mastodon --interval 120
python mastodon_listener.py --interval 90
```

Or use a process manager (systemd, supervisord, etc.) to keep them running.
