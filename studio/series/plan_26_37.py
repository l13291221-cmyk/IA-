"""Testi e scene dei reel 26-37 della serie "How to invest in crypto" (inglese)."""
import json
import os

NUM = {26: "twenty-six", 27: "twenty-seven", 28: "twenty-eight", 29: "twenty-nine", 30: "thirty",
       31: "thirty-one", 32: "thirty-two", 33: "thirty-three", 34: "thirty-four", 35: "thirty-five",
       36: "thirty-six", 37: "thirty-seven"}

R = {}

R[26] = [
    ("Most people draw these two lines wrong. Support and resistance.",
     "The wolf stands between a glowing green floor below and a glowing red ceiling above, a price chart bouncing between them.", None),
    ("Support is a price zone where buyers keep stepping in. Like a floor the price bounces off.",
     "A bouncing golden ball hitting a glowing green floor and bouncing back up, the wolf watching with a clipboard.", None),
    ("Resistance is a zone where sellers keep showing up. Like a ceiling the price hits its head on.",
     "A golden ball hitting a glowing red ceiling and falling back down, the wolf wincing.", None),
    ("They're zones, not exact prices. Draw a thick band, not a thin line.",
     "The wolf paints a thick glowing band across a big chart screen with a wide paint roller.", None),
    ("And when resistance finally breaks, it often turns into the new support.",
     "The golden ball smashes through the red ceiling, which turns green and becomes the new floor, the wolf cheering.", None),
    ("But no level holds forever. Always have a plan if it breaks the wrong way.",
     "The green floor cracks under the golden ball, the wolf ready with a parachute.", None),
    ("Follow for part twenty-seven: how to spot a trend. Not financial advice.",
     "The wolf points at the viewer with a grin, a staircase going upward behind him.", None),
]

R[27] = [
    ("Fighting the trend is one of the fastest ways to lose money.",
     "The wolf tries to swim upstream against a powerful river current, exhausted.", None),
    ("In an uptrend, the price makes higher highs and higher lows. Like a staircase going up.",
     "The wolf climbs a glowing golden staircase that zigzags upward into the sky.", None),
    ("In a downtrend, it's the opposite: lower highs and lower lows. A staircase going down.",
     "The wolf walks carefully down a dark red staircase going down into a foggy basement.", None),
    ("And when it moves sideways between the same levels, that's a range. No clear trend.",
     "The wolf walks back and forth in a long flat corridor between two walls, bored.", None),
    ("A simple rule: in an uptrend, look for buys near the lows. Don't short a rocket.",
     "The wolf tries to stop a launching rocket with his paws and gets blasted back, comic style.", None),
    ("Trends can change, so always use a stop loss in case you're wrong.",
     "The wolf on the staircase with a safety harness rope attached, confident.", None),
    ("Follow for part twenty-eight: moving averages, made simple. Not financial advice.",
     "The wolf points at the viewer with a grin, a smooth glowing curved line behind him.", None),
]

R[28] = [
    ("Price charts look messy. Moving averages clean them up.",
     "The wolf with a vacuum cleaner cleaning up a messy zigzag chart, leaving a smooth glowing line.", None),
    ("A moving average is the average price over the last few days, updated every day.",
     "The wolf on a moving walkway holding a smooth glowing line, calendar pages flying by.", None),
    ("Two famous ones are the fifty-day and the two-hundred-day averages.",
     "Two smooth glowing lines of different colors racing like snakes across a giant chart, the wolf as race commentator.", {"fifty-day": "50-day", "two-hundred-day": "200-day"}),
    ("When the price is above the two-hundred-day average, the long-term trend is usually considered healthy.",
     "The wolf sunbathing happily on top of a calm glowing line, sunny sky.", {"two-hundred-day": "200-day"}),
    ("When the fifty crosses above the two hundred, traders call it a golden cross. Below is a death cross.",
     "Two glowing lines crossing in an X, one side shines golden, the other side dark with a skull-shaped cloud, the wolf pointing.", {"fifty": "50", "two hundred": "200"}),
    ("But moving averages are slow. They confirm moves, they don't predict them.",
     "The wolf watches a sleepy turtle carrying a glowing line, smiling patiently.", None),
    ("Follow for part twenty-nine: the RSI indicator. Not financial advice.",
     "The wolf points at the viewer with a grin, holding a speedometer gauge.", None),
]

