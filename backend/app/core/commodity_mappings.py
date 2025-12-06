"""
Commodity name mappings between Tagalog and English
For handling queries in both languages
"""

# NCR Cities and Municipality Mapping
# Maps city/municipality names to their region (NCR)
NCR_CITIES = {
    # 16 Cities (Highly Urbanized Cities)
    "caloocan": "NCR",
    "las piñas": "NCR",
    "las pinas": "NCR",
    "makati": "NCR",
    "malabon": "NCR",
    "mandaluyong": "NCR",
    "manila": "NCR",
    "maynila": "NCR",
    "marikina": "NCR",
    "muntinlupa": "NCR",
    "navotas": "NCR",
    "parañaque": "NCR",
    "paranaque": "NCR",
    "pasay": "NCR",
    "pasig": "NCR",
    "quezon city": "NCR",
    "qc": "NCR",
    "san juan": "NCR",
    "taguig": "NCR",
    "valenzuela": "NCR",
    
    # 1 Municipality
    "pateros": "NCR",
    
    # Common aliases
    "metro manila": "NCR",
    "ncr": "NCR",
    "national capital region": "NCR",
}

# Laguna Cities and Municipalities Mapping
LAGUNA_CITIES = {
    # Cities
    "calamba": "Laguna",
    "calamba city": "Laguna",
    "san pablo": "Laguna",
    "san pablo city": "Laguna",
    "cabuyao": "Laguna",
    "cabuyao city": "Laguna",
    "biñan": "Laguna",
    "binan": "Laguna",
    "santa rosa": "Laguna",
    "city of santa rosa": "Laguna",
    "san pedro": "Laguna",
    
    # Municipalities
    "bay": "Laguna",
    "cavinti": "Laguna",
    "pagsanjan": "Laguna",
    "alaminos": "Laguna",
    "lumban": "Laguna",
    "majayjay": "Laguna",
    "luisiana": "Laguna",
    "calauan": "Laguna",
    "famy": "Laguna",
    "los baños": "Laguna",
    "los banos": "Laguna",
    "liliw": "Laguna",
    "mabitac": "Laguna",
    "siniloan": "Laguna",
    "santa maria": "Laguna",
    "paete": "Laguna",
    "pangil": "Laguna",
    "nagcarlan": "Laguna",
    "santa cruz": "Laguna",
    "pakil": "Laguna",
    "kalayaan": "Laguna",
    "pila": "Laguna",
    "rizal": "Laguna",
    "victoria": "Laguna",
    "magdalena": "Laguna",
    
    # Barangays and areas
    "canlubang": "Laguna",
    "punta": "Laguna",
    "kay-anlog": "Laguna",
    "parian": "Laguna",
    "turbina": "Laguna",
    "malitlit": "Laguna",
    "del remedio": "Laguna",
    "santo angel": "Laguna",
    "banilan": "Laguna",
    "mamatid": "Laguna",
    
    # Province name
    "laguna": "Laguna",
}

# Combined location mapping
ALL_LOCATIONS = {**NCR_CITIES, **LAGUNA_CITIES}

# Tagalog to English mapping
TAGALOG_TO_ENGLISH = {
    # Vegetables
    "kamatis": "tomato",
    "talong": "eggplant",
    "sibuyas": "onion",
    "bawang": "garlic",
    "repolyo": "cabbage",
    "patatas": "potato",
    "kalabasa": "squash",
    "sitaw": "string beans",
    "pechay": "pechay",
    "kangkong": "water spinach",
    "labanos": "radish",
    "singkamas": "turnip",
    "sayote": "chayote",
    "pipino": "cucumber",
    "sili": "chili",
    
    # Meat
    "manok": "chicken",
    "baboy": "pork",
    "baka": "beef",
    "karne": "meat",
    
    # Fish/Seafood
    "isda": "fish",
    "bangus": "milkfish",
    "tilapia": "tilapia",
    "galunggong": "mackerel scad",
    "alumahan": "mackerel",
    "pusit": "squid",
    "hipon": "shrimp",
    "sugpo": "prawn",
    "tahong": "mussel",
    "talaba": "oyster",
    
    # Grains/Staples
    "bigas": "rice",
    "mais": "corn",
    "harina": "flour",
    
    # Fruits
    "saging": "banana",
    "mangga": "mango",
    "papaya": "papaya",
    "pinya": "pineapple",
    "pakwan": "watermelon",
    "melon": "melon",
    "ubas": "grapes",
    "mansanas": "apple",
    "dalandan": "orange",
    "kalamansi": "calamansi",
    
    # Common price-related words
    "presyo": "price",
    "halaga": "price",
    "magkano": "how much",
    "sa": "in",
    "kilo": "kilogram",
    "tali": "bundle",
    
    # Specifications
    "malaki": "large",
    "maliit": "small",
    "katamtaman": "medium",
    "sariwa": "fresh",
    "prito": "fried",
}

