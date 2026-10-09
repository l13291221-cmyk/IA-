"""Seconda libreria (L271+), fatta con gli ultimi crediti Vadoo: serve al bot automatico
per le storie del passato, materie prime, economia e azioni (temi di bot_backlog.txt).
Il piano 2-390 non la usa: è già montato con le immagini scelte."""
import json
import os

T = {}

T["history"] = [
    "The wolf as an ancient merchant in a sunny Greek marketplace holding the very first small gold and silver coins.",
    "The wolf in a Roman toga counting silver coins on a marble table in an ancient Roman forum.",
    "The wolf as a Silk Road trader riding a camel in a desert caravan loaded with bags of coins and spices.",
    "The wolf as a Renaissance banker in a velvet coat sitting at a wooden bench with ledgers and coins in Florence.",
    "The wolf in 1600s Dutch clothes holding a single precious red and white tulip like a treasure, crowd of buyers behind him.",
    "The wolf in 1600s Dutch clothes looking shocked at a pile of wilted tulips worth nothing, empty market square.",
    "The wolf as a 1700s gentleman with a powdered wig waving paper certificates in a crowded old coffee house.",
    "The wolf in a 1700s French street holding a fistful of paper banknotes while a crowd runs to the bank.",
    "The wolf as a gold prospector in 1849 panning for gold in a river with mountains behind him, big hat.",
    "The wolf as a Klondike gold miner in a snowy landscape with a pickaxe and a small bag of gold nuggets.",
    "The wolf in 1800s clothes watching a steam locomotive with excited investors waving railway share papers.",
    "The wolf in a 1900s Texas oil field celebrating as black oil gushes from a wooden derrick.",
    "The wolf in a 1920s suit and hat reading a stock ticker tape machine, excited, art deco office.",
    "The wolf in 1929 clothes standing in a panicked crowd outside a bank with columns, newspapers flying.",
    "The wolf in 1923 pushing a wheelbarrow full of paper banknotes to buy a single loaf of bread, old European street.",
    "The wolf in 1944 at a grand hotel conference table with delegates in suits, mountains outside the window.",
    "The wolf in a 1950s diner paying with a brand new plastic card, retro colors.",
    "The wolf in the 1960s using one of the first cash machines on a brick wall, amazed.",
    "The wolf in a 1970s gas station queue waiting next to a long line of old cars, worried.",
    "The wolf in a 1980s trading pit full of traders in colorful jackets shouting with hand signals.",
    "The wolf in 1987 staring at an old green computer screen with a falling line, dark office.",
    "The wolf in a late 1990s startup office with bean bags and beige computers, celebrating with balloons.",
    "The wolf in 2000 sitting alone in an empty startup office with boxes, a deflated balloon on the floor.",
    "The wolf in 2008 walking out of a big glass bank tower carrying a cardboard box, rainy street.",
    "The wolf in 2009 at a messy desk with an old laptop and a single glowing gold coin floating above the keyboard.",
    "The wolf in 2010 holding two large pizzas and looking at a glowing gold coin, small apartment kitchen.",
    "The wolf next to a homemade computer mining rig with fans and cables in a garage, 2011 style.",
    "The wolf in a giant warehouse full of rows of mining machines with blinking lights.",
    "The wolf at a vintage world map with old sailing ships and coins from different countries.",
    "The wolf as a medieval goldsmith storing gold in a strong room and handing out paper receipts.",
    "The wolf in an old stone bank vault from 1800s with a huge round door and stacks of gold bars.",
    "The wolf as a newspaper boy in the 1920s shouting with a stack of newspapers, busy city street.",
    "The wolf in a museum looking at a glass case with ancient coins and old banknotes.",
    "The wolf with a magnifying glass studying an old treasure map rolled out on a wooden table, candlelight.",
    "The wolf flipping through an old photo album with black and white photos of stock exchanges.",
    "The wolf standing in front of a huge wall timeline with old coins, paper money and a glowing digital coin.",
    "The wolf as a 1600s ship merchant on a dock with wooden crates of spices and a sailing ship.",
    "The wolf in an old library reading a dusty book about money by candlelight.",
    "The wolf at a 1980s home computer typing on a beige keyboard, retro bedroom.",
    "The wolf at a telegraph office in the 1800s sending a message, brass machines and wires.",
]
T["commodities"] = [
    "The wolf in a hard hat inside a glittering silver mine holding a shiny silver nugget, headlamp light.",
    "The wolf at a copper mine looking at a giant open pit with huge trucks, sunny day.",
    "The wolf holding a glowing battery next to a white salt flat with lithium pools.",
    "The wolf on an offshore oil platform at sunset in a hard hat, ocean waves.",
    "The wolf in a wheat field at golden hour holding a bundle of wheat, tractor in the distance.",
    "The wolf at a coffee plantation holding a sack of coffee beans, green hills.",
    "The wolf in a jewelry workshop examining a sparkling diamond with a loupe.",
    "The wolf at a gold refinery watching glowing molten gold poured into a bar mold.",
    "The wolf on a cargo ship deck with stacked colorful containers, port cranes behind.",
    "The wolf next to huge natural gas tanks and pipelines at dusk, blue flame.",
    "The wolf stacking silver bars and gold bars side by side on a scale, comparing them.",
    "The wolf in a field of solar panels and wind turbines at sunrise.",
    "The wolf holding a rare earth metal rock in a geology lab with microscopes.",
    "The wolf at a busy commodity exchange with screens showing grain, oil and metal icons, no text.",
    "The wolf filling a car at a gas pump, looking surprised at the rising numbers on the pump display, no text.",
]
T["economy"] = [
    "The wolf pushing a shopping cart with very few items, looking shocked at a long receipt.",
    "The wolf watching a balloon labeled with a dollar sign slowly deflate, sad face.",
    "The wolf at a grand central bank building with a giant money printing machine spitting banknotes.",
    "The wolf turning a big dial like a thermostat on a wall, central bank office, serious.",
    "The wolf on a seesaw: one side a stack of bonds, the other a stack of stocks, balancing.",
    "The wolf holding a small house model in one hand and a gold coin in the other, deciding.",
    "The wolf looking at a long line of people at a job center, worried city street.",
    "The wolf at a ballot box with flags behind him, election day atmosphere.",
    "The wolf exchanging money at an airport currency booth with banknotes of different colors.",
    "The wolf on a globe surrounded by cargo planes and ships, world trade.",
    "The wolf watering a money tree in a pot that keeps growing year after year, calendar pages flying.",
    "The wolf putting coins in a glass jar labeled with a shield icon, emergency savings, no text.",
    "The wolf holding a long paper bill and a calculator at the kitchen table, budgeting.",
    "The wolf with a snowball rolling down a hill growing bigger and bigger with coins inside it.",
    "The wolf at a factory loading dock watching boxes shipped out, busy economy.",
]
T["companies"] = [
    "The wolf in a small garage workshop building a computer with friends in the 1970s.",
    "The wolf on stage at a big product launch holding up a sleek smartphone, spotlight.",
    "The wolf touring a chip factory in a white clean room suit, glowing wafers.",
    "The wolf in a huge online shop warehouse with robots moving packages.",
    "The wolf at a company shareholder meeting raising his hand in a big auditorium.",
    "The wolf cutting a giant cake into slices that turn into small shares, stock split idea.",
    "The wolf ringing a big bell on a stock exchange balcony with confetti, IPO day.",
    "The wolf at an electric car factory with robot arms assembling cars.",
    "The wolf at a coffee shop counter of a global chain, counting coins, morning rush.",
    "The wolf reading a thick company annual report with charts at a desk, glasses on.",
    "The wolf at a giant server room with endless rows of blinking servers, cloud computing.",
    "The wolf receiving a small envelope of coins in the mail, dividend day, smiling.",
]
T["crypto2"] = [
    "The wolf holding a small metal hardware wallet like a precious key, vault background.",
    "The wolf writing a list of words on a steel plate with a punch tool, secure room.",
    "The wolf looking at a giant digital clock counting down to a halving, coins splitting in half.",
    "The wolf surfing a giant wave made of coins, bull market energy.",
    "The wolf hiding in a cave from a snowstorm, bear market winter, holding a coin close.",
    "The wolf building a tall bridge between two islands of coins, cross-chain idea.",
    "The wolf at a busy digital marketplace with glowing art frames on the walls.",
    "The wolf receiving free coins falling from the sky but noticing a hook attached to one of them.",
    "The wolf ignoring a flashy stranger offering a glowing coin in a dark alley.",
    "The wolf checking a long email on his laptop with a red warning triangle, suspicious face.",
]
T["cta"] = [
    "The wolf in an old library points at the viewer with a smile, holding an old book.",
    "The wolf in a 1920s suit and hat points at the viewer, art deco office background.",
    "The wolf at a gold mine entrance points at the viewer with a hard hat on, smiling.",
    "The wolf on a cargo ship deck points at the viewer, sunset ocean.",
    "The wolf in a Renaissance banker coat points at the viewer, Florence background.",
    "The wolf at a product launch stage points at the viewer, spotlight.",
    "The wolf next to a steam locomotive points at the viewer with a top hat.",
    "The wolf in a wheat field at golden hour points at the viewer, confident grin.",
]

lib = {}
n = 271
for theme, scenes in T.items():
    for p in scenes:
        lib[f"L{n:03d}"] = {"theme": theme, "p": p}
        n += 1

if __name__ == "__main__":
    json.dump(lib, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "library_bot.json"), "w"),
              indent=1, ensure_ascii=False)
    print(len(lib), "immagini", min(lib), "-", max(lib))
