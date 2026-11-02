"""Word lists the scraper uses to find products and label the keywords around them.

Everything here is plain data, so it is the place to tune results:
- add a brand to BRANDS to start tracking its products,
- add a phrase to one of the keyword groups to start counting it.
"""

# Subreddits to read, with the category a post there usually belongs to.
# "mixed" means the category comes from the product words instead.
SUBREDDITS = {
    "SkincareAddiction": "skincare",
    "AsianBeauty": "skincare",
    "30PlusSkinCare": "skincare",
    "SkincareAddicts": "skincare",
    "Sephora": "mixed",
    "Ulta": "mixed",
    "MakeupAddiction": "makeup",
    "drugstoreMUA": "makeup",
    "BeautyGuruChatter": "mixed",
    "MakeupRehab": "makeup",
}

# brand alias (lowercase, as people type it) -> display name.
BRANDS = {
    "abib": "Abib", "aestura": "Aestura", "anua": "Anua", "aveeno": "Aveeno",
    "axis-y": "Axis-Y", "axis y": "Axis-Y", "beauty of joseon": "Beauty of Joseon",
    "boj": "Beauty of Joseon", "biore": "Bioré", "bioré": "Bioré",
    "bioderma": "Bioderma", "biodance": "Biodance", "byoma": "Byoma",
    "cerave": "CeraVe", "cetaphil": "Cetaphil", "cosrx": "COSRX",
    "drunk elephant": "Drunk Elephant", "dr. jart": "Dr. Jart+", "dr jart": "Dr. Jart+",
    "dr.jart": "Dr. Jart+", "eucerin": "Eucerin", "first aid beauty": "First Aid Beauty",
    "glow recipe": "Glow Recipe", "good molecules": "Good Molecules",
    "haruharu wonder": "Haruharu Wonder", "isntree": "Isntree", "innisfree": "Innisfree",
    "kiehl's": "Kiehl's", "kiehls": "Kiehl's", "krave beauty": "KraveBeauty",
    "la roche-posay": "La Roche-Posay", "la roche posay": "La Roche-Posay",
    "lrp": "La Roche-Posay", "laneige": "Laneige", "medicube": "Medicube",
    "mixsoon": "Mixsoon", "neutrogena": "Neutrogena", "numbuzin": "Numbuzin",
    "olay": "Olay", "paula's choice": "Paula's Choice", "paulas choice": "Paula's Choice",
    "peach & lily": "Peach & Lily", "peach and lily": "Peach & Lily",
    "purito": "Purito", "round lab": "Round Lab", "skin1004": "SKIN1004",
    "skinfix": "Skinfix", "some by mi": "Some By Mi", "summer fridays": "Summer Fridays",
    "sunday riley": "Sunday Riley", "supergoop": "Supergoop!", "the inkey list": "The INKEY List",
    "inkey list": "The INKEY List", "the ordinary": "The Ordinary", "torriden": "Torriden",
    "tatcha": "Tatcha", "tower 28": "Tower 28", "vanicream": "Vanicream",
    "versed": "Versed", "youth to the people": "Youth To The People",
    "beekman 1802": "Beekman 1802", "naturium": "Naturium",
    "eltamd": "EltaMD", "elta md": "EltaMD", "avène": "Avène", "avene": "Avène",
    "aquaphor": "Aquaphor", "differin": "Differin", "hero cosmetics": "Hero Cosmetics",
    "mighty patch": "Mighty Patch", "starface": "Starface", "sol de janeiro": "Sol de Janeiro",
    "bubble skincare": "Bubble", "rhode": "Rhode", "skinceuticals": "SkinCeuticals",
    "estee lauder": "Estée Lauder", "estée lauder": "Estée Lauder", "clinique": "Clinique",
    "shiseido": "Shiseido", "sk-ii": "SK-II", "sulwhasoo": "Sulwhasoo", "dieux": "Dieux",
    "augustinus bader": "Augustinus Bader", "la mer": "La Mer", "kosas": "Kosas",
    "ilia": "ILIA", "glossier": "Glossier", "rare beauty": "Rare Beauty",
    "fenty beauty": "Fenty Beauty", "fenty": "Fenty Beauty", "charlotte tilbury": "Charlotte Tilbury",
    "huda beauty": "Huda Beauty", "nars": "NARS", "maybelline": "Maybelline",
    "l'oreal": "L'Oréal", "loreal": "L'Oréal", "l'oréal": "L'Oréal", "elf": "e.l.f.",
    "e.l.f.": "e.l.f.", "e.l.f": "e.l.f.", "milani": "Milani", "nyx": "NYX",
    "covergirl": "CoverGirl", "revlon": "Revlon", "wet n wild": "wet n wild",
    "essence": "essence", "catrice": "Catrice", "colourpop": "ColourPop", "colorpop": "ColourPop",
    "morphe": "Morphe", "too faced": "Too Faced", "benefit": "Benefit", "urban decay": "Urban Decay",
    "tarte": "Tarte", "mac": "MAC", "dior": "Dior", "chanel": "Chanel", "ysl": "YSL",
    "armani beauty": "Armani Beauty", "giorgio armani": "Armani Beauty", "hourglass": "Hourglass",
    "patrick ta": "Patrick Ta", "makeup by mario": "Makeup by Mario",
    "danessa myricks": "Danessa Myricks", "haus labs": "Haus Labs", "saie": "Saie",
    "merit": "Merit", "westman atelier": "Westman Atelier", "nudestix": "Nudestix",
    "anastasia beverly hills": "Anastasia Beverly Hills", "abh": "Anastasia Beverly Hills",
    "benefit cosmetics": "Benefit", "it cosmetics": "IT Cosmetics", "laura mercier": "Laura Mercier",
    "pat mcgrath": "Pat McGrath", "natasha denona": "Natasha Denona", "kylie cosmetics": "Kylie Cosmetics",
    "one/size": "One/Size", "onesize": "One/Size", "half magic": "Half Magic", "lys beauty": "LYS Beauty",
    "about-face": "About-Face", "about face": "About-Face", "physicians formula": "Physicians Formula",
    "rimmel": "Rimmel", "lancome": "Lancôme", "lancôme": "Lancôme", "clarins": "Clarins",
    "romand": "Rom&nd", "rom&nd": "Rom&nd", "peripera": "Peripera", "clio": "CLIO",
    "hince": "Hince", "dasique": "Dasique", "amuse": "Amuse", "3ce": "3CE", "tirtir": "TIRTIR",
    "lisa eldridge": "Lisa Eldridge", "sephora collection": "Sephora Collection",
    "summer friday": "Summer Fridays", "bobbi brown": "Bobbi Brown", "smashbox": "Smashbox",
    "jones road": "Jones Road", "r.e.m. beauty": "r.e.m. beauty", "rem beauty": "r.e.m. beauty",
    "gxve": "GXVE", "valentino beauty": "Valentino Beauty", "prada beauty": "Prada Beauty",
    "hermes": "Hermès", "tom ford": "Tom Ford", "sisley": "Sisley", "byredo": "Byredo",
    "kaja": "KAJA", "lancer": "Lancer", "fwee": "fwee", "wakemake": "Wakemake",
    "dear dahlia": "Dear Dahlia", "laka": "Laka", "unleashia": "Unleashia",
}

