from build import reel, save

reel(50, [
    ("You clicked buy at one price, but you paid more. That's slippage.",
     "The wolf slips on a banana peel while carrying a gold coin, the coin flying out of his paws, comic style, city street."),
    ("Slippage is the difference between the price you expect and the price you actually get.", "@07_s1!"),
    ("It happens when the price moves fast, or when there aren't enough buyers and sellers at your price.", "@48_s1"),
    ("Small coins with low liquidity can have huge slippage, especially on decentralized exchanges.", "@34_s0"),
    ("The fixes: use limit orders, trade liquid pairs, and split big orders into smaller ones.", "@48_s2"),
])

reel(51, [
    ("Every exchange keeps a live list of who wants to buy and who wants to sell. It's called the order book.",
     "The wolf reads a giant glowing ledger book with green entries on the left page and red entries on the right page, futuristic hall."),
    ("On one side, the bids: buyers, and the prices they're willing to pay.", "@30_s1"),
    ("On the other side, the asks: sellers, and the prices they want.", "@30_s1!"),
    ("The gap between the best bid and the best ask is called the spread.", "@26_s0"),
    ("A thick order book means you can trade big amounts without moving the price much.", "@08_s2"),
])

reel(52, [
    ("In 2008, Warren Buffett made a ten-year bet: a simple S&P 500 index fund against hedge funds picked by professionals.",
     "A wise old investor with glasses shakes hands with a group of sharp fund managers over a huge golden trophy, the wolf watching, cartoon style.",
     {"ten-year": "10-year"}),
    ("The professionals charged high fees and tried to beat the market.", "@21_s0"),
    ("The index fund simply held the whole market, with tiny fees.", "@49_s0"),
    ("After ten years, the index fund won, by a wide margin.", "@10_s2"),
    ("The lesson: low costs and patience often beat clever stock picking.", "@31_s5"),
])

reel(53, [
    ("There are two kinds of crypto exchanges, and they work very differently.", "@03_s0"),
    ("A centralized exchange is a company. It holds your coins, matches orders, and usually has customer support.", "@02_s1"),
    ("It's easier for beginners, but you're trusting that company with your money.", "@02_s0"),
    ("A decentralized exchange is a set of smart contracts. You trade directly from your own wallet.", "@33_s2"),
    ("More control, but no help desk, and you're responsible for every click.", "@10_s4!"),
])

reel(54, [
    ("Why does a crypto app want a photo of your passport?",
     "The wolf holds up his passport next to his face while a smartphone camera scans him, slightly annoyed."),
    ("It's called KYC: know your customer. Regulated exchanges must verify who their users are.", "@02_s1!"),
    ("It's there to fight money laundering, fraud, and stolen funds.", "@15_s0"),
    ("The downside: your data is stored by the company, so choose exchanges with a strong security record.", "@02_s2"),
    ("And be careful: real exchanges ask for ID inside their official app, never through a random link or chat.", "@17_s0"),
])

reel(55, [
    ("Some stocks pay you just for holding them. Those payments are called dividends.", "@32_s0"),
    ("A company makes a profit and sends part of it to its shareholders, often every three months.",
     "The wolf opens his mailbox and finds an envelope full of gold coins, happy, sunny suburban street."),
    ("The dividend yield is the yearly dividend divided by the stock price.", "@08_s1"),
    ("Mature companies, like utilities or big consumer brands, often pay steady dividends.", "@40_s4"),
    ("But a very high yield can be a warning sign. Sometimes it's high only because the price crashed.", "@15_s1!"),
])

reel(56, [
    ("After FTX, a big question: does your exchange actually have your money?", "@02_s0!"),
    ("Proof of reserves is a way for an exchange to show it holds enough assets to cover customer balances.", "@07_s3"),
    ("Usually, it publishes wallet addresses and a cryptographic check of user balances.", "@05_s2"),
    ("But it's only a snapshot. It may not show all the debts the exchange owes.",
     "The wolf takes a photo of a neat vault with an old camera, while behind the vault wall a giant pile of unpaid bills is hidden."),
    ("It's a good sign, not a guarantee. Don't keep more on an exchange than you need.", "@02_s5"),
])

reel(57, [
    ("In 2014, the biggest Bitcoin exchange in the world collapsed. Its name was Mt. Gox.", "@02_s0"),
    ("At its peak, it handled most of the world's Bitcoin trading.", "@30_s1"),
    ("Then it announced that around eight hundred fifty thousand bitcoin were missing, lost to hackers and mismanagement.",
     "An empty giant vault with a broken door, dust and a few scattered coins on the floor, the wolf standing inside with a flashlight, shocked.",
     {"eight hundred fifty thousand": "850,000"}),
    ("Customers waited about ten years before repayments finally began.", "@10_s5"),
    ("The lesson crypto keeps teaching: not your keys, not your coins.", "@03_s4"),
])

reel(58, [
    ("What you do with your dividends can matter more than the dividends themselves.", "@55_s1"),
    ("Instead of spending them, you can use them to buy more shares, automatically.", "@01_s6"),
    ("More shares pay more dividends, which buy even more shares. That's compounding.",
     "A snowball made of gold coins rolls down a snowy hill growing bigger and bigger, the wolf running beside it cheering."),
    ("Over decades, reinvested dividends have made up a big part of total stock market returns.", "@27_s1"),
    ("Many brokers offer a DRIP, a dividend reinvestment plan, often with no extra fees.", "@03_s1"),
])

reel(59, [
    ("Who really holds your crypto? The answer decides who's in control.", "@04_s2"),
    ("With a custodial wallet, a company holds your keys. Like a bank account: easy, but they control access.", "@02_s1"),
    ("With a non-custodial wallet, only you hold the keys. Full control, and full responsibility.", "@04_s1"),
    ("If the company freezes withdrawals or goes bust, custodial users can lose access.", "@02_s0"),
    ("Lose your seed phrase in a non-custodial wallet, and nobody can help you.", "@04_s0"),
])

reel(60, [
    ("Everyone talks about the blockchain. But what is a block, really?",
     "The wolf holds a glowing transparent cube filled with tiny paper receipts, examining it curiously."),
    ("A block is a bundle of transactions. Like a page in a giant shared notebook.", "@38_s0"),
    ("Each block contains a fingerprint of the previous one. That's what links them into a chain.", "@05_s2"),
    ("Change one old transaction, and every block after it breaks. That's why history is so hard to rewrite.", "@05_s3"),
    ("On Bitcoin, a new block is added about every ten minutes.", "@05_s0", {"ten minutes": "10 minutes"}),
])

reel(61, [
    ("Is a stock expensive or cheap? One quick number gives a first clue: the P/E ratio.", "@08_s0"),
    ("P/E means price to earnings: the share price divided by the profit per share.", "@08_s1"),
    ("A P/E of twenty means investors pay twenty dollars for every dollar of yearly profit.",
     "The wolf at a shop counter pays a tall stack of gold coins to buy one single small gold coin, thinking hard.",
     {"twenty dollars": "$20", "twenty": "20"}),
    ("Fast-growing companies often have high P/Es. Slow, mature ones usually have lower ones.", "@27_s1"),
    ("Compare P/Es within the same industry, and never use it as your only reason to buy.", "@08_s4"),
])

save()