R[29] = [
    ("This indicator tells you when the market might be running too hot. It's called the RSI.",
     "The wolf looks at a giant glowing speedometer gauge with the needle in the red zone, steam coming out.", None),
    ("The RSI measures how strong recent moves were, on a scale from zero to one hundred.",
     "The wolf points at a giant gauge going from green to red, like a teacher.", {"zero": "0", "one hundred": "100"}),
    ("Above seventy is usually called overbought. The price went up fast, maybe too fast.",
     "A rocket overheating with flames and steam, the wolf holding a fire extinguisher.", {"seventy": "70"}),
    ("Below thirty is called oversold. The price fell fast, maybe too fast.",
     "A deflated balloon lying on the ground, the wolf gently pumping air into it.", {"thirty": "30"}),
    ("But careful: in strong trends, the RSI can stay overbought or oversold for weeks.",
     "The speedometer needle stuck in the red zone while a car keeps accelerating, the wolf surprised.", None),
    ("Use it as a warning light, never as a buy or sell button on its own.",
     "A car dashboard with a glowing warning light, the wolf driving carefully.", None),
    ("Follow for part thirty: why volume matters. Not financial advice.",
     "The wolf points at the viewer with a grin, a giant volume knob behind him.", None),
]

R[30] = [
    ("A price move without volume is like a party with no guests.",
     "The wolf alone at a big party with balloons and music, the room completely empty, awkward.", None),
    ("Volume is how much of a coin was traded in a period of time.",
     "A busy futuristic marketplace full of people trading glowing coins, the wolf counting them.", None),
    ("When the price breaks out with high volume, a lot of people agree with the move.",
     "A huge crowd pushing a giant golden coin up a hill together, the wolf leading them.", None),
    ("When it breaks out on low volume, it's often a fake move that fades quickly.",
     "A lonely little coin trying to push a giant boulder up a hill and failing, the wolf shaking his head.", None),
    ("Huge volume after a long drop can mean panic selling, and sometimes, the end of the fall.",
     "A stampede of panicking cartoon people running down a hill, at the bottom the wolf calmly waiting with a basket.", None),
    ("Price tells you what happened. Volume tells you how much conviction was behind it.",
     "The wolf holding a giant megaphone, sound waves glowing, confident pose.", None),
    ("Follow for part thirty-one: lump sum or DCA, which one wins? Not financial advice.",
     "The wolf points at the viewer with a grin, a big bag of money on one side and a jar of coins on the other.", None),
]

R[31] = [
    ("You have money to invest. All at once, or a little at a time?",
     "The wolf stands at a fork: on one side a giant bag of money, on the other a calendar with a small coin jar.", None),
    ("Investing all at once is called lump sum. If the price goes up after, you win the most.",
     "The wolf throws a giant bag of money into a rocket that launches upward, cheering.", None),
    ("But if it drops right after, you feel every bit of that fall.",
     "The same wolf falling with his bag of money down a steep red slide, screaming.", None),
    ("DCA means splitting it into equal parts and buying on a fixed schedule.",
     "The wolf drops one coin into a jar every week, a calendar with checkmarks behind him, calm.", None),
    ("You might miss part of a rally, but you avoid going all in at the worst moment.",
     "The wolf on a gentle staircase while another character jumps off a cliff, the wolf smiling calmly.", None),
    ("In volatile markets like crypto, many people pick DCA simply because it's easier to stick with.",
     "The wolf sleeping peacefully on a hammock next to a slowly filling coin jar.", None),
    ("Follow for part thirty-two: staking, and how it really works. Not financial advice.",
     "The wolf points at the viewer with a grin, planting a gold coin in the ground like a seed.", None),
]

