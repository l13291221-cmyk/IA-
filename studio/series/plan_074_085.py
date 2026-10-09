from build import reel, save

reel(74, [
    ("On January 3rd, 2009, the very first Bitcoin block was created. It's called the genesis block.",
     "A single glowing golden cube floating alone in deep darkness like the first star of the universe, the wolf gazing at it in wonder."),
    ("Satoshi hid a message inside it: a newspaper headline about banks getting a second bailout.",
     "The wolf reads an old newspaper with a dramatic front page on a park bench in London, foggy morning."),
    ("Many see it as a statement: Bitcoin was born as an answer to the 2008 financial crisis.", "@09_s2"),
    ("And the fifty bitcoin reward in that block can never be spent.", "@05_s4", {"fifty": "50"}),
    ("Every Bitcoin block since then links back, one by one, to that very first block.", "@05_s2"),
])

reel(75, [
    ("On May 22nd, 2010, a programmer paid ten thousand bitcoin for two pizzas.",
     "The wolf happily holds two large pizza boxes while handing over a huge sack of golden Bitcoin coins, retro kitchen.",
     {"ten thousand": "10,000"}),
    ("It was one of the first real purchases ever made with Bitcoin.", "@75_s0!"),
    ("At today's prices, those pizzas would be worth hundreds of millions of dollars, or even more.", "@08_s2"),
    ("But without people willing to spend it, Bitcoin might never have become real money.", "@06_s2"),
    ("Today, May 22nd is celebrated every year as Bitcoin Pizza Day.", "@10_s2"),
])

reel(76, [
    ("A stock for under a dollar sounds like a bargain. Usually, it's a trap.", "@08_s0"),
    ("Penny stocks are shares of tiny companies, often under five dollars, sometimes traded outside the major exchanges.",
     "A shady back-alley market stall selling cheap glowing stock certificates from a bargain bin, the wolf frowning.",
     {"five dollars": "$5"}),
    ("They come with little information, low trading volume, and huge price swings.", "@12_s5"),
    ("That makes them perfect for pump and dump schemes.", "@35_s0"),
    ("A low price doesn't mean cheap. Look at the business, not the price tag.", "@61_s2"),
])

reel(77, [
    ("You don't need to buy a whole bitcoin. Most people never do.", "@05_s0"),
    ("One bitcoin can be split into one hundred million smaller units, called satoshis, or sats.",
     "The wolf slices a giant golden Bitcoin into a cloud of countless tiny glowing coins with a laser, amazed.",
     {"one hundred million": "100 million"}),
    ("Most exchanges let you start with just a few dollars.", "@03_s1"),
    ("Stacking sats simply means buying small amounts, regularly.", "@01_s6"),
    ("What matters is the percentage you gain or lose, not whether you own a whole coin.", "@08_s1"),
])

reel(78, [
    ("Bitcoin can be slow and expensive for small payments. The Lightning Network is the fix.",
     "The wolf rides a glowing golden lightning bolt across a night city, sparkling coins trailing behind him."),
    ("Lightning is a second layer built on top of Bitcoin.", "@23_s3"),
    ("Two people open a payment channel, then send many payments instantly, almost for free.", "@33_s2"),
    ("Only the opening and the closing get recorded on the main blockchain.", "@60_s0"),
    ("It's made for small, fast payments, like buying a coffee.",
     "The wolf pays for a coffee at a cozy cafe by tapping his phone on a reader, a tiny lightning bolt sparkling, the barista smiling."),
])

reel(79, [
    ("A stock split makes each share cheaper, but it doesn't make you any richer.", "@13_s3"),
    ("In a four-for-one split, one share becomes four, each worth a quarter of the price.", "@39_s2",
     {"four-for-one": "4-for-1"}),
    ("Apple did exactly that in 2020. Nvidia did a ten-for-one split in 2024.", "@73_s0", {"ten-for-one": "10-for-1"}),
    ("The company's total value stays the same. Only the number of shares changes.", "@07_s1"),
    ("Splits can make shares easier to buy and bring attention, but they don't change the business.", "@40_s4"),
])

reel(80, [
    ("In January 2024, the United States approved spot Bitcoin ETFs. That was huge.",
     "The wolf rings a big golden bell on a stock exchange balcony while confetti and golden Bitcoin coins fly, a crowd cheering below."),
    ("A Bitcoin ETF gives you Bitcoin exposure through a normal brokerage account.", "@03_s1!"),
    ("The fund holds the bitcoin. You hold shares of the fund.", "@05_s4!"),
    ("It's simple and familiar, but you pay a yearly fee, and you don't hold your own keys.", "@21_s0"),
    ("For big institutions, it opened a regulated door into Bitcoin.", "@43_s0"),
])

reel(81, [
    ("After Bitcoin, Ethereum got its turn. Spot Ethereum ETFs started trading in the US in July 2024.", "@80_s0!"),
    ("They work the same way: a fund holds ether, and you buy shares of the fund.", "@49_s0"),
    ("It's a way to follow ether's price without managing a wallet.", "@06_s0"),
    ("One difference: at launch, the US funds didn't include staking rewards.", "@32_s2"),
    ("Same rules apply: check the fees, and know exactly what you're buying.", "@21_s0!"),
])

reel(82, [
    ("Sometimes a company buys back its own shares. It's called a buyback.",
     "The wolf in a suit buys back golden stock certificates from a line of people at a counter, smiling."),
    ("Fewer shares remain, so each one owns a slightly bigger piece of the company.", "@13_s3!"),
    ("It's another way to return money to shareholders, besides dividends.", "@55_s1"),
    ("Apple, for example, has spent hundreds of billions of dollars on buybacks over the years.", "@73_s0!"),
    ("But buybacks at very high prices, or paid for with debt, can destroy value.", "@11_s1"),
])

reel(83, [
    ("Coin or token? People use the words as if they're the same, but they're not.", "@08_s0"),
    ("A coin is native to its own blockchain. Bitcoin on Bitcoin, ether on Ethereum.", "@01_s4"),
    ("A token is built on top of another blockchain, using smart contracts.", "@06_s3"),
    ("Stablecoins, meme coins and most app tokens are actually tokens.", "@35_s1"),
    ("Why it matters: a token depends on the security of the chain it lives on.", "@05_s3"),
])

reel(84, [
    ("Thousands of tokens live on Ethereum, and most follow the same standard: ERC-20.",
     "The wolf inspects a futuristic factory where identical tokens in many colors roll off a conveyor belt, quality control."),
    ("It's a shared set of rules, so every wallet and exchange knows how to handle the token.", "@06_s1"),
    ("That's why you can hold USDT, LINK or UNI in the same Ethereum wallet.", "@03_s1"),
    ("But anyone can create an ERC-20 token in minutes. A standard doesn't mean it's safe.", "@16_s0"),
    ("Always verify the official contract address before buying a token.", "@08_s4!"),
])

reel(85, [
    ("When a private company sells shares to the public for the first time, that's an IPO.", "@80_s0"),
    ("It raises money for the company, and lets early investors cash out.", "@31_s1"),
    ("IPO prices can jump on day one, then slide for months after the hype.", "@14_s1"),
    ("Small investors often get in only after the big first-day jump.",
     "The wolf arrives late at a party where the confetti is already on the floor and the cake is almost gone."),
    ("Many investors wait for a few earnings reports before buying a new IPO.", "@67_s0"),
])

save()
