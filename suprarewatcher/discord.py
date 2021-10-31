from typing import Any, Union

import requests
import scrapy.http as http
import scrapy.signals as signals
from scrapy.crawler import Crawler
from scrapy.exceptions import NotConfigured
from scrapy.spiders import Spider
from twisted.internet import defer, reactor, task

from suprarewatcher.items import Bid


class DiscordBotExtension:
    """Extension to send bids messages to a Discord webhook."""

    webhook_url: str
    message = (
        "@{bidder_name} ([{bidder_address}](https://etherscan.io/address/{bidder_address})) "
        "bidded {bid_amount}Ξ on [{piece_name}]({auction_url})"
    )

    def __init__(
        self,
        webhook_url: str,
    ):
        self.webhook_url = webhook_url

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> "DiscordBotExtension":
        webhook_url = crawler.settings.get("DISCORD_WEBHOOK")
        if not webhook_url:
            raise NotConfigured("Missing discord webhook URL")
        extension = cls(webhook_url)

        crawler.signals.connect(extension.item_scraped, signal=signals.item_scraped)

        return extension

    def item_scraped(
        self, item: object, response: http.Response, spider: Spider
    ) -> Union[Any, defer.Deferred]:
        if not isinstance(item, Bid):
            return None
        return self.send_message(item)

    def send_message(self, item: Bid, ttl: int = 3) -> Union[None, defer.Deferred]:
        data = {"content": self.message.format(**dict(item))}
        response = requests.post(url=self.webhook_url, data=data)
        if response.status_code == 429 and ttl > 0:  # Discord rate limits
            retry_after = response.json().get("retry_after", 3)
            return task.deferLater(
                reactor, retry_after, self.send_message, item, ttl - 1
            )
