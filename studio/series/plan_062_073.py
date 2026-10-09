from build import reel, save

reel(62, [
    ("Blockchains rely on a kind of digital fingerprint, called a hash.",
     "The wolf looks through a big magnifying glass at a giant glowing fingerprint made of light, futuristic lab."),
    ("A hash function turns any data into a fixed-length code. Same input, same code, every time.", "@06_s2"),
    ("Change even one letter, and the code changes completely.", "@62_s0!"),
    ("And you can't run it backwards. From the code, you can't recover the original data.", "@04_s3"),
    ("That's how blocks are linked together, and how Bitcoin mining works.", "@10_s1"),
])

reel(63, [
    ("Your crypto wallet runs on two keys. Mix them up, and you could lose everything.", "@04_s2"),
    ("The public key is like your email address. You can share it, so people can send you coins.",
     "The wolf hands out business cards with a glowing blue key symbol to friendly people, smiling."),
    ("The private key is like the password to that email. Whoever has it controls your funds.", "@04_s0"),
    ("Your seed phrase is a human-readable backup of your private keys.", "@04_s1"),
    ("Share the public one freely. Never, ever share the private one.", "@04_s3"),
])

reel(64, [
    ("A company can sell billions and still lose money. Here's why.",
     "A huge river of gold coins flows into a company building while most of the coins leak out of holes in the back wall, the wolf watching worried."),
    ("Revenue is all the money that comes in from sales.", "@30_s1"),
    ("Profit is what's left after paying for everything: staff, materials, rent, taxes and interest.", "@02_s3"),
    ("A fast-growing company may have huge revenue and no profit yet, because it's investing to grow.", "@40_s4"),
    ("Healthy businesses eventually turn revenue into real, growing profit. That's what investors watch.", "@27_s1!"),
])

reel(65, [
    ("That long string of letters and numbers is your wallet address. Here's what it really is.",
     "The wolf stands next to a futuristic glowing mailbox engraved with a very long code, holding a gold coin like a letter."),
    ("It's derived from your public key, and it's where people send you crypto.", "@63_s1"),
    ("Each blockchain has its own address format. A Bitcoin address is not an Ethereum address.", "@22_s1"),
    ("Anyone can see the balance and history of an address on the blockchain. It's public.", "@05_s2"),
    ("Always double-check the first and last characters before you send.", "@08_s4"),
])

reel(66, [
    ("You sent crypto, and it still says pending. Why does it take time?", "@01_s3"),
    ("A transaction becomes real when it's included in a block. That's the first confirmation.", "@60_s0"),
    ("Each new block added on top is another confirmation, and makes reversing it harder.",
     "The wolf stacks glowing transparent cubes one on top of another into a tall, stable tower."),
    ("That's why exchanges often wait for several confirmations before crediting your deposit.", "@02_s4"),
    ("And when the network is busy, paying a higher fee can get you into a block faster.", "@23_s2"),
])

reel(67, [
    ("Four times a year, companies reveal their results, and the stock can jump or crash overnight.",
     "The wolf stands at a podium on a stage presenting a big glowing report while a crowd of investors holds its breath."),
    ("An earnings report shows revenue, profit, and what the company expects for the future.", "@38_s0"),
    ("The stock reacts to the numbers versus expectations, not just to whether they're good or bad.", "@07_s1"),
    ("Great results can still sink a stock if investors expected even more.", "@01_s0"),
    ("So if you hold a stock, know its earnings dates. Volatility often spikes around them.", "@10_s2"),
])

reel(68, [
    ("Bitcoin is secured by computers playing a giant guessing game. It's called proof of work.", "@10_s1"),
    ("Miners race to find a special number that gives the block a hash below a target.",
     "Rows of glowing mining machines in a huge warehouse, fans spinning, the wolf walking between them with a clipboard."),
    ("Finding it takes enormous computing power, but anyone can check the answer instantly.", "@62_s0"),
    ("The winner adds the next block and earns new bitcoin, plus the transaction fees.", "@10_s1!"),
    ("To attack the network, you'd need more computing power than all the honest miners combined.", "@05_s3"),
])

reel(69, [
    ("There are two main ways to secure a blockchain: proof of work, and proof of stake.",
     "The wolf stands between a noisy industrial mining machine on the left and a calm glowing vault of locked coins on the right."),
    ("Proof of work uses energy and machines. Security comes from the cost of computing.", "@68_s1"),
    ("Proof of stake uses locked coins. Validators put their own money at risk to verify blocks.", "@05_s4"),
    ("Cheat in proof of stake, and you can lose part of your stake. It's called slashing.", "@11_s3"),
    ("Bitcoin uses proof of work. Ethereum switched to proof of stake in 2022.", "@06_s5"),
])

reel(70, [
    ("There are two classic styles of stock investing: growth, and value.", "@09_s0"),
    ("Growth stocks are companies expanding fast. Investors pay high prices for future potential.", "@31_s1"),
    ("Value stocks look cheap compared to their profits or assets. Often boring, sometimes overlooked.",
     "The wolf finds a dusty treasure chest full of gold in a quiet old antique shop that everyone else ignores."),
    ("Growth can win big in good times, but falls hard when expectations drop.", "@01_s2"),
    ("Value can lag for years, then shine. Many investors simply own some of both.", "@07_s5"),
])

reel(71, [
    ("Sometimes a blockchain splits in two. It's called a fork.",
     "A glowing chain of cubes splits into two separate branches like a fork in a road, the wolf standing at the split point."),
    ("A soft fork is a backward-compatible upgrade. Old software still works with the new rules.", "@06_s1"),
    ("A hard fork changes the rules in a way old software can't follow. If people disagree, you get two chains.", "@71_s0!"),
    ("That's how Bitcoin Cash was born in 2017, splitting away from Bitcoin.", "@10_s0"),
    ("If you held coins before a split, you usually ended up with coins on both chains.", "@13_s3"),
])

reel(72, [
    ("Bitcoin's creator is still a mystery. The name: Satoshi Nakamoto.",
     "A mysterious hooded figure with no visible face stands in the fog holding a glowing golden Bitcoin, the wolf watching from a distance."),
    ("In 2008, Satoshi published the Bitcoin whitepaper, and in early 2009, launched the network.", "@38_s0"),
    ("Satoshi worked with early developers online, then disappeared around 2011.", "@72_s0!"),
    ("The coins believed to be Satoshi's, estimated at around one million bitcoin, have never moved.", "@05_s4",
     {"one million": "1 million"}),
    ("No leader, no CEO, no company. Maybe that's exactly the point.", "@05_s1"),
])

reel(73, [
    ("Blue chip stocks are the giants: big, established companies with long track records.",
     "The wolf stands among towering skyscrapers of grand corporate headquarters, looking up, sunny day."),
    ("The name comes from poker, where the blue chips had the highest value.",
     "The wolf at a poker table stacking shiny blue poker chips, warm casino lights."),
    ("They usually have strong brands, steady profits, and often pay dividends.", "@55_s1"),
    ("They're generally less volatile than small companies, but not risk-free. Giants can fall too.", "@07_s4"),
    ("Many investors use them as the solid core of a portfolio.", "@19_s0"),
])

save()
