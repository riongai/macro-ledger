#!/usr/bin/env python3
"""Insert a sugar value into every FOODS row of macro-ledger.html.

Sugar is added as the 8th field, between fat and cuisine:
    [name, unit, basis, kcal, protein, carbs, fat, SUGAR, cuisine]

Two sources, in priority order:

1. EXPLICIT — whole foods and single ingredients, where sugar content is
   established composition data (USDA-style per 100 g, or per the row's own
   basis for per-piece items). These are facts, not guesses.

2. Derived — composite dishes have no published sugar figure anywhere, so
   sugar is computed as a fraction of that dish's carbohydrate, using the
   most specific matching rule. A plate of char kuey teow is mostly starch
   with a little sweet sauce (~10%); a bubble tea is essentially all sugar
   (~95%). The ratio encodes what actually carries the sugar in the dish.

Run: python3 add-sugar.py
"""
import re, sys

SRC = "macro-ledger.html"

# ---------------------------------------------------------------- explicit
# Grams of sugar per the row's own basis. Whole foods and ingredients only.
EXPLICIT = {
    # fruit
    "Banana, medium": 14.4, "Apple, medium": 19.0, "Orange, medium": 12.2,
    "Kiwi fruit": 6.2, "Medjool date": 16.0, "Mango": 13.7, "Pineapple": 9.9,
    "Watermelon": 6.2, "Grapes": 15.5, "Strawberries": 4.9, "Blueberries": 10.0,
    "Avocado": 0.7, "Durian": 20.0,
    # vegetables
    "Broccoli": 1.7, "Spinach": 0.4, "Mixed salad leaves": 0.9, "Mushrooms": 2.0,
    "Carrot": 4.7, "Capsicum": 4.2, "Zucchini": 2.5, "Green beans": 3.3,
    "Cucumber": 1.7, "Tomato": 2.6, "Sweet corn": 4.5, "Green peas": 5.7,
    "Bok choy, stir-fried": 1.5, "Edamame": 2.2, "Kimchi": 1.9,
    # protein — plain meat, fish and eggs carry no sugar
    "Chicken breast, cooked": 0, "Chicken thigh, cooked": 0, "Turkey breast, cooked": 0,
    "Beef mince 5%, raw": 0, "Steak, lean, cooked": 0, "Pork loin, cooked": 0,
    "Lamb chop, cooked": 0, "Salmon, cooked": 0, "White fish (cod), cooked": 0,
    "Tuna, tinned in springwater": 0, "Sardines, tinned": 0, "Prawns, cooked": 0,
    "Sashimi, tuna": 0, "Egg, large": 0.2, "Egg white": 0.2,
    "Greek yoghurt, 0% fat": 3.6, "Cottage cheese": 3.0, "Cheddar cheese": 0.5,
    "Paneer": 2.6, "Tofu, firm": 0.6, "Tempeh": 0.5, "Natto": 2.2,
    "Whey protein powder": 2.0, "Casein protein powder": 2.0,
    "Black beans, cooked": 0.3, "Chickpeas, cooked": 4.8,
    # staples
    "White rice, cooked": 0.1, "Brown rice, cooked": 0.4, "Rice noodles, cooked": 0.1,
    "Egg noodles, cooked": 0.6, "Pasta, cooked": 0.6, "Pasta, wholemeal, cooked": 1.0,
    "Pasta, fresh egg, cooked": 1.0, "Pasta, gluten free, cooked": 0.5,
    "Spaghetti, dry": 2.7, "Lasagna sheets, dry": 2.7, "Quinoa, cooked": 0.9,
    "Rolled oats, dry": 1.0, "Potato, boiled": 0.9, "Sweet potato, baked": 6.5,
    "Wholemeal bread": 4.0, "Tortilla wrap, white": 1.5, "Rice cake": 0.2,
    "Couscous, cooked": 0.1, "Soba noodles, cooked": 0.5,
    "Gnocchi, potato, plain": 1.0, "Sticky rice, 1 cup": 0.2,
    # fats, dairy, sauces
    "Olive oil": 0, "Sesame oil": 0, "Butter": 0,
    "Milk, full cream": 4.8, "Milk, skim": 5.0, "Soy milk": 3.0,
    "Coconut milk": 3.0, "Coconut cream": 3.0,
    "Soy sauce": 0.4, "Oyster sauce": 4.0, "Hoisin sauce": 6.0, "Sriracha": 2.5,
    "Peanut sauce": 4.0, "Peanut butter": 9.0, "Almonds": 4.4, "Cashews": 6.0,
    "Walnuts": 2.6, "Chia seeds": 0, "Honey": 16.3, "Dark chocolate 70%": 24.0,
    "Parmesan": 0.2, "Pesto": 0.5, "Napolitana sauce": 5.0, "Bolognese sauce": 3.0,
    "Alfredo sauce": 2.0, "Grilled halloumi": 2.0, "Hummus": 0.3, "Guacamole": 0.7,
    "Prawn crackers": 1.0, "Keropok lekor": 2.0,
    # alcohol — ethanol is not sugar; only mixers and residual sugar count
    "Beer, mid-strength": 0.4, "Beer, full strength schooner": 0.5, "Beer, pint": 0.7,
    "Craft IPA, 375 ml": 1.0, "Cider, 375 ml": 20.0, "Red wine": 1.0,
    "White wine, 150 ml": 1.4, "Sparkling wine, 150 ml": 2.0, "Sake, 100 ml": 2.0,
    "Soju, 360 ml bottle": 0, "Spirit, neat nip 30 ml": 0,
    "Whiskey (whisky), nip 30 ml": 0, "Whiskey (whisky), double 60 ml": 0,
    "Whiskey (whisky), free pour 90 ml": 0, "Whiskey (whisky), cask strength nip": 0,
    "Whiskey and soda water": 0, "Diet soft drink": 0, "Electrolyte tablet drink": 0,
    "Energy drink, sugar-free": 0, "Tea, green or herbal": 0,
    "Espresso / short black": 0, "Long black / americano": 0, "Cold brew, black": 0,
    "Kopi o": 8.0, "Sugar, 1 teaspoon": 4.0, "Wheatgrass shot": 1.0,
}

