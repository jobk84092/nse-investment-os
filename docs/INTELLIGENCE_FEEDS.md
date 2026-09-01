# Intelligence Feeds

This layer turns the Investment OS from a scheduled report generator into an event-driven research system.

## Existing components already in the repository

- NSE announcements and corporate-action context
- RSS/news ingestion
- Telegram commentary ingestion
- AIB PDF portfolio synchronization
- Email digests and launchd scheduling

## Added event layer

All watchers write normalized, append-only records to:

`data/events/events.jsonl`

Event schema:

```json
{
  "event_id": "stable-dedup-id",
  "observed_at": "ISO timestamp",
  "source": "nse | google_drive | gmail",
  "type": "dividend | profit_warning | results | document_uploaded | ...",
  "title": "...",
  "url": "...",
  "requires_review": true
}
```

Agents should consume events by asking:

> What changed since the last successful analysis?

Do not repeatedly re-analyse the entire internet.

## Feed 1 — NSE corporate actions

Run:

```bash
python scripts/run_feeds.py
```

The watcher collects candidate corporate actions and announcements, classifies them, and writes evidence events. Dates and material details must still be verified from the issuer/exchange document before any portfolio action.

## Feed 2 — Google Drive document watcher

Configure local settings:

```json
"google_drive_watcher": {
  "enabled": true,
  "folder_id": "YOUR_FOLDER_ID",
  "token_path": "gdrive_token.json"
}
```

Recommended folder workflow:

```
Mac work → Google Drive / Agent Inbox
                      ↓
               gdrive_watcher
                      ↓
               document_uploaded event
                      ↓
            relevant Cursor agent
                      ↓
        extract → classify → analyse
```

Suggested routing:

- Investment PDFs → portfolio/thesis agent
- Job documents → career agent
- Research datasets → research agent
- AIB portfolio PDFs → holdings sync

## Operating principle

Watchers are deliberately dumb.

They:

1. detect
2. normalize
3. deduplicate
4. store an event

Analysis agents decide what the event means.

This separation prevents a scraper or watcher from becoming an uncontrolled autonomous decision-maker.