# Words that tell us what kind of product a phrase is.
SKINCARE_TYPES = {
    "cleanser", "cleansers", "wash", "face wash", "cleansing", "balm", "oil", "toner", "toners",
    "essence", "serum", "serums", "ampoule", "moisturizer", "moisturiser", "moisturizers",
    "cream", "creams", "lotion", "gel", "gel-cream", "sunscreen", "sunscreens", "spf",
    "sunblock", "sun", "retinol", "retinal", "retinoid", "tretinoin", "adapalene", "exfoliant",
    "exfoliator", "aha", "bha", "peel", "pads", "pad", "mask", "masks", "patches", "patch",
    "eye cream", "mist", "treatment", "niacinamide", "vitamin c", "acid", "hyaluronic",
    "ceramide", "peptide", "peptides", "snail", "mucin", "centella", "cica", "rice", "barrier",
    "salve", "ointment", "sleeping", "overnight", "lip mask", "lip balm", "jelly", "glaze",
    "pore", "pores", "clay", "scrub", "sunstick", "stick", "milk", "foam",
}
MAKEUP_TYPES = {
    "foundation", "concealer", "concealers", "powder", "setting", "spray", "primer", "blush",
    "blushes", "bronzer", "contour", "highlighter", "highlight", "mascara", "eyeliner", "liner",
    "lipstick", "lipsticks", "lip", "gloss", "lipgloss", "stain", "tint", "skin tint", "palette",
    "eyeshadow", "shadow", "shadows", "brow", "brows", "pencil", "gel", "pomade", "lash",
    "lashes", "cushion", "bb", "cc", "kohl", "pigment", "glitter", "topper", "duo", "trio",
    "liquid", "pinch", "matte", "velvet", "balm", "crayon", "crème", "creme", "cheek",
}