# ------------------------------------------------------------------- rules
# (substring, fraction of carbohydrate that is sugar). First match wins, so
# the list runs most specific to least.
KEYWORD = [
    # essentially liquid sugar
    ("bubble tea", .95), ("brown sugar milk", .95), ("sirap", .95), ("cendol", .80),
    ("milo", .85), ("cola", 1.0), ("lemonade", 1.0), ("ginger beer", 1.0),
    ("tonic water", 1.0), ("energy drink", 1.0), ("sports drink", 1.0),
    ("iced tea", 1.0), ("kombucha", 1.0), ("juice", .95), ("coconut water", .90),
    ("sugarcane", 1.0), ("root beer float", .90), ("air limau", 1.0),
    ("teh o ais limau", 1.0), ("thai iced tea", .85), ("teh tarik", .80),
    ("kopi", .80), ("vietnamese iced coffee", .85), ("milkshake", .85),
    ("thickshake", .85), ("frappuccino", .85), ("frappe", .85),
    ("iced blended", .85), ("iced coffee", .80), ("hot chocolate", .80),
    ("mocha", .75), ("chai latte", .75), ("matcha latte", .75),
    ("caramel macchiato", .80), ("green tea latte", .75), ("smoothie", .85),
    ("acai bowl", .70), ("frozen yoghurt", .80), ("lassi", .80),
    ("shot", .80), ("margarita", 1.0), ("espresso martini", .95),
    ("old fashioned", 1.0), ("manhattan", 1.0), ("whiskey sour", 1.0),
    ("hot toddy", 1.0), ("aperol", 1.0), ("gin and tonic", 1.0),
    ("spirit with cola", 1.0), ("and cola", 1.0), ("dry ginger ale", 1.0),
    ("flavoured milk", .80), ("chocolate milk", .80), ("soft serve", .80),
    # plain milk coffees: the carbohydrate is lactose, so it is all sugar
    ("latte", .95), ("cappuccino", .95), ("flat white", .95), ("piccolo", .95),
    ("macchiato", .95), ("instant coffee with milk", .90), ("tea, black with milk", .90),
    ("tea with milk and sugar", .95), ("miso soup", .30),
    # desserts and sweets
    ("ice cream", .75), ("gelato", .75), ("sundae", .80), ("mcflurry", .75),
    ("cheesecake", .70), ("brownie", .70), ("cookie", .60), ("doughnut", .60),
    ("cake", .65), ("pie", .55), ("tiramisu", .70), ("churros", .60),
    ("waffle", .60), ("pancake", .55), ("hotcakes", .55), ("muffin", .55),
    ("danish", .55), ("croissant", .25), ("banana bread", .55),
    ("chocolate", .70), ("gummy", .95), ("nutella", .80), ("honey", .95),
    ("mochi", .60), ("taiyaki", .60), ("dorayaki", .65), ("melon pan", .55),
    ("apam balik", .60), ("kuih", .55), ("ondeh", .60), ("bubur cha cha", .65),
    ("ais kacang", .80), ("halo halo", .70), ("gulab jamun", .75), ("jalebi", .80),
    ("kulfi", .70), ("egg tart", .55), ("pineapple bun", .50), ("sesame ball", .55),
    ("mango pudding", .70), ("sticky date", .65), ("mango sticky rice", .55),
    ("bingsu", .70), ("hotteok", .65), ("ube cake", .60), ("che (", .70),
    ("banana fritters", .45), ("pisang goreng", .40), ("martabak manis", .55),
    ("kaya", .60), ("dessert", .65), ("pastry", .50), ("bar", .60),
    ("raisins", .95), ("dates", .95),
    # savoury dishes with a distinctly sweet sauce
    ("sweet and sour", .55), ("honey chicken", .55), ("lemon chicken", .50),
    ("teriyaki", .45), ("char siu", .45), ("char siew", .45), ("bulgogi", .35),
    ("yangnyeom", .40), ("satay", .30), ("peanut sauce", .30), ("rendang", .20),
    ("massaman", .25), ("pad thai", .25), ("som tam", .35), ("rojak", .40),
    ("gado gado", .30), ("tteokbokki", .30), ("japchae", .25), ("adobo", .20),
    ("korma", .20), ("butter chicken", .25), ("tikka masala", .25),
    ("sweet potato chips", .30), ("baked beans", .40),
    # breads, wraps, buns — a little added sugar in the dough
    ("naan", .10), ("roti", .10), ("bread", .12), ("bun", .15), ("bao", .20),
    ("toast", .12), ("bagel", .10), ("wrap", .10), ("pita", .10),
    # burgers, pizza and fried food: sauce and bun only
    ("burger", .18), ("pizza", .12), ("taco", .15), ("burrito", .12),
    ("nachos", .12), ("hot dog", .25), ("nugget", .08), ("fries", .03),
    ("chips", .03), ("wedges", .05), ("hash brown", .03), ("onion ring", .10),
    ("tempura", .05), ("karaage", .08), ("fried chicken", .08), ("popcorn chicken", .10),
    ("schnitzel", .08), ("parmigiana", .12), ("katsu", .10),
    # noodle and rice plates: mostly starch
    ("fried rice", .06), ("nasi", .08), ("mee", .10), ("noodle", .08),
    ("kuey teow", .10), ("kway teow", .10), ("ramen", .06), ("udon", .05),
    ("pho", .08), ("congee", .03), ("porridge", .05), ("biryani", .06),
    ("risotto", .05), ("bibimbap", .12), ("sushi", .15), ("nigiri", .15),
    ("onigiri", .05), ("gimbap", .10), ("laksa", .12), ("curry", .12),
    ("soup", .10), ("salad", .25), ("stew", .12), ("dumpling", .08),
    ("gyoza", .08), ("spring roll", .10), ("samosa", .08), ("pakora", .10),
    ("crackers", .05), ("crisps", .03), ("pretzel", .04), ("popcorn", .02),
    ("jerky", .60), ("peanuts", .15), ("hummus", .05),
]

