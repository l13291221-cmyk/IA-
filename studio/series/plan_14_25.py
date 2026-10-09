"""Testi e scene dei reel 14-25 della serie "How to invest in crypto" (inglese)."""
import json
import os

NUM = {14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
       20: "twenty", 21: "twenty-one", 22: "twenty-two", 23: "twenty-three", 24: "twenty-four", 25: "twenty-five"}

R = {}

R[14] = [
    ("Two emotions empty more wallets than any market crash: FOMO and FUD.",
     "The wolf stands between two cartoon emotion clouds: a wild excited fiery cloud on the left and a trembling scared ghost cloud on the right.", None),
    ("FOMO is the fear of missing out. A coin pumps, everyone is posting about it, and you buy right at the top.",
     "The wolf runs desperately after a rocket that has already launched into the sky, a crowd of people with phones cheering around.", None),
    ("FUD is fear, uncertainty and doubt. Scary news hits, and you panic sell at the bottom.",
     "The wolf hides under his desk, trembling, while scary newspapers with big red warning symbols fly around the room.", None),
    ("Both make you act fast, without a plan. And that's exactly when mistakes happen.",
     "The wolf frantically smashing two huge arcade buttons, one green and one red, sweating, chaos around him.", None),
    ("The fix: decide your entries and exits before you even open the app.",
     "The wolf calmly writes a plan in a leather notebook at a tidy desk, cup of coffee, soft morning light.", None),
    ("And if you feel a strong urge to buy or sell right now, wait twenty-four hours.",
     "The wolf sits patiently in an armchair holding a big golden hourglass, relaxed smile.", {"twenty-four hours": "24 hours"}),
    ("Follow for part fifteen: how to spot a crypto scam in seconds. Not financial advice.",
     "The wolf points at the viewer with a grin, holding a big magnifying glass, neon city at night.", None),
]

R[15] = [
    ("Crypto scams steal billions of dollars every year. Here's how to spot most of them in seconds.",
     "The wolf with a detective magnifying glass in a dark alley full of shady neon signs, coins being stolen by shadowy hands.", None),
    ("Red flag one: guaranteed returns. Nobody can guarantee profits in crypto. Nobody.",
     "The wolf raises a big red flag in front of a shady man in a shiny suit opening a briefcase full of money.", None),
    ("Red flag two: giveaways. Send one coin and get two back. That's always a scam, even with a famous face on it.",
     "A fake smiling celebrity on a giant screen wearing a mask, gold coins being sucked into a swirling vortex, the wolf shaking his head.", None),
    ("Red flag three: pressure. Act now, only today, last chance. Real opportunities don't rush you.",
     "A shady salesman points nervously at a giant ticking clock, the wolf stands calm with arms crossed, unimpressed.", None),
    ("Red flag four: a stranger online who wants to teach you trading, then moves you to a special app.",
     "The wolf looks suspiciously at a smartphone showing a chat with hearts and a strange glowing unknown app icon.", None),
    ("If it sounds too good to be true, it is. Close the chat, and block.",
     "The wolf presses a big block button on his phone with a satisfied grin, the scammer disappearing in smoke.", None),
    ("Follow for part sixteen: what a rug pull is, and how to avoid one. Not financial advice.",
     "The wolf points at the viewer with a grin, standing on a fancy red carpet rug.", None),
]

R[16] = [
    ("You buy a new coin, it's going up, and suddenly it's worth zero. That's a rug pull.",
     "The wolf stands on a fancy rug that is being violently pulled out from under his feet, he flies in the air surprised.", None),
    ("The creators hype a token, attract buyers, then take all the money and disappear.",
     "Shady masked developers run away through a back door carrying big sacks of gold coins, a party stage with fireworks left empty.", None),
    ("Warning sign one: an anonymous team, no track record, and huge promises.",
     "Faceless hooded figures behind a flashy podium with rockets and fireworks, the wolf watching skeptically.", None),
    ("Warning sign two: the developers hold a huge share of the supply.",
     "A giant pie made of coins where a shadowy figure takes almost the whole pie, leaving only a tiny slice, the wolf frowning.", None),
    ("Warning sign three: you can buy, but you can't sell. That's called a honeypot.",
     "The wolf stuck inside a giant sticky honey pot, coins glued around him, annoyed face.", None),
    ("Stick to established coins, and treat brand new tokens as money you're ready to lose.",
     "The wolf walks past flashy carnival stalls selling new glowing coins toward a solid old stone bank building.", None),
    ("Follow for part seventeen: phishing, and the fake apps that empty wallets. Not financial advice.",
     "The wolf points at the viewer with a grin, a fishing hook dangling next to him.", None),
]

