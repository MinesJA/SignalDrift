# Odds Aggregator Idea

Pull odds from major sports books:

1. BetFair
2. FanDuel
3. Pinnacle
4. Circa

Convert to true odds for each and average out.

> Note:
> We will probably need to weight these as we figure out which ones are more/less accurate

Pull pricing data for Polymarket.

If the polymarket price is "discounted" compared to average, submit limit order to Polymarket with limit sell at average odds calculated above.

> Note:
> Will need to figure out stop loss as well
