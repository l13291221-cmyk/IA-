from build import reel, save

reel(134, [
    ("Bollinger Bands wrap the price in a channel that breathes with volatility.",
     "A glowing price line flows through a stretchy elastic tube that widens and narrows, the wolf stretching the tube with his paws."),
    ("The middle line is a twenty-period average. The outer bands sit two standard deviations above and below.", "@28_s2",
     {"twenty-period": "20-period"}),
    ("When the bands squeeze tight, volatility is low, and a big move often follows.", "@125_s0"),
    ("Touching the upper band doesn't automatically mean sell. In strong trends, price can ride the band.", "@09_s1"),
    ("Use the bands to read volatility, not as a magic buy or sell button.", "@10_s4"),
])

reel(135, [
    ("Two moving averages, one big difference: speed.", "@28_s2"),
    ("A simple moving average gives every day the same weight.", "@07_s1"),
    ("An exponential moving average gives more weight to recent prices, so it reacts faster.",
     "A sleek fast race car and a slow heavy truck drive side by side on a glowing road shaped like a chart, the wolf waving a racing flag."),
    ("Faster means earlier signals, but also more false ones.", "@12_s5"),
    ("Many traders use EMAs for short-term moves, and SMAs, like the two-hundred-day, for the big picture.", "@09_s3",
     {"two-hundred-day": "200-day"}),
])

reel(136, [
    ("Some stocks move on memes, not on business results. They're called meme stocks.", "@133_s0"),
    ("Online communities pile in, prices explode, and social media fuels the fire.", "@35_s1"),
    ("GameStop and AMC were the famous examples in 2021.", "@133_s0!"),
    ("Prices can disconnect completely from the company's real value, in both directions.", "@11_s2"),
    ("If you join the party, know that the music can stop at any second.", "@30_s0"),
])

reel(137, [
    ("Traders draw these lines on almost every chart. They come from a math sequence that's eight hundred years old.",
     "The wolf draws glowing horizontal lines across a big chart, a golden spiral shell floating beside him and an ancient scroll on the desk.",
     {"eight hundred": "800"}),
    ("Fibonacci retracements mark where a pullback might pause, often around thirty-eight, fifty, or sixty-two percent.", "@12_s2",
     {"thirty-eight": "38", "fifty": "50", "sixty-two percent": "62%"}),
    ("After a big move up, traders watch those levels for a bounce.", "@26_s1"),
    ("They work partly because so many people watch them.", "@30_s1"),
    ("Treat them as zones of interest, never as guarantees.", "@26_s0"),
])

reel(138, [
    ("Sometimes price says one thing, and momentum says another. That's a divergence.",
     "Two paths split on a mountain, one climbing up and the other sloping down, the wolf standing at the fork with a compass."),
    ("Price makes a higher high, but the RSI makes a lower high. Momentum is fading.", "@29_s0"),
    ("That's a bearish divergence: an early warning of a possible reversal.", "@108_s0"),
    ("The opposite, lower lows in price with higher lows in the RSI, is a bullish divergence.", "@138_s0!"),
    ("Divergences can last a long time before anything happens. Wait for price to confirm.", "@48_s2"),
])

reel(139, [
    ("The stock market is divided into sectors, like technology, healthcare, energy and banks.",
     "A big city map divided into colorful districts: a tech district, a hospital district, an oil refinery district and a bank district, the wolf looking from above."),
    ("Different sectors shine at different times in the economic cycle.", "@09_s3"),
    ("Tech often leads in booms. Utilities and consumer staples tend to hold up better in slowdowns.", "@73_s0"),
    ("Sector ETFs let you invest in a whole industry at once.", "@49_s0"),
    ("But betting heavily on one sector means less diversification. Know where you're concentrated.", "@18_s0"),
])

reel(140, [
    ("You can lose most of your trades and still make money. Here's how.", "@20_s3"),
    ("Before you enter, decide where you're wrong, your stop, and where you take profit, your target.", "@12_s2"),
    ("If you risk one to make three, one win pays for three losses.",
     "A balance scale where one small red weight is outweighed by three shiny gold coins on the other side, the wolf smiling.",
     {"one to make three": "1 to make 3"}),
    ("Most beginners do the opposite: tiny wins, and huge losses.", "@13_s0"),
    ("Aim for trades where the reward is at least twice the risk.", "@20_s1"),
])

reel(141, [
    ("The best traders keep a diary. It's called a trading journal.",
     "The wolf writes in a thick leather journal at night by a desk lamp, charts glowing on a screen behind him."),
    ("For every trade: why you entered, where your stop was, and how you felt.", "@45_s0"),
    ("After a month, patterns appear. Maybe you lose most trades on Fridays, or right after a big win.", "@10_s2"),
    ("The journal shows your mistakes before the market makes you pay for them twice.", "@38_s0"),
    ("What gets measured gets improved.", "@27_s1"),
])

reel(142, [
    ("Some of the world's fastest-growing economies are called emerging markets.",
     "The wolf flies in a hot air balloon over a rapidly growing city with cranes and new skyscrapers rising, sunrise."),
    ("Countries like India, Brazil and Indonesia, with growing populations and middle classes.", "@142_s0!"),
    ("Growth can be fast, but so can trouble: politics, currency swings, and weaker investor protection.", "@12_s5"),
    ("Emerging market ETFs spread your money across many countries at once.", "@49_s0"),
    ("Many investors keep them as a smaller slice of a global portfolio.", "@19_s2"),
])

reel(143, [
    ("Before you trust a strategy with real money, test it on the past.",
     "The wolf in a retro-futuristic time machine cockpit watches old charts fly past on screens."),
    ("Backtesting means applying your rules to historical data, to see how they would have performed.", "@143_s0!"),
    ("Clear rules only: entry, exit, stop, size. No decisions made with hindsight.", "@45_s0"),
    ("Beware of overfitting: a strategy tuned perfectly to the past often fails in the future.", "@12_s5"),
    ("A good backtest is a starting point, not a promise.", "@10_s4"),
])

reel(144, [
    ("What if you could practice trading without risking a cent?",
     "The wolf trades on a big screen made of paper, surrounded by paper money and paper coins, playful."),
    ("Paper trading means trading with fake money on real prices.", "@144_s0!"),
    ("It's great for learning how orders work, and for testing a plan.", "@48_s1"),
    ("But fake money doesn't feel like real money. Fear and greed only show up when it's real.", "@13_s6"),
    ("Practice on paper, then start for real with tiny amounts.", "@01_s1"),
])

reel(145, [
    ("Your investment can go up, and you can still lose money. Blame the currency.",
     "The wolf at an airport currency exchange counter looks shocked at a big board of glowing changing currency symbols."),
    ("If you live in Europe and buy US stocks, you're also betting on the dollar.", "@145_s0!"),
    ("If the stock rises ten percent but the dollar falls ten percent against the euro, you're roughly flat.", "@07_s1",
     {"ten percent": "10%"}),
    ("Over long periods, currency moves often even out. In the short term, they can hurt.", "@09_s3"),
    ("Some ETFs are currency hedged to reduce this effect, usually with slightly higher fees.", "@02_s2"),
])

save()