R[17] = [
    ("One wrong click can drain your wallet in seconds.",
     "The wolf's finger hovers over a glowing link on a laptop that has a hidden sharp fishing hook, dramatic tension.", None),
    ("Phishing means fake websites, emails or messages that look exactly like the real ones.",
     "Two identical glowing websites side by side on big screens, one of them hides a fishing hook behind it, the wolf comparing them.", None),
    ("They ask you to log in, connect your wallet, or type your seed phrase. And then they take everything.",
     "A giant fishing hook pulls gold coins out of a smartphone screen, the wolf trying to grab them back.", None),
    ("Always type the address yourself, or use a saved bookmark. Don't trust links in emails or ads.",
     "The wolf types carefully on a keyboard, a big red bookmark ribbon on the screen, focused face.", None),
    ("Download wallet apps only from the official site or app store, and check who the developer is.",
     "The wolf in a futuristic store aisle inspecting colorful app boxes with a magnifying glass.", None),
    ("And never approve a wallet transaction you don't fully understand.",
     "The wolf refuses to sign a very long mysterious glowing contract scroll, pushing the pen away.", None),
    ("Follow for part eighteen: diversification, done the right way. Not financial advice.",
     "The wolf points at the viewer with a grin, several baskets of colorful eggs behind him.", None),
]

R[18] = [
    ("Putting everything in one coin is risky. But owning fifty random coins isn't diversification either.",
     "The wolf balances one wobbling basket with all the eggs, next to a messy overflowing basket with dozens of eggs falling out.", {"fifty": "50"}),
    ("Diversification means spreading risk, so one bad bet can't sink your whole portfolio.",
     "A big ship with separate watertight compartments, one compartment leaking but the ship still floating, the wolf as captain.", None),
    ("But most crypto moves together. When Bitcoin drops, many altcoins drop even harder.",
     "A group of coins tied together with a rope falling off a cliff, a big golden Bitcoin leading the fall, the wolf watching.", None),
    ("So real diversification also means not having all your money in crypto.",
     "The wolf at a table with separate piles: cash, gold bars, a small house model, and a small pile of crypto coins.", None),
    ("A few solid coins you actually understand beat a long list of random ones.",
     "The wolf carefully picks a few shiny gold coins out of a huge messy pile of random coins.", None),
    ("Follow for part nineteen: a simple way to build a crypto portfolio. Not financial advice.",
     "The wolf points at the viewer with a grin, a golden planet with small moons orbiting behind him.", None),
]

R[19] = [
    ("Here's a simple way many investors structure a crypto portfolio: a core, and satellites.",
     "The wolf in an astronaut suit floating in space next to a big golden planet with small moons orbiting it.", None),
    ("The core is the biggest part, usually the most established coins, like Bitcoin and Ethereum.",
     "A huge solid golden planet made of Bitcoin and Ethereum coins, glowing, the wolf standing proudly on it.", None),
    ("The satellites are small positions in riskier coins that could grow faster, or go to zero.",
     "Small colorful moons orbiting the golden planet, one moon exploding into dust, the wolf watching from his spaceship.", None),
    ("Big core, small satellites. Never the other way round.",
     "The wolf points at a big heavy golden planet and a few tiny moons, giving a confident thumbs up.", None),
    ("That way, if one risky bet fails, your core keeps you in the game.",
     "A small moon breaks apart but the big golden planet remains perfectly intact, the wolf relaxing on it.", None),
    ("And check it a few times a year, rebalancing if it gets out of shape.",
     "The wolf with a giant wrench adjusting the orbits of the moons like a mechanic, focused.", None),
    ("Follow for part twenty: position sizing, the rule that keeps you alive. Not financial advice.",
     "The wolf points at the viewer with a grin, holding a ruler and a small bag of coins.", None),
]

