"""Testi e scene dei reel 02-13 della serie "How to invest in crypto" (inglese)."""
import json
import os

NUM = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
       "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]

R = {}

R[2] = [
    ("In 2022, FTX, one of the biggest crypto exchanges in the world, collapsed in a few days, and customers couldn't withdraw their money.",
     "A huge futuristic crypto exchange building with its glass doors chained shut and padlocked, a crowd of worried people outside, the wolf in front looking up at it with a serious face, dark rainy night.", None),
    ("So here's how to choose a safer exchange. First, check that it's regulated or registered where you live.",
     "The wolf inspects a grand bank-like crypto exchange building with a big magnifying glass, a shiny golden shield emblem on the facade, sunny day.", None),
    ("Second, turn on two-factor authentication the moment you sign up. A password alone is not enough.",
     "The wolf holds a smartphone glowing with a big blue shield and padlock icon, while a hooded hacker silhouette is blocked behind a thick glass wall.", None),
    ("Third, look at the fees. Trading fees, spreads and withdrawal fees add up fast.",
     "The wolf frowns at a very long paper receipt unrolling down to the floor, while small gold coins leak out of a hole in his money bag.", None),
    ("Fourth, test the withdrawal. Send a small amount out before you send anything big.",
     "The wolf carefully drops one single small gold coin into a glowing futuristic transfer tube, watching it travel, focused expression.", None),
    ("And remember: an exchange is a place to buy, not always the best place to store.",
     "The wolf walks out of a crypto exchange building carrying a small steel safe under his arm, confident smile, city street.", None),
]
R[2].append(("Follow for part three: hot wallets versus cold wallets. Not financial advice.",
             "The wolf points at the viewer with a confident grin, holding a flaming smartphone in one hand and an icy frozen hardware wallet in the other.", None))

R[3] = [
    ("Where you keep your crypto matters as much as what you buy.",
     "The wolf stands between two doors: one door on fire and one door covered in ice, thinking with a paw on his chin, neon city corridor.", None),
    ("A hot wallet is an app on your phone or computer. It's connected to the internet, so it's fast and easy to use.",
     "The wolf holds a smartphone that glows bright orange with small flames around it, crypto coins flying out of the screen.", None),
    ("It's great for small amounts you use often, but it's more exposed to hackers and malware.",
     "A shadowy hooded hacker hand reaches out of a laptop screen toward the wolf's glowing phone, the wolf pulls the phone away just in time.", None),
    ("A cold wallet keeps your keys offline, usually on a small hardware device.",
     "The wolf holds a small hardware wallet device covered in frost and ice crystals, cold blue light, snowflakes around.", None),
    ("It's slower to use, but much harder to hack. That's why it's made for long-term savings.",
     "A small hardware wallet resting inside a massive bank vault with a thick round steel door, the wolf guarding the vault with arms crossed.", None),
    ("A simple setup: spending money in a hot wallet, and the rest in cold storage.",
     "The wolf at a desk with a small burning wooden box holding a few coins on the left and a huge icy steel vault full of coins on the right.", None),
    ("Follow for part four: the seed phrase rule nobody should ever break. Not financial advice.",
     "Close-up of the wolf pointing at the viewer, holding an old paper scroll with a glowing golden key drawn on it.", None),
]

R[4] = [
    ("If someone gets these twelve words, your crypto is gone. Forever.",
     "The wolf holds a small paper card with a grid of twelve small blank boxes, looking worried, a dark shadowy thief silhouette lurking behind him.", {"twelve": "12"}),
    ("When you create a wallet, you get a seed phrase: usually twelve or twenty-four words.",
     "The wolf at a desk writing carefully on a small paper card with a pen, a hardware wallet next to it, warm desk lamp.", {"twelve": "12", "twenty-four": "24"}),
    ("Those words are the master key. Anyone who has them can move your coins from anywhere in the world.",
     "A giant glowing golden master key floating above a globe, a sneaky masked thief grabbing it, the wolf shocked.", None),
    ("So never type them into a website. Never send them in a chat. And never save them in a screenshot.",
     "The wolf with arms crossed and a stern face in front of a laptop, a smartphone and a camera, each one with a big red prohibition sign.", None),
    ("No real support team will ever ask for them. If someone does, it's a scam. Every single time.",
     "A fake support agent wearing a smiling mask on a video call on a laptop, the wolf slams the laptop shut with an angry face.", None),
    ("Write them on paper, or stamp them on metal, and keep them somewhere safe.",
     "The wolf stamps letters into a small steel plate with a hammer and metal punch, a home safe open behind him.", None),
    ("Follow for part five: what Bitcoin actually is, explained simply. Not financial advice.",
     "The wolf points at the viewer with a grin while holding a big shiny golden Bitcoin coin, neon city at night.", None),
]