# Words that mean "this is not a specific product" when they follow a brand.
GENERIC_AFTER_BRAND = {
    "products", "product", "stuff", "line", "brand", "brands", "items", "item", "store",
    "website", "site", "sale", "sales", "pr", "haul", "dupes", "dupe", "collection", "range",
    "version", "one", "ones", "stores", "counter", "account", "packaging", "customer", "team",
    "lol", "x", "vs", "and", "or", "&", "but", "too", "also", "is", "are", "was", "were",
    "gwp", "brush", "brushes", "mini", "minis", "set", "sets", "kit", "gift", "gifts", "sample",
    "samples", "palettes", "launch", "launches", "releases", "release", "event", "order",
}

# A name that is only a brand plus one of these is a category, not a product ("NARS Palette").
CATEGORY_WORDS = {
    "palette", "palettes", "cream", "creams", "moisturizer", "moisturizers", "cleanser", "cleansers",
    "sunscreen", "sunscreens", "spf", "serum", "serums", "toner", "toners", "lip", "lips", "lipstick",
    "lipsticks", "gloss", "foundation", "concealer", "blush", "bronzer", "highlighter", "mascara",
    "eyeliner", "liner", "primer", "powder", "setting", "spray", "brow", "brows", "skincare", "makeup",
    "lotion", "oil", "balm", "mask", "masks", "face", "eye", "eyes", "cheek", "tint", "tints",
    "essence", "gel", "wash", "pads", "pad", "body", "sun", "retinol", "stick", "sticks", "stuff",
}

STOPWORDS = set("""
a about above after again against all almost also am an and any are aren't as at be because
been before being below between both but by can can't cannot could couldn't did didn't do does
doesn't doing don't down during each even ever every few for from further get gets getting got
had hadn't has hasn't have haven't having he he'd he'll he's her here here's hers herself him
himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself just let's like
literally lol me more most mustn't my myself no nor not now of off on once only or other ought
our ours ourselves out over own really same shan't she she'd she'll she's should shouldn't so
some such than that that's the their theirs them themselves then there there's these they
they'd they'll they're they've this those through to too under until up us very was wasn't we
we'd we'll we're we've were weren't what what's when when's where where's which while who
who's whom why why's will with won't would wouldn't you you'd you'll you're you've your yours
yourself yourselves im ive dont doesnt didnt cant isnt wasnt thats theyre youre u ur yeah yes
ok okay thing things think thought much many lot lots one two also still use used using
using tried try trying bought buy buying know make makes made way want wanted need needs
since though however actually definitely probably maybe pretty super honestly anyone someone
something anything everything every always never sometimes usually would've could've
going go goes went see seen look looks looked feel feels felt day days week weeks time times
year years month months bit kind sort right new good great best better love loved
""".split())

