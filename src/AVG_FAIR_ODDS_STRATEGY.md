# Average Fair Odds Strategy

## 1. Start with a particular game, given by the user
    Example:
        - San Diego Padres vs Milwaukee Brewers

## 2. Scrape odds data for game from predetermined sports books
### BetFair
> Notes on Connecting:
> Currently using London, UK VPN vis NordVPN
>   - IP address: 47.158.160.200
>   - London #1847

Format: Fractional Odds

#### Example Odds:
```
Fractional Odds
Padres 1/1
Brewers 9/10
```

### Pinnacle
> Notes on Connecting:
> Does not work with VPN. Just ran in Incognito Mode and it worked

Format: `Decimal Odds`

#### Example Odds:
```
Decimal Odds
Padres 2.050
Brewers 1.884
```

### FanDuel
> Notes on Connecting:
> Does not work with VPN. Just ran in Incognito Mode and it worked

Format: `American Odds`

#### Example Odds:
```
American Odds
Padres -102
Brewers -116
```

## 3. Convert Odds to Fair Value

### Fractional Odds
#### Convert to Implied Probability
```python
def convert_to_implied(numerator: int, denominator: int) -> float:
    return denominator / (numerator + denominator)
```

### American Odds
#### Convert to Implied Probability
```python
def convert_to_implied(american_odds: int) -> float:
    if american_odds > 0:
        # Positive odds (underdog): +150 = 100/(150+100) = 40%
        return 100 / (american_odds + 100)
    else:
        # Negative odds (favorite): -150 = 150/(150+100) = 60%
        return abs(american_odds) / (abs(american_odds) + 100)
```

### Decimal Odds
#### Convert to Implied Probability
```python
def convert_to_implied(decimal_odds: float) -> float:
    return 1 / decimal_odds
```

## 4. Remove vig
### Fractional Odds
#### Example
```
Decimal Odds
Padres 2.050 -> 47.89%
Brewers 1.884 -> 52.11%
```


### American Odds
#### Example
```
Decimal Odds
Padres 2.050 -> 47.89%
Brewers 1.884 -> 52.11%
```

### Decimal Odds
#### Example
```
Decimal Odds
Padres 2.050 -> 47.89%
Brewers 1.884 -> 52.11%
```

# Fractional odds formula: Probability = Denominator / (Numerator + Denominator)
Padres: 1 / (1 + 1) = 50.00%
Brewers: 10 / (9 + 10) = 52.63%

Total = 50.00% + 52.63% = 102.63% (2.63% vig)

# Remove Vig
Padres_true = 50.00% / 102.63% = 48.72%
Brewers_true = 52.63% / 102.63% = 51.28%


## Three-Way Odds Format Comparison

| Sportsbook | Format | Padres Odds | Brewers Odds | Format Type |
|------------|--------|-------------|--------------|-------------|
| **FanDuel** | American | -102 | -116 | US Standard |
| **Pinnacle** | Decimal | 2.050 | 1.884 | International |
| **Betfair** | Fractional | 1/1 | 9/10 | UK Standard |

## Probability Analysis Results

| Sportsbook | Padres Implied % | Brewers Implied % | Total (Vig) | Padres True % | Brewers True % |
|------------|------------------|-------------------|-------------|---------------|----------------|
| **FanDuel** | 50.50% | 53.70% | 104.20% | 48.46% | 51.54% |
| **Pinnacle** | 48.78% | 53.08% | 101.86% | 47.89% | 52.11% |
| **Betfair** | 50.00% | 52.63% | 102.63% | 48.72% | 51.28% |

## Vig Comparison

| Sportsbook | Vig Percentage | Market Type | Notes |
|------------|----------------|-------------|--------|
| **Pinnacle** | 1.86% | Sharp/Professional | Lowest vig, tightest spreads |
| **Betfair** | 2.63% | Exchange/P2P | Middle ground, peer-to-peer |
| **FanDuel** | 4.20% | US Retail | Highest vig, recreational market |

## Weighted Fair Value Calculation

| Team | FanDuel (40%) | Pinnacle (35%) | Betfair (25%) | **Weighted Fair Value** |
|------|---------------|----------------|---------------|-------------------------|
| **Padres** | 48.46% × 0.40 | 47.89% × 0.35 | 48.72% × 0.25 | **48.35%** |
| **Brewers** | 51.54% × 0.40 | 52.11% × 0.35 | 51.28% × 0.25 | **51.65%** |

## Key Insights Summary

- **Most Efficient Market**: Pinnacle (1.86% vig)
- **Consensus Favorite**: Brewers (~51.6% probability)
- **Probability Range**: 1.22% spread between books for Padres
- **Best for Arbitrage**: Compare your 48.35% Padres fair value against Polymarket