# English to Tagalog mapping (reverse)
ENGLISH_TO_TAGALOG = {v: k for k, v in TAGALOG_TO_ENGLISH.items()}

# Category mappings
CATEGORY_MAPPING = {
    "rice": ["bigas", "rice", "palay"],
    "fish": ["isda", "fish", "bangus", "tilapia", "galunggong"],
    "meat": ["karne", "meat", "manok", "chicken", "baboy", "pork", "baka", "beef"],
    "vegetables": ["gulay", "vegetables", "kamatis", "tomato", "talong", "eggplant"],
    "fruits": ["prutas", "fruits", "saging", "banana", "mangga", "mango"],
}


def translate_tagalog_to_english(text: str) -> str:
    """
    Translate Tagalog commodity names to English in a given text
    
    Args:
        text: Input text that may contain Tagalog words
        
    Returns:
        Text with Tagalog commodity names translated to English
    """
    translated = text.lower()
    
    for tagalog, english in TAGALOG_TO_ENGLISH.items():
        # Replace whole words only
        import re
        pattern = r'\b' + re.escape(tagalog) + r'\b'
        translated = re.sub(pattern, english, translated, flags=re.IGNORECASE)
    
    return translated


def get_commodity_variations(commodity: str) -> list:
    """
    Get both English and Tagalog variations of a commodity name
    
    Args:
        commodity: Commodity name in English or Tagalog
        
    Returns:
        List of variations [english, tagalog]
    """
    commodity_lower = commodity.lower()
    
    variations = [commodity_lower]
    
    # Check if it's Tagalog, add English
    if commodity_lower in TAGALOG_TO_ENGLISH:
        variations.append(TAGALOG_TO_ENGLISH[commodity_lower])
    
    # Check if it's English, add Tagalog
    if commodity_lower in ENGLISH_TO_TAGALOG:
        variations.append(ENGLISH_TO_TAGALOG[commodity_lower])
    
    return list(set(variations))


def extract_commodity_from_query(query: str) -> str:
    """
    Extract commodity name from a natural language query
    
    Args:
        query: User query like "Magkano kamatis?" or "Price of tomatoes"
        
    Returns:
        Extracted commodity name
    """
    query_lower = query.lower()
    
    # Check for Tagalog commodities
    for tagalog in TAGALOG_TO_ENGLISH.keys():
        if tagalog in query_lower:
            return TAGALOG_TO_ENGLISH[tagalog]
    
    # Check for English commodities
    for english in ENGLISH_TO_TAGALOG.keys():
        if english in query_lower:
            return english
    
    return ""


def extract_location_from_query(query: str) -> str:
    """
    Extract location from query and map cities to their region (NCR or Laguna)
    
    Args:
        query: User query like "Magkano kamatis sa Pasig" or "rice price in Laguna"
        
    Returns:
        Region name (e.g., "NCR" or "Laguna") or original location if not a known city
    """
    query_lower = query.lower()
    
    # Check for all known locations (NCR + Laguna)
    for location, region in ALL_LOCATIONS.items():
        # Use word boundaries to avoid partial matches
        import re
        pattern = r'\b' + re.escape(location) + r'\b'
        if re.search(pattern, query_lower):
            return region
    
    # Return empty string if no location found
    return ""