# Words too common in beauty talk to count as a keyword on their own.
BEAUTY_GENERIC = set("""
skin face product products routine makeup skincare face's using use apply applied applying
wear wearing wore put bottle tube price color colour shade shades formula look looks brand
help helps helped hair body thanks thank post comment people sub reddit edit update
luck else last found keep weird helpful removed question questions follow bad missing gave
helping step top similar well perfect size work works worked worth link links amazon sephora
ulta target store stores buy bought recommend recommendation recommendations nice cute
favorite favourite fav ones also pretty little lot advice please anyone help idea ideas
monday tuesday wednesday thursday friday saturday sunday morning night tonight today
""".split())

# Words that end a product name when they follow it.
NAME_BREAKERS = (STOPWORDS | {
    "honestly", "personally", "tbh", "imo", "lately", "recently", "today", "yesterday",
    "everyday", "daily", "though", "instead", "alone", "together", "first", "last", "next",
    "again", "already", "anymore", "forever", "worth", "dupe", "dupes", "vs", "versus",
    "authentic", "fake", "fakes", "original", "real", "legit", "review", "reviews", "haul",
}) - {"me"}  # keep "Fit Me", "Kiss Me"

# Keyword groups. Each entry: label shown on the site -> list of regex patterns.
RECOMMENDED_FOR = {
    "dry skin": [r"\bdry skin\b", r"\bdry patches\b", r"\bflaky\b", r"\bflakes\b"],
    "oily skin": [r"\boily skin\b", r"\boily\b", r"\boil control\b", r"\bsebum\b"],
    "combination skin": [r"\bcombo skin\b", r"\bcombination skin\b"],
    "sensitive skin": [r"\bsensitive skin\b", r"\bsensitive\b", r"\breactive skin\b"],
    "acne": [r"\bacne\b", r"\bbreakouts?\b(?! me)", r"\bpimples?\b", r"\bzits?\b", r"\bblemish(es)?\b"],
    "hormonal acne": [r"\bhormonal acne\b", r"\bcystic\b"],
    "fungal acne": [r"\bfungal acne\b", r"\bfa safe\b", r"\bmalassezia\b"],
    "blackheads": [r"\bblackheads?\b", r"\bsebaceous filaments?\b"],
    "large pores": [r"\bpores?\b"],
    "texture": [r"\btexture\b", r"\btextured skin\b", r"\bbumpy\b"],
    "hyperpigmentation": [r"\bhyperpigmentation\b", r"\bdark spots?\b", r"\bpih\b",
                          r"\bacne scars?\b", r"\bmelasma\b", r"\bdiscoloration\b"],
    "redness / rosacea": [r"\bredness\b", r"\brosacea\b"],
    "eczema": [r"\beczema\b", r"\bdermatitis\b"],
    "damaged barrier": [r"\bbarrier\b", r"\bover-?exfoliat\w*"],
    "dehydrated skin": [r"\bdehydrat\w*\b", r"\btight skin\b"],
    "fine lines & wrinkles": [r"\bfine lines?\b", r"\bwrinkles?\b", r"\banti-?aging\b", r"\bcrow'?s feet\b"],
    "mature skin": [r"\bmature skin\b", r"\b(40|50|60)s\b"],
    "dullness / glow": [r"\bdull\w*\b", r"\bbrighten\w*\b", r"\bglass skin\b"],
    "dark circles": [r"\bdark circles?\b", r"\bunder ?eyes?\b", r"\bpuffy\b", r"\bpuffiness\b"],
    "sun protection": [r"\bspf\b", r"\bsun protection\b", r"\buv\b"],
    "under makeup": [r"\bunder makeup\b", r"\bunder foundation\b", r"\bbefore makeup\b"],
    "no-makeup look": [r"\bno[- ]makeup\b", r"\bnatural look\b", r"\beveryday look\b", r"\bminimal makeup\b"],
    "hooded eyes": [r"\bhooded\b"],
    "oily lids": [r"\boily lids\b"],
    "deep skin tones": [r"\bdeep skin\b", r"\bdark skin\b", r"\bdeep tones?\b", r"\bpoc\b", r"\bwoc\b", r"\bmelanin\b"],
    "fair skin": [r"\bfair skin\b", r"\bpale\b", r"\bvery fair\b"],
    "olive / undertone match": [r"\bolive\b", r"\bundertones?\b"],
    "beginners": [r"\bbeginners?\b", r"\bnew to makeup\b", r"\bnew to skincare\b"],
    "events / weddings": [r"\bwedding\b", r"\bbridal\b", r"\bprom\b", r"\bevent\b"],
    "hot / humid weather": [r"\bhumid\w*\b", r"\bsweat\w*\b", r"\bsummer\b", r"\bheat\b"],
    "cold weather": [r"\bwinter\b", r"\bcold weather\b"],
    "lips": [r"\bchapped\b", r"\bdry lips\b"],
}