R[32] = [
    ("Can your crypto earn more crypto while you sleep? That's the idea behind staking.",
     "The wolf sleeps in bed while small gold coins pop out of a plant pot next to him.", None),
    ("Some blockchains, like Ethereum, use proof of stake. Validators lock up coins to help secure the network.",
     "The wolf locks gold coins into a glowing vault that powers a big blockchain machine.", None),
    ("In return, they earn rewards in new coins. You can join through an exchange or a staking service.",
     "Small gold coins grow on a tree, the wolf harvesting them into a basket.", None),
    ("But there are risks. Your coins may be locked for a while, and you can't sell quickly.",
     "The wolf tries to open a locked vault with a timer counting down, impatient.", None),
    ("The coin's price can drop more than the rewards you earn.",
     "The wolf holds a small basket of new coins while a big pile of coins melts behind him.", None),
    ("And if you stake through a platform, you're trusting that platform with your coins.",
     "The wolf hands his coins to a robot butler, looking slightly worried.", None),
    ("Follow for part thirty-three: DeFi, finance without banks. Not financial advice.",
     "The wolf points at the viewer with a grin, a futuristic bank with no walls behind him.", None),
]

R[33] = [
    ("What if you could lend, borrow and trade without a bank? That's DeFi.",
     "The wolf stands in a futuristic open-air bank with no walls and no bankers, glowing machines doing the work.", None),
    ("DeFi means decentralized finance: apps built on blockchains that run with smart contracts.",
     "Glowing transparent machines connected by chains of light, coins flowing through them, the wolf observing.", None),
    ("On a decentralized exchange, you swap coins directly from your own wallet.",
     "The wolf swaps a gold coin for a silver coin through a glowing portal from his own wallet, no clerk in sight.", None),
    ("On lending apps, you can deposit coins to earn interest, or borrow against your crypto.",
     "The wolf deposits coins into a glowing machine that drips small coins back to him.", None),
    ("The risk: smart contracts can have bugs, and hacks have stolen billions over the years.",
     "A hacker character pulling a thread that unravels a glowing machine, coins spilling out, the wolf shocked.", None),
    ("And there's no customer support to call if you make a mistake. Start small, and learn first.",
     "The wolf alone in front of a closed help desk with a cobweb, scratching his head.", None),
    ("Follow for part thirty-four: liquidity pools and impermanent loss. Not financial advice.",
     "The wolf points at the viewer with a grin, standing next to a swimming pool full of gold coins.", None),
]

R[34] = [
    ("Ever wondered where decentralized exchanges get their coins? From liquidity pools.",
     "The wolf stands next to a big swimming pool filled with gold and silver coins instead of water.", None),
    ("A liquidity pool is a pot of two coins that traders swap against. Users like you fill it.",
     "Several cartoon people pouring gold and silver coins into a big pool, the wolf supervising.", None),
    ("In return, you earn a share of the trading fees.",
     "The wolf relaxes on an inflatable in the coin pool while small coins drop on him from above.", None),
    ("But there's a catch called impermanent loss. When one coin's price moves a lot, the pool rebalances.",
     "A giant balance scale tipping over in the pool, coins sliding from one side to the other, the wolf surprised.", None),
    ("You can end up with less value than if you had simply held both coins.",
     "Two piles of coins side by side, the pool pile smaller than the held pile, the wolf comparing them sadly.", None),
    ("Fees can make up for it, or not. Understand the math before you jump in.",
     "The wolf at the edge of the coin pool with a calculator before diving, thinking.", None),
    ("Follow for part thirty-five: the truth about meme coins. Not financial advice.",
     "The wolf points at the viewer with a grin, a cartoon dog-faced coin with a party hat next to him.", None),
]

