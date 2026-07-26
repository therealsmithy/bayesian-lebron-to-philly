# Did the crowd beat the market on LeBron to Philly?

## The question
In the three weeks before LeBron signed with the 76ers, how did the crowd's belief in this move compare to the market's priced probability?

Philly's odds at landing the King was a longshot, never eclipsing 23% on Kalshi and sitting at around 10 cents a share at resolution. 

How wide was the gap between what the people were saying and what the money was saying?

## Data (July 3, 2026 - July 24, 2026)

* Market - Kalshi API
* Sentiment - Reddit API, pytrends for Google Trends volume

## Plan

1. Pull market odds
2. Pull in crowd data
3. Label Reddit post stance
4. Update beliefs day by day the Bayesian way
5. Compare and write it up