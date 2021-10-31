from pathlib import Path
from typing import Iterator, List

import jsonlines
import scrapy
import scrapy.http as http
from scrapy.crawler import Crawler
from suprarewatcher.items import Bid
from twisted.python.failure import Failure


class BidWatcherSpider(scrapy.Spider):
    """Spider to track bids on SuperRare auction.

    This Spider uses the auction url to extract the auction token id first,
    the with the token perform continuous calls to the SuperRare NFT API.

    With each call extract all auction bids, store and yield new bids.
    Bids are loaded / stored in a local json file in jsonlines format.

    Delay between calls can be configured through `DOWNLOAD_DELAY` setting.

    Configuration:
    - `AUCTION_URL`: URL of the auction on SuperRare
    - `BIDS_FILE`: Path to the local file to load / store bids (default: `bids.jsonl`)
    """

    name: str = "BidWatcher"
    api_url: str = "https://superrare.com/api/v2/nft/get"
    auction_url: str = ""
    tokend_id: int
    bids_file_path: str
    bids: List[dict]

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args, **kwargs) -> "BidWatcherSpider":
        spider = cls(*args, **kwargs)
        spider._set_crawler(crawler)
        spider._set_auction(crawler)
        spider._load_bids_list(crawler)
        return spider

    def _set_auction(self, crawler: Crawler) -> None:
        if not crawler.settings.get("AUCTION_URL"):
            raise Exception("Missing auction url")
        self.auction_url = crawler.settings.get("AUCTION_URL")

    def _load_bids_list(self, crawler: Crawler) -> None:
        bids_file_path = Path(
            crawler.settings.get("BIDS_FILE", Path.cwd() / "bids.jsonl")
        )
        if not bids_file_path.exists():
            bids_file_path.parent.mkdir(parents=True, exist_ok=True)
            bids_file_path.touch()
        self.bids_file_path = bids_file_path

        with jsonlines.open(self.bids_file_path, "r") as reader:
            self.bids = [bid for bid in reader]

    def start_requests(self) -> Iterator[http.Request]:
        self.token_id = int(self.auction_url.rsplit("-")[-1])
        json_parameters = {
            "tokenId": self.token_id,
            "contractAddress": "0xb932a70a57673d89f4acffbe830e8ed7f75fb9e0",
            "marketAddresses": [
                "0x41a322b28d0ff354040e2cbc676f0320d8c8850d",
                "0x65b49f7aee40347f5a90b714be4ef086f3fe5e2c",
                "0x2947f98c42597966a0ec25e92843c09ac17fbaa7",
                "0x65b49f7aee40347f5a90b714be4ef086f3fe5e2c",
                "0x2947f98c42597966a0ec25e92843c09ac17fbaa7",
            ],
            "fingerprint": None,
            "contractAddresses": ["0xb932a70a57673d89f4acffbe830e8ed7f75fb9e0"],
        }

        while True:
            yield http.JsonRequest(
                url=self.api_url,
                method="POST",
                data=json_parameters,
                errback=self.catch,
                dont_filter=True,
            )

    def catch(self, failure: Failure) -> None:
        self.logger.error(repr(failure))

    def parse(self, response: http.Response) -> dict:
        data = response.json()["result"]
        piece_name = data["metadata"].get("name")
        auction_bids = data.get("auction", {}).get("allAuctionBids", [])
        auction_bids.reverse()
        for bid in auction_bids:
            _amount = float(bid["amount"]) / 10 ** 18 if bid.get("amount") else None
            bid = Bid(
                auction_token=self.token_id,
                auction_url=self.auction_url,
                piece_name=piece_name,
                bidder_name=bid.get("bidder", {}).get("username"),
                bidder_address=bid.get("bidderAddress"),
                bid_amount=_amount,
            )
            if bid.dict() not in self.bids:
                self.bids.append(bid.dict())
                yield bid
        self._store_bids()

    def _store_bids(self):
        with jsonlines.open(self.bids_file_path, "w") as writer:
            writer.write_all(self.bids)