PEOPLE_LIKE = {
    "lightweight": [r"\blight ?weight\b", r"\bfeels like nothing\b", r"\bweightless\b"],
    "non-greasy": [r"\bnon-?greasy\b", r"\bnot greasy\b", r"\bnot sticky\b", r"\bnon-?sticky\b"],
    "hydrating": [r"\bhydrat(ing|es|ion)\b", r"\bmoisturizing\b", r"\bplump\w*\b"],
    "gentle": [r"\bgentle\b", r"\bdoesn'?t sting\b", r"\bsoothing\b", r"\bcalming\b"],
    "fragrance-free": [r"\bfragrance[- ]free\b", r"\bunscented\b"],
    "no white cast": [r"\bno white cast\b", r"\bzero white cast\b", r"\bno cast\b"],
    "glowy / dewy": [r"\bglow\w*\b", r"\bdewy\b", r"\bluminous\b", r"\bradiant\b", r"\bglazed\b"],
    "matte finish": [r"\bmatte\b", r"\bblur\w*\b", r"\bsoft focus\b"],
    "natural / skin-like": [r"\bskin-?like\b", r"\bnatural finish\b", r"\blooks like skin\b", r"\bsecond skin\b"],
    "long-lasting": [r"\blong[- ]?lasting\b", r"\blasts all day\b", r"\blong[- ]?wear\w*\b", r"\bstays put\b", r"\ball day\b"],
    "smudge / water-proof": [r"\bsmudge[- ]?proof\b", r"\bwaterproof\b", r"\btransfer[- ]?proof\b", r"\bdoesn'?t smudge\b"],
    "buildable": [r"\bbuildable\b", r"\bbuilds up\b"],
    "blendable": [r"\bblend(s|able|ing)?\b", r"\bmelts into\b"],
    "pigmented": [r"\bpigment(ed|ation)?\b", r"\bpayoff\b", r"\bopaque\b"],
    "full coverage": [r"\bfull coverage\b"],
    "sheer / light coverage": [r"\bsheer\b", r"\blight coverage\b", r"\bmedium coverage\b"],
    "affordable": [r"\baffordable\b", r"\bcheap\b", r"\bbudget\b", r"\bdrugstore\b", r"\bunder \$\d+", r"\bgreat value\b"],
    "worth the hype": [r"\bworth the hype\b", r"\blives up to the hype\b", r"\bworth it\b"],
    "holy grail": [r"\bholy grail\b", r"\bhg\b", r"\bride or die\b"],
    "repurchase": [r"\brepurchas\w*\b", r"\bbackups?\b", r"\bon my \w+ bottle\b"],
    "smells nice": [r"\bsmells? (so )?(amazing|good|nice|great|lovely)\b", r"\bscent is\b"],
    "packaging": [r"\bpackaging\b", r"\bcute\b"],
    "great dupe": [r"\bdupe\b", r"\bdupes\b"],
    "fast-absorbing": [r"\babsorbs? (quickly|fast)\b", r"\bsinks in\b", r"\bquick to absorb\b"],
    "doesn't pill": [r"\bdoesn'?t pill\b", r"\bno pilling\b", r"\blayers well\b"],
    "results / it works": [r"\bgame ?changer\b", r"\bcleared\b", r"\bfaded\b", r"\bdifference\b", r"\bresults\b"],
}

