from build import reel, save

reel(122, [
    ("This calm little pause often comes right before the next move up.",
     "A tall flagpole shaped like a strong green upward line with a small flag waving on top, the wolf saluting next to it."),
    ("First, a strong push up. That's the pole.", "@27_s1"),
    ("Then the price drifts slightly down or sideways in a tight channel. That's the flag.", "@122_s0!"),
    ("The signal is the breakout above the flag, ideally with rising volume.", "@26_s4"),
    ("Put your stop below the flag. If it fails, the loss stays small.", "@12_s3"),
])

reel(123, [
    ("The bear flag is the bull flag, turned upside down.",
     "A big bear holds a red flag on a pole pointing downward from a cliff edge, the wolf watching cautiously."),
    ("A sharp drop first, then a weak bounce inside a tight channel.", "@01_s2"),
    ("Buyers try to recover, but they're not strong enough.", "@27_s0"),
    ("A break below the flag often continues the downtrend.", "@11_s2"),
    ("The lesson: a small bounce after a crash is not always a recovery.", "@09_s2"),
])

reel(124, [
    ("Some stocks cost hundreds, even thousands of dollars per share. You don't need that much to start.", "@61_s2"),
    ("Many brokers let you buy fractional shares: just a slice of one share.", "@13_s3"),
    ("With ten dollars, you could own a tenth of a hundred-dollar share.", "@40_s0",
     {"ten dollars": "$10", "hundred-dollar": "$100"}),
    ("Your gains, losses and dividends are proportional to your slice.", "@55_s1"),
    ("Check the rules, though: some brokers don't let you transfer fractional shares elsewhere.", "@121_s0"),
])

reel(125, [
    ("Wedges look like triangles, but they often break the opposite way.",
     "Two glowing converging lines form a narrow wedge funnel tilted upward with a golden ball squeezed inside, the wolf watching."),
    ("A rising wedge climbs while getting narrower. Buyers are losing strength, and it often breaks down.", "@29_s2"),
    ("A falling wedge drops while narrowing. Sellers are tiring, and it often breaks up.", "@125_s0!"),
    ("Volume usually shrinks inside the wedge, then expands on the breakout.", "@30_s0"),
    ("Wait for the break, then manage your risk.", "@48_s2"),
])

reel(126, [
    ("This pattern looks like a teacup, and traders love it.",
     "A giant golden teacup with a handle sits on a hill shaped like a smooth U, the wolf sipping tea from a tiny cup next to it."),
    ("First, a rounded bottom: the cup. Price slowly recovers to the old high.", "@113_s0"),
    ("Then a small dip: the handle. Nervous holders sell, and the price shakes out.", "@12_s5"),
    ("A breakout above the rim of the cup is the classic signal.", "@26_s4"),
    ("It can take weeks or months to form. Patience is part of the pattern.", "@31_s5"),
])

reel(127, [
    ("Options can turn a small amount into a fortune, or into zero, very fast.",
     "The wolf sweats at a casino roulette table with stacks of chips, the wheel spinning, dramatic lights."),
    ("An option is a contract that gives you the right, but not the obligation, to buy or sell at a set price before a deadline.", "@38_s0"),
    ("A call option profits if the price goes up. A put profits if it goes down.", "@09_s0"),
    ("Time works against the buyer. Every day, the option loses some value, and many expire worthless.", "@05_s0"),
    ("Learn them slowly, with tiny amounts, or not at all.", "@01_s1"),
])

reel(128, [
    ("The price breaks out, you buy, and it immediately falls back. That's a fakeout.", "@16_s0"),
    ("A breakout is when price moves through a key level, like resistance.", "@26_s4"),
    ("Fakeouts happen when there aren't enough buyers to keep it going.", "@30_s0"),
    ("Look for a candle that closes above the level, rising volume, or a retest that holds.",
     "The wolf carefully taps a glowing floor with one foot to test it before stepping on it with his full weight."),
    ("And size your trade so that a fakeout is just a small, planned loss.", "@20_s1"),
])

reel(129, [
    ("The same coin can look bullish and bearish at the same time. It depends on the timeframe.",
     "The wolf looks confused at three screens side by side: a jagged zoomed-in chart, a medium chart, and a huge smooth long-term chart."),
    ("Each candle can be one minute, one hour, one day, or one week.", "@05_s0"),
    ("Short timeframes are noisy. Long ones show the bigger trend.", "@09_s3"),
    ("Day traders watch minutes. Long-term investors look at daily and weekly charts.", "@00_desk"),
    ("Pick the timeframe that matches how long you plan to hold.", "@13_s2"),
])

reel(130, [
    ("Buying stocks on margin means buying with money borrowed from your broker.", "@11_s1"),
    ("It multiplies your gains, and your losses.", "@11_s0"),
    ("If your account drops too far, you get a margin call: add money, or be forced to sell.",
     "The wolf's phone rings with an alarming red flashing screen while he holds his head, papers flying, at night."),
    ("And forced selling usually happens at the worst possible moment.", "@01_s0"),
    ("Plus, you pay interest on the loan for every day you hold.", "@21_s0"),
])

reel(131, [
    ("Professional traders rarely look at just one chart.", "@129_s0"),
    ("Start with a big timeframe, like the weekly, to find the main trend.", "@09_s3!"),
    ("Then zoom into the daily chart to find the key levels.", "@12_s2"),
    ("Then use a smaller timeframe to time your entry.", "@08_s4"),
    ("Trade in the direction of the bigger trend, and you're climbing with the market, not against it.", "@27_s1"),
])

reel(132, [
    ("The MACD is one of the most popular indicators in trading.",
     "Two glowing curved lines crossing above a histogram of green and red bars on a giant screen, the wolf pointing at the crossing."),
    ("It compares a fast moving average with a slow one, usually twelve and twenty-six periods.", "@28_s2",
     {"twelve": "12", "twenty-six": "26"}),
    ("When the MACD line crosses above its signal line, momentum is turning up.", "@132_s0!"),
    ("When it crosses below, momentum is turning down.", "@28_s2!"),
    ("It lags behind price and gives false signals in sideways markets. Combine it with other tools.", "@10_s4"),
])

reel(133, [
    ("In January 2021, an internet crowd took on Wall Street, and a video game store went to the moon.",
     "A huge crowd of cheering people holding phones launches a giant video game store shopping cart like a rocket over grand financial buildings, the wolf amazed."),
    ("Hedge funds had bet heavily against GameStop. More shares had been sold short than were available to trade.", "@15_s1"),
    ("Traders on Reddit started buying, forcing short sellers to buy back at higher and higher prices.", "@133_s0!"),
    ("The stock went from under twenty dollars to over four hundred in a few weeks.", "@14_s1",
     {"twenty dollars": "$20", "four hundred": "$400"}),
    ("Then it crashed. Some got rich, many bought the top. A short squeeze is a wild ride, not a strategy.", "@01_s2"),
])

save()