R[35] = [
    ("Meme coins can go up a thousand percent. They can also go to zero by Friday.",
     "The wolf watches a cartoon coin with a silly dog face shoot up like a rocket and then fall into a trash can.", {"a thousand percent": "1000%"}),
    ("A meme coin is a token driven by jokes, internet culture and hype, not by a product.",
     "A colorful cartoon coin with a funny face wearing sunglasses on a stage, a crowd cheering with phones.", None),
    ("Prices move on social media posts, influencers and pure attention.",
     "Giant smartphones with cartoon influencers shouting into megaphones, coins bouncing around, the wolf covering his ears.", None),
    ("For every meme coin that made people rich, thousands went to almost zero.",
     "A graveyard full of tiny tombstones shaped like coins with funny faces, the wolf walking through with a lantern.", None),
    ("Early insiders often sell to the latecomers. And the latecomers are usually us.",
     "A line of people climbing a ladder, the people at the top throwing bags of coins down at the people at the bottom, the wolf frowning.", None),
    ("If you play, treat it like a lottery ticket. A tiny amount you can lose completely.",
     "The wolf holds a single small golden lottery ticket, shrugging with a smirk.", None),
    ("Follow for part thirty-six: presales, and why most of them go wrong. Not financial advice.",
     "The wolf points at the viewer with a grin, a shiny gift box with a question mark behind him.", None),
]

R[36] = [
    ("Get in early before it lists! That's how presales are sold. Here's the catch.",
     "A flashy salesman with a megaphone in front of a shiny gift box, the wolf raising an eyebrow.", None),
    ("In a presale, you buy tokens of a project before they're tradable on exchanges.",
     "The wolf pays for a sealed mystery box at a futuristic counter, curious.", None),
    ("Often your tokens are locked for months, and you can't sell even if things go wrong.",
     "The mystery box chained shut with a big padlock and a timer, the wolf waiting impatiently.", None),
    ("Early investors and the team often bought cheaper than you, and they may sell the moment it lists.",
     "A group of shadowy figures selling coins to the crowd from a balcony on launch day, the wolf watching from below.", None),
    ("Many presales are pure marketing, and some are straight-up scams that never deliver a token.",
     "The wolf opens the mystery box and finds it completely empty except for a little cloud of dust.", None),
    ("Check the team, the token unlock schedule, and assume you could lose it all.",
     "The wolf reading a long document with a magnifying glass at a desk, serious face.", None),
    ("Follow for part thirty-seven: free crypto airdrops, real or scam? Not financial advice.",
     "The wolf points at the viewer with a grin, coins falling from the sky with little parachutes.", None),
]

R[37] = [
    ("Free crypto falling from the sky? Sometimes it's real. Often it's a trap.",
     "Gold coins falling from the sky with little parachutes, the wolf looking up suspiciously.", None),
    ("An airdrop is when a project gives away tokens, usually to early users of its app or network.",
     "A friendly airplane dropping small gift boxes with parachutes over a city, the wolf catching one.", None),
    ("Real airdrops never ask you to send money or share your seed phrase.",
     "The wolf holds a gift box and pushes away a shady hand asking for his wallet.", None),
    ("Scam airdrops put random tokens in your wallet, then lead you to a fake site to claim them.",
     "A strange glowing token appears in a phone wallet with a fishing hook attached, the wolf suspicious.", None),
    ("Connect your wallet there and approve, and it can be drained in one click.",
     "A giant vacuum cleaner sucking all the coins out of a phone, the wolf shocked.", None),
    ("If you didn't expect it, don't touch it. Unknown tokens are best ignored.",
     "The wolf walks away calmly ignoring a glowing suspicious coin on the ground.", None),
    ("Follow for part thirty-eight: how to read a crypto whitepaper. Not financial advice.",
     "The wolf points at the viewer with a grin, holding a big rolled document.", None),
]

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan.json")
    plan = json.load(open(out)) if os.path.exists(out) else {}
    for n, scenes in R.items():
        plan[str(n)] = {"part": n, "intro_say": f"How to invest in crypto. Part {NUM[n]}.",
                        "scenes": [{"say": s, "p": p, **({"show": sh} if sh else {})} for s, p, sh in scenes]}
    json.dump(plan, open(out, "w"), indent=1, ensure_ascii=False)
    print("parts:", sorted(int(k) for k in plan))