COMPLAINTS = {
    "broke me out": [r"\bbroke me out\b", r"\bbreaks? me out\b", r"\bbreaking me out\b", r"\bpurg\w*\b", r"\bclogged\b"],
    "pilling": [r"\bpill(s|ing|ed)\b"],
    "greasy / sticky": [r"\bgreasy\b", r"\bsticky\b", r"\btacky\b", r"\boily finish\b"],
    "white cast": [r"(?<!no )(?<!zero )\bwhite cast\b", r"\bashy\b"],
    "irritation / stinging": [r"\bburn(s|ed|ing)?\b", r"\bsting(s|ing)?\b", r"\birritat\w*\b", r"\brash\b", r"\breaction\b"],
    "drying": [r"\bdrying\b", r"\bdried out\b", r"\bdries out\b", r"\bstripping\b"],
    "cakey / patchy": [r"\bcakey\b", r"\bpatchy\b", r"\bseparat(es|ing)\b", r"\bcling(s|ing)? to\b"],
    "oxidizes": [r"\boxidi[sz]\w*\b"],
    "creases": [r"\bcreas(es|ing)\b"],
    "fades fast": [r"\bfades? (fast|quickly)\b", r"\bdoesn'?t last\b", r"\bwears off\b"],
    "too expensive": [r"\btoo expensive\b", r"\boverpriced\b", r"\bnot worth (it|the money)\b", r"\bpricey\b"],
    "overhyped": [r"\boverhyped\b", r"\boverrated\b", r"\bdisappoint\w*\b", r"\bunderwhelm\w*\b"],
    "fragrance": [r"\bfragrance\b(?![- ]free)", r"\bperfumey\b", r"\bsmells? (bad|weird|awful|off)\b"],
    "shade range": [r"\bshade range\b", r"\btoo (dark|light|orange|pink)\b"],
    "formula change": [r"\breformulat\w*\b", r"\bnew formula\b"],
}

POSITIVE = [
    r"\blove\b", r"\bloving\b", r"\bobsessed\b", r"\bamazing\b", r"\bholy grail\b", r"\bhg\b",
    r"\brecommend\w*\b", r"\bfavou?rite\b", r"\bfave\b", r"\bbest\b", r"\brepurchas\w*\b",
    r"\bgame ?changer\b", r"\bworks\b", r"\bgreat\b", r"\bperfect\b", r"\bgorgeous\b",
    r"\bbeautiful\b", r"\bincredible\b", r"\bworth\b", r"\bglad\b", r"\bimpressed\b", r"\bsaved\b",
]
NEGATIVE = [
    r"\bhate\b", r"\bbroke me out\b", r"\breturn(ed|ing)?\b", r"\bdisappoint\w*\b", r"\bworst\b",
    r"\bwaste\b", r"\birritat\w*\b", r"\bburn(ed|s|ing)?\b", r"\bawful\b", r"\bmeh\b",
    r"\boverrated\b", r"\boverhyped\b", r"\bterrible\b", r"\bregret\b", r"\bnot worth\b",
    r"\bcakey\b", r"\bdidn'?t work\b", r"\bdoesn'?t work\b", r"\bunderwhelm\w*\b", r"\bugh\b",
]
