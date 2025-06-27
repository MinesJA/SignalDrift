import asyncio
import statistics
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from calculators import decimal_odds
from models import OddsEvent, OddsSource, OddsType


# Mock
async def mock_get_betfair_odds(timestamp: datetime, request_id: UUID) -> dict[str, list[OddsEvent]]:
    await asyncio.sleep(0.2)

    result = [{"odds": 2.2, "question": "marlins"}, {"odds": 1.7, "question": "pirates"}]

    odds = decimal_odds.calculate_fair_odds(result)
    odds = [{   **odd.to_dict(),
                "timestamp": timestamp,
                "request_id": request_id,
                "source": OddsSource.BETFAIR,
            } for odd in odds]

    return {"betfair_odds": [OddsEvent(**odd) for odd in odds]}

async def mock_get_pinnacle_odds(timestamp: datetime, request_id: UUID) -> dict[str, list[OddsEvent]]:
    await asyncio.sleep(0.4)

    result = [{"odds": 2.0, "question": "marlins"}, {"odds": 1.9, "question": "pirates"}]

    # TODO: Have multiple conversions from dicts to objects back to dicts
    #   Maybe rethink
    odds = decimal_odds.calculate_fair_odds(result)
    odds = [{   **odd.to_dict(),
                "timestamp": timestamp,
                "request_id": request_id,
                "source": OddsSource.PINNACLE,
            } for odd in odds]

    return {"pinnacle_odds": [OddsEvent(**odd) for odd in odds]}

async def mock_get_polymarket_odds(timestamp: datetime, request_id: UUID) -> dict[str, list[OddsEvent]]:
    await asyncio.sleep(0.4)

    result = [{"odds": 0.4, "question": "marlins"}, {"odds": 0.6, "question": "pirates"}]

    # NOTE: There may be some implied_odds calculations we need to do but for now
    # we just take what Polymarket gives us.
    odds = [{   "question": odd["question"],
                "og_odds": odd["odds"],
                "fair_odds": odd["odds"],
                "impl_prob": odd["odds"],
                "odds_type": OddsType.EXCHANGE,
                "timestamp": timestamp,
                "request_id": request_id,
                "source": OddsSource.POLYMARKET,
            } for odd in result]

    return {"polymarket_odds": [OddsEvent(**odd) for odd in odds]}


def calculate_avg_impl_prob(data: dict[str, Any]) -> dict[str, float]:
    x = [odd.impl_prob for odd in (data.get("betfair_odds", []) + data.get("pinnacle_odds", []))]
    return {"avg_impl_prob": statistics.mean(x)}


# Depends on avg_impl_prob
def calculate_z(data: dict[str, Any]) -> dict[str, float]:
    a = data.get("avg_impl_prob")
    if a:
        return {"avg_impl_prob_mult": a * 8}
    else:
        return {}


#def strategy_a(data: Dict[str, Any]) -> List[OrderEvent]:
#    now = datetime.now()
#
#    if data.get('avg_impl_prob_mult', 0) > 0.25:
#        return [ OrderEvent(timestamp=now, price=0.25, order_signal=OrderSignal.LIMIT_BUY),
#                 OrderEvent(timestamp=now, price=0.35, order_signal=OrderSignal.LIMIT_SELL) ]
#    else:
#        return [OrderEvent(timestamp=now, price=0.55, order_signal=OrderSignal.LIMIT_SELL)]


#def executor(orders: List[OrderEvent]):





async def main():
    timestamp = datetime.now()
    request_id = uuid4()

    # Gather data
    results = await asyncio.gather(
        mock_get_betfair_odds(timestamp, request_id),
        mock_get_pinnacle_odds(timestamp, request_id),
        mock_get_polymarket_odds(timestamp, request_id)
    )

    data = {k: v for d in results for k, v in d.items()}

    for calculator in [calculate_avg_impl_prob, calculate_z]:
        data = data | calculator(data)

    print(data)

    orders = [strategy(data) for strategy in [strategy_a]]

    flattened_list = [item for sublist in orders for item in sublist]

    print("\n")

    print(flattened_list)








    #more_data = [calculator(**data) for calculator in [calculate_y]]

    #data = {**calculator(**data) for calculator in [calculate_y]}
    #more_data = dict(i for i in calculator.items() for d in [calculator_y]}

     #{
     # "betfair_odds": [{}],
     # "polymarket_odds": [{}],
     # "pinnacle_odds": [{}]
     #}

    #for r in results:
    #    print(r)

#if __name__ == "__main__":
#    #asyncio.run(main())
#    connect()