R[5] = [
    ("Bitcoin, explained in under a minute. No tech jargon.",
     "The wolf stands in front of a giant glowing golden Bitcoin coin, holding a stopwatch, confident smile, futuristic city.", None),
    ("Bitcoin is digital money that no bank and no government controls.",
     "The wolf stands on top of a giant floating golden Bitcoin above a city, tiny bank buildings far below, blue sky.", None),
    ("Every transaction is recorded on a public ledger called the blockchain, copied on thousands of computers around the world.",
     "A glowing chain of connected cubes wrapping around planet Earth, linking thousands of small computers, the wolf watching from space.", None),
    ("To cheat, someone would have to overpower most of that network at once. That's what keeps it secure.",
     "A tiny cartoon villain pushing with all his strength against a gigantic glowing wall of servers that doesn't move, the wolf laughing.", None),
    ("And there will only ever be twenty-one million bitcoin. Nobody can print more.",
     "The wolf locks a huge vault filled with a big pile of golden Bitcoin coins, heavy chains and a giant padlock, dramatic light.", {"twenty-one million": "21 million"}),
    ("That fixed supply is why some people call it digital gold. But its price can still swing a lot, so it's a high-risk investment.",
     "The wolf holds a shiny gold bar in one paw and a golden Bitcoin in the other, balancing them like a scale, while a stormy price chart rages behind him.", None),
    ("Follow for part six: Ethereum, and why it's not just another coin. Not financial advice.",
     "The wolf points at the viewer with a confident grin, a glowing purple-blue Ethereum crystal floating next to him.", None),
]

R[6] = [
    ("If Bitcoin is digital gold, Ethereum is a world computer.",
     "The wolf stands in front of a gigantic glowing Ethereum diamond crystal that works like a futuristic supercomputer with cables and lights.", None),
    ("Ethereum is a blockchain that can run programs, called smart contracts.",
     "The wolf types on a holographic keyboard while glowing code blocks fly into a big Ethereum crystal, futuristic lab.", None),
    ("A smart contract works like a vending machine: put in the right input, and it automatically gives you the result. No middleman.",
     "The wolf inserts a coin into a sleek futuristic vending machine and a glowing package drops out automatically, no shopkeeper around.", None),
    ("That's how apps for lending, trading and digital collectibles run on Ethereum.",
     "A floating futuristic city of small app buildings sitting on top of a giant Ethereum diamond platform, the wolf flying above with a jetpack.", None),
    ("Its coin, ether, pays the fees to use the network. Those fees are called gas.",
     "The wolf at a futuristic gas station filling up a sports car with glowing purple fuel shaped like the Ethereum diamond.", None),
    ("In 2022, Ethereum switched to proof of stake and cut its energy use by more than ninety-nine percent.",
     "The wolf plants a small green tree next to a glowing green Ethereum diamond, a huge old power plant shutting down in the background.", {"ninety-nine percent": "99%"}),
    ("Follow for part seven: stablecoins, the crypto that's not supposed to move. Not financial advice.",
     "The wolf points at the viewer with a grin, a calm green coin with a dollar sign floating perfectly still next to him.", None),
]

R[7] = [
    ("Not all crypto goes up and down. Some coins are designed to stay at one dollar.",
     "The wolf balances a shiny green coin with a dollar sign perfectly on one fingertip, while other coins bounce wildly around him.", {"one dollar": "$1"}),
    ("They're called stablecoins, like USDT and USDC. One coin aims to always equal one US dollar.",
     "A perfectly balanced scale with a green dollar-sign coin on one side and a paper dollar bill on the other, the wolf nodding.", {"one US dollar": "$1"}),
    ("Traders use them to park money between trades, without leaving crypto.",
     "The wolf parks a sports car shaped like a big green coin in a neon parking garage, relaxed.", None),
    ("Most are backed by reserves, like cash and treasury bills, held by the issuing company.",
     "A big bank vault with neat stacks of cash and documents, an auditor with a clipboard checking them, the wolf watching.", None),
    ("But stable doesn't mean risk-free. In 2022, TerraUSD lost its peg and collapsed to almost zero.",
     "A cracked coin falling off a cliff edge into darkness, the wolf on the edge with a shocked face.", None),
    ("So stick to the biggest, most transparent ones, and don't keep everything in a single stablecoin.",
     "The wolf calmly places coins into several different baskets lined up on a table.", None),
    ("Follow for part eight: why a cheap coin is not a cheap investment. Not financial advice.",
     "The wolf points at the viewer with a grin, holding a tiny penny-like coin with a magnifying glass.", None),
]

