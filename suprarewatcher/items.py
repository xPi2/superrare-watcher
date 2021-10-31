from pydantic import BaseModel


class Bid(BaseModel):

    auction_token: int
    auction_url: str
    piece_name: str
    bidder_name: str
    bidder_address: str
    bid_amount: float
