from pydantic import BaseModel

class InvestmentIndicators(BaseModel):
    corp_name: str
    market_cap: str
    dividend_yield: str
    per: str
    pbr: str
    roe: str
    psr: str
    foreign_ownership: str