R[8] = [
    ("A coin that costs one cent is not cheaper than a coin that costs fifty thousand dollars.",
     "The wolf holds a tiny copper coin in one paw and a giant golden coin in the other, raising an eyebrow, neon city.", {"one cent": "1¢", "fifty thousand dollars": "$50,000"}),
    ("Price alone tells you almost nothing. What matters is the market cap: the price, times the number of coins.",
     "The wolf with a big calculator, multiplying a small coin by a huge mountain of coins, numbers floating as glowing symbols without text.", None),
    ("A coin at one cent, with a trillion coins in circulation, is already worth ten billion dollars.",
     "A gigantic mountain of tiny copper coins as tall as skyscrapers, the wolf looking up at it in awe.", {"one cent": "1¢", "a trillion": "1 trillion", "ten billion dollars": "$10 billion"}),
    ("To reach just one dollar, it would need to be worth a trillion dollars. Only a handful of companies on Earth are worth that much.",
     "A tiny copper coin trying to climb an impossibly tall ladder reaching into the clouds, the wolf laughing at the bottom.", {"one dollar": "$1", "a trillion dollars": "$1 trillion"}),
    ("So before you buy, check the market cap and the total supply, not just the price.",
     "The wolf reads a tablet with a magnifying glass, looking smart and careful, desk with coins.", None),
    ("Follow for part nine: bull markets and bear markets, explained. Not financial advice.",
     "The wolf points at the viewer with a grin, a golden bull and a big brown bear standing behind him.", None),
]

R[9] = [
    ("Crypto moves in big seasons. Knowing which one you're in changes everything.",
     "The wolf stands at a crossroads, on the left a sunny golden path with a charging bull, on the right a stormy path with a bear.", None),
    ("A bull market is when prices rise for months. Everyone is excited, and everyone feels like a genius.",
     "The wolf rides a charging golden bull through a city street full of confetti and cheering crowds.", None),
    ("A bear market is when prices fall for months. People give up and say crypto is dead.",
     "A big grumpy bear sitting on top of a red falling chart in the rain, the wolf standing calmly under an umbrella.", None),
    ("Bitcoin has gone through several of these cycles, with drops of seventy percent or more along the way.",
     "The wolf hikes across a huge mountain range shaped like a price chart with high peaks and deep valleys.", {"seventy percent": "70%"}),
    ("The classic mistake: buying with excitement at the top, and selling in fear at the bottom.",
     "Split scene: on the left the wolf happily buying at a mountain peak, on the right the same wolf crying at the bottom of a valley.", None),
    ("Patient investors often do the opposite. They keep buying slowly when everyone else is scared.",
     "The wolf calmly stacks gold coins while a crowd of panicking people runs away in the background.", None),
    ("Follow for part ten: the Bitcoin halving. Not financial advice.",
     "The wolf points at the viewer with a grin, a golden Bitcoin cut perfectly in half floating behind him.", None),
]

R[10] = [
    ("Every four years or so, Bitcoin cuts its own supply of new coins in half. It's called the halving.",
     "A giant golden Bitcoin being sliced perfectly in half by a bright laser beam, the wolf watching with sunglasses.", None),
    ("New bitcoin are created as a reward for the miners who secure the network.",
     "Cartoon miners with pickaxes inside a glowing digital mine extracting shiny Bitcoin coins, the wolf supervising with a hard hat.", None),
    ("About every four years, that reward is cut in half. The last halving was in April 2024.",
     "The wolf holds a big calendar page and a golden coin cut in half, celebrating with confetti.", None),
    ("So fewer new coins enter the market every single day.",
     "A golden faucet slowly dripping fewer and fewer Bitcoin coins into a bucket, the wolf watching closely.", None),
    ("In the past, big bull markets came in the months after a halving. But past results don't guarantee future ones.",
     "The wolf looks skeptically at an old rising chart on a dusty screen, scratching his head.", None),
    ("And around the year 2140, the last bitcoin will be mined. After that, no new ones, ever.",
     "A far-future city in the year 2140 with flying cars, the very last golden Bitcoin falling into a jar, the wolf old with grey beard smiling.", None),
    ("Follow for part eleven: leverage, the fastest way to lose everything. Not financial advice.",
     "The wolf points at the viewer with a serious look, a huge dangerous red lever behind him.", None),
]

