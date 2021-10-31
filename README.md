# SuperRare Watcher

[Scrapy](https://github.com/scrapy/scrapy) project to track SuperRare auctions.

## Installation

Packaging / dependencies is managed with [Poetry](https://python-poetry.org/docs/#installation).

From the project's root:

```bash
poetry install
```

## Usage

### Local installation

Activate the environment and run Scrapy command:

```bash
poetry shell
scrapy crawl [SPIDER]
```

Or use Poetry run command:

```bash
poetry run scrapy crawl [SPIDER]
```

### Docker container

Build Docker image:

```bash
poetry build -f wheel
docker build . --tag suprarewatcher
```

Run docker container:

```bash
docker run [ENV] suprarewatcher:latest scrapy crawl [SPIDER]
```

### Configuration

Tracker is configured by ENV variables, general configurations:

- `UPDATE_INTERVAL`: Seconds between each update (default: 180)
- `AUCTION_URL`: URL of the auction on SuperRare
- `DISCORD_WEBHOOK`: Discord webhook url to send messages to with the [DiscordBotExtension](#discordbotextension)

Further configuration can be found on the following modules.

## Modules

### BidWatcher

This spider will track new bids on the auction.

Configuration:

- `AUCTION_URL`: URL of the auction on SuperRare
- `BIDS_FILE`: Path to the local file to load / store bids (default: `bids.jsonl`)

Example:

```bash
export AUCTION_URL="https://superrare.com/artwork-v2/asymmetrical-liberation-29715"
poetry run scrapy crawl BidWatcher
```

### DiscordBotExtension

Extension to send bids to a Discord webhook, active by default.

Configuration:

- `DISCORD_WEBHOOK`: Discord webhook url to send messages to