R[20] = [
    ("Picking the right coin matters less than how much money you put into it.",
     "The wolf chooses between a small bag of coins and a gigantic overflowing bag of coins, thinking hard.", None),
    ("Position sizing means deciding how big each investment is, before you buy.",
     "The wolf measures piles of gold coins with a big ruler like a tailor, careful.", None),
    ("A common rule for traders: risk only one or two percent of your account on a single trade.",
     "The wolf cuts a tiny thin slice from a huge golden pie made of coins and puts it on a small plate.", {"one or two percent": "1-2%"}),
    ("That way, even ten losing trades in a row won't wipe you out.",
     "The wolf holds a strong shield while ten small arrows bounce off it, standing firm and smiling.", {"ten": "10"}),
    ("Bigger bets feel exciting, but one bad move can undo months of gains.",
     "The wolf watches a tall tower of cards made of money collapse in front of him, shocked.", None),
    ("Small, consistent positions are boring. And boring is how you stay in the game.",
     "The wolf calmly stacks small neat piles of coins in a row on a desk, relaxed.", None),
    ("Follow for part twenty-one: the hidden fees eating your profits. Not financial advice.",
     "The wolf points at the viewer with a grin, a tiny gremlin nibbling a gold coin on his shoulder.", None),
]

R[21] = [
    ("You might be losing money to fees without even noticing.",
     "The wolf holds a bag of gold coins while tiny gremlins secretly nibble the coins from behind.", None),
    ("Trading fees: every time you buy or sell, the exchange takes a small cut.",
     "The wolf drives a small car through a futuristic toll booth where a robotic arm takes a gold coin.", None),
    ("The spread: the gap between the buy price and the sell price. Instant buy buttons often hide a big one.",
     "Two glowing price tags floating far apart with a wide gap between them, the wolf measuring the gap with a tape measure.", None),
    ("Network fees: moving coins on a blockchain costs a fee, and it changes with demand.",
     "A futuristic highway in a traffic jam of rolling gold coins waiting at a toll gate, the wolf in the queue.", None),
    ("Withdrawal fees: some exchanges charge extra to send your coins out.",
     "A big bouncer at a club door charging the wolf a coin to let his coins leave, the wolf annoyed.", None),
    ("Small fees, repeated a hundred times, become big losses. Trade less, and compare more.",
     "A small pile of coins growing into a huge mountain made of tiny coins, the wolf amazed at the bottom.", None),
    ("Follow for part twenty-two: the mistake that sends coins into the void forever. Not financial advice.",
     "The wolf points at the viewer with a serious grin, a swirling black hole behind him.", None),
]

R[22] = [
    ("Send crypto on the wrong network, and it can be gone forever.",
     "A gold coin falling into a swirling black hole in space, the wolf reaching out in shock.", None),
    ("Many coins exist on several blockchains. USDT, for example, runs on Ethereum, Tron and others.",
     "A gold coin standing at a junction of several glowing futuristic highways of different colors, the wolf pointing at the signs without text.", None),
    ("The sender and the receiver must use the same network. If they don't, the money may never arrive.",
     "Two bridges that don't connect in the middle, a coin falling into the gap, the wolf facepalming.", None),
    ("Always double check the address. Copy and paste it, then compare the first and last characters.",
     "The wolf compares two long paper scrolls side by side with a magnifying glass, very focused.", None),
    ("Watch out for clipboard malware, which secretly swaps the address you pasted.",
     "A tiny sneaky virus bug swapping two pieces of paper behind the wolf's back.", None),
    ("And for big amounts, send a small test first. A small fee is cheaper than a big mistake.",
     "The wolf sends a tiny coin across a bridge first, while a giant gold coin waits behind him.", None),
    ("Follow for part twenty-three: gas fees, and why they sometimes explode. Not financial advice.",
     "The wolf points at the viewer with a grin, leaning on a futuristic gas pump.", None),
]