R[11] = [
    ("Leverage can make you rich in a day, and broke in an hour.",
     "The wolf pulls a giant red lever on a machine, half of the scene full of flying money, the other half empty and dark.", None),
    ("With leverage, you borrow money to trade bigger. Ten times leverage means a hundred dollars controls a thousand.",
     "The wolf tries to lift a gigantic barbell with tiny shaking arms, sweating.", {"Ten times": "10x", "a hundred dollars": "$100", "a thousand": "$1,000"}),
    ("Sounds great when the price goes up. But if it drops just ten percent, your whole position can be wiped out.",
     "The glass floor under the wolf's feet cracks and shatters, the wolf panicking.", {"ten percent": "10%"}),
    ("That's called liquidation. The exchange closes your trade, and your money is gone.",
     "A giant robotic arm sweeps a pile of gold coins off a table into a trash can, the wolf screaming.", None),
    ("Crypto can easily move ten percent in a single day. With high leverage, a normal move becomes a total loss.",
     "The wolf on a tiny surfboard being swept away by a gigantic red wave shaped like a price chart.", {"ten percent": "10%"}),
    ("If you're a beginner, the simplest rule is: no leverage. Only buy what you can actually pay for.",
     "The wolf cuts a rope with scissors that tied him to a giant red balloon, landing safely on the ground, relieved.", None),
    ("Follow for part twelve: the stop loss, your seatbelt in trading. Not financial advice.",
     "The wolf points at the viewer with a grin while fastening a seatbelt in a futuristic car.", None),
]

R[12] = [
    ("Would you drive without a seatbelt? Then don't trade without a stop loss.",
     "The wolf in a sports car fastening his seatbelt with a confident face, neon city highway at night.", None),
    ("A stop loss is an order that sells automatically if the price falls to a level you choose.",
     "The wolf walks on a tightrope high above the city with a big safety net stretched below him.", None),
    ("You decide in advance how much you're willing to lose. For example, five percent.",
     "The wolf draws a thick red horizontal line on a big trading screen with a marker, focused.", {"five percent": "5%"}),
    ("If the price hits that level, you're out. Small loss, no drama, no hoping.",
     "The wolf falls from the tightrope and lands safely and softly in the safety net, giving a thumbs up.", None),
    ("Without one, a small loss can turn into a huge one while you're asleep.",
     "The wolf sleeping peacefully in bed while a huge red chart crashes on a giant screen behind him.", None),
    ("Just don't set it too tight, or normal price swings will kick you out of good trades.",
     "The wolf wobbling on an extremely thin thread, about to fall, nervous face.", None),
    ("Follow for part thirteen: taking profit, and why you need an exit plan. Not financial advice.",
     "The wolf points at the viewer with a grin, standing next to a glowing green exit door.", None),
]

R[13] = [
    ("Making money in crypto is the easy part. Keeping it is the hard part.",
     "The wolf holds a bag of gold coins tightly while coins slip through a hole in the bottom, worried face.", None),
    ("Many people watched their coins double, waited for more, and gave it all back in the next crash.",
     "The wolf watches sadly as a big balloon made of money floats away into the sky.", None),
    ("That's why you need an exit plan before you even buy.",
     "The wolf draws a treasure-map-style plan on a big table with an arrow pointing to a door, planning carefully.", None),
    ("A simple one: sell a part at each target. For example, a quarter at two x, and another quarter at three x.",
     "The wolf cuts a big golden cake shaped like a coin into four equal slices with a knife.", {"two x": "2x", "three x": "3x"}),
    ("You lock in real gains, and you still keep some coins if the price keeps going up.",
     "The wolf puts gold coins into a safe with one paw while still holding a few coins in the other, smiling.", None),
    ("Nobody sells at the exact top. The goal is to sell some, not to be perfect.",
     "The wolf climbs a mountain and plants small flags at different heights on the way up, happy.", None),
    ("Follow for part fourteen: FOMO and FUD, the two emotions that empty wallets. Not financial advice.",
     "The wolf points at the viewer with a grin, two cartoon emotion clouds behind him: one excited and one scared.", None),
]

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan.json")
    plan = json.load(open(out)) if os.path.exists(out) else {}
    for n, scenes in R.items():
        plan[str(n)] = {"part": n, "intro_say": f"How to invest in crypto. Part {NUM[n]}.",
                        "scenes": [{"say": s, "p": p, **({"show": sh} if sh else {})} for s, p, sh in scenes]}
    json.dump(plan, open(out, "w"), indent=1, ensure_ascii=False)
    print("parts:", sorted(int(k) for k in plan))