# per-cuisine fallback when nothing above matches
CUISINE = {
    "Dessert": .70, "Drinks": .90, "Juice bar": .85, "Coffee & tea": .80,
    "Snacks": .15, "Fast food": .15, "Franchise": .15,
    "Malaysian": .12, "Chinese": .12, "Japanese": .10, "Korean": .15,
    "Thai": .18, "Vietnamese": .12, "Indian": .12, "SE Asian": .15,
    "Filipino": .15, "Middle East": .10, "Italian & Med": .10, "Mexican": .12,
    "Western": .15, "Protein": .0, "Staple": .02, "Extras": .20,
    "Fruit & veg": .80,
}

ROW = re.compile(r'^(\s*)\["(.+?)","(\w+)",([\d.]+),([\d.]+),([\d.]+),([\d.]+),([\d.]+),"(.+?)"\],\s*$')


def sugar_for(name, carbs, cui):
    if name in EXPLICIT:
        return EXPLICIT[name], "explicit"
    low = name.lower()
    for kw, ratio in KEYWORD:
        if kw in low:
            return round(carbs * ratio, 1), "rule"
    return round(carbs * CUISINE.get(cui, .12), 1), "cuisine"


def main():
    lines = open(SRC, encoding="utf-8").read().split("\n")
    out, stats, changed = [], {"explicit": 0, "rule": 0, "cuisine": 0}, 0
    inside = False
    for line in lines:
        if "const FOODS = [" in line:
            inside = True
        elif inside and line.startswith("];"):
            inside = False
        m = ROW.match(line) if inside else None
        if not m:
            out.append(line)
            continue
        indent, name, unit, basis, kcal, p, c, f, cui = m.groups()
        s, how = sugar_for(name, float(c), cui)
        if s > float(c):            # sugar can never exceed total carbohydrate
            s = float(c)
        stats[how] += 1
        changed += 1
        s_txt = str(int(s)) if float(s) == int(s) else str(s)
        out.append(f'{indent}["{name}","{unit}",{basis},{kcal},{p},{c},{f},{s_txt},"{cui}"],')
    open(SRC, "w", encoding="utf-8").write("\n".join(out))
    print(f"rows updated: {changed}")
    for k, v in stats.items():
        print(f"  {k:9}: {v}")
    if changed != 645:
        print(f"WARNING: expected 645 rows, got {changed}", file=sys.stderr)


main()