R[23] = [
    ("Ever tried to send crypto, and the fee was higher than the amount? Let's talk about gas.",
     "The wolf stares in shock at a giant gas pump with a huge glowing price, holding a tiny coin.", None),
    ("On Ethereum, every action needs computing power. Gas is the fee you pay for it.",
     "The wolf fills up a sports car with glowing purple fuel shaped like the Ethereum diamond.", None),
    ("When the network is busy, fees go up. Like taxi prices at rush hour.",
     "A massive traffic jam of yellow taxis at rush hour in a neon city, the wolf stuck in one taxi looking at the meter.", None),
    ("That's why layer two networks were built. They bundle many transactions together and settle them on Ethereum.",
     "A big futuristic bus carrying many small coins onto a fast highway, the wolf as the bus driver.", None),
    ("The result: much lower fees, while still relying on Ethereum for security.",
     "The wolf happily pays with a tiny coin at a cheap toll booth, a big Ethereum shield glowing above.", None),
    ("Just make sure your exchange and your wallet support the layer two you're using.",
     "The wolf tries to fit a plug into a socket, checking that they match, focused.", None),
    ("Follow for part twenty-four: Bitcoin dominance and altcoin season. Not financial advice.",
     "The wolf points at the viewer with a grin, a giant golden pie chart behind him.", None),
]

R[24] = [
    ("There's one chart that shows whether Bitcoin or the altcoins are in charge: Bitcoin dominance.",
     "The wolf stands in front of a giant glowing pie chart where one huge golden slice dominates.", None),
    ("Bitcoin dominance is Bitcoin's share of the total crypto market.",
     "A giant pie made of coins with a big golden Bitcoin slice and many smaller colorful slices, the wolf pointing at the gold slice.", None),
    ("When it rises, money is flowing into Bitcoin, and altcoins often struggle.",
     "A river of gold coins flowing into a big golden lake, while small colorful ponds nearby dry up, the wolf watching.", None),
    ("When it falls, money moves into altcoins. Some people call that altcoin season.",
     "Colorful cartoon coins having a wild party with fireworks and music, the wolf dancing with them.", None),
    ("But altcoin seasons are short and hard to predict, and many altcoins never recover afterwards.",
     "The party is over, broken colorful coins lying on the floor with confetti, the wolf cleaning up with a broom.", None),
    ("So watch this chart, but never use it as your only signal.",
     "The wolf looks at several screens with different charts, a big golden pie chart among them, thoughtful.", None),
    ("Follow for part twenty-five: how to read a candlestick. Not financial advice.",
     "The wolf points at the viewer with a grin, holding a big glowing green candle.", None),
]

R[25] = [
    ("Every crypto chart is made of these little candles. Here's how to read one in thirty seconds.",
     "The wolf holds a giant glowing green candlestick bar like a trophy, a trading chart in the background.", {"thirty seconds": "30 seconds"}),
    ("Each candle shows four prices: where it opened, where it closed, the highest point and the lowest.",
     "The wolf points with a stick at a giant candlestick bar on a stage, like a teacher in front of a class.", None),
    ("Green means it closed higher than it opened. Red means it closed lower.",
     "One giant green candle and one giant red candle standing on a stage under spotlights, the wolf between them.", None),
    ("The thick part is the body. The thin lines are the wicks: the extremes the price touched.",
     "The wolf touches the thin wick line on top of a giant candlestick bar, curious face.", None),
    ("A long wick below means sellers pushed the price down, but buyers pushed it back up.",
     "A tug of war on a giant candlestick: bears pulling down and bulls pulling up, the bulls winning, the wolf as referee.", None),
    ("But one candle is just a clue, not a signal. Always look at the bigger picture.",
     "The wolf looks through binoculars at a huge chart full of candles in the distance, zooming out.", None),
    ("Follow for part twenty-six: support and resistance, explained. Not financial advice.",
     "The wolf points at the viewer with a grin, standing on a glowing floor with a ceiling above.", None),
]

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan.json")
    plan = json.load(open(out)) if os.path.exists(out) else {}
    for n, scenes in R.items():
        plan[str(n)] = {"part": n, "intro_say": f"How to invest in crypto. Part {NUM[n]}.",
                        "scenes": [{"say": s, "p": p, **({"show": sh} if sh else {})} for s, p, sh in scenes]}
    json.dump(plan, open(out, "w"), indent=1, ensure_ascii=False)
    print("parts:", sorted(int(k) for k in plan))
