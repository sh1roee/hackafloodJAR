"""
Hardcoded agricultural price data for Laguna province
Simple format: name, tagalog, price per kilo
"""

LAGUNA_AGRICULTURAL_DATA = {
    "province": "Laguna",
    "last_updated": "December 2024",
    
    "vegetables": [
        {"name": "Tomato", "tagalog": "Kamatis", "price_per_kg": 45.00},
        {"name": "Eggplant", "tagalog": "Talong", "price_per_kg": 38.00},
        {"name": "Pechay (Bokchoy)", "tagalog": "Pechay", "price_per_kg": 32.00},
        {"name": "Ampalaya (Bitter Gourd)", "tagalog": "Ampalaya", "price_per_kg": 55.00},
        {"name": "Sitaw (String Beans)", "tagalog": "Sitaw", "price_per_kg": 42.00},
        {"name": "Okra", "tagalog": "Okra", "price_per_kg": 48.00},
        {"name": "Squash", "tagalog": "Kalabasa", "price_per_kg": 28.00},
        {"name": "Cabbage", "tagalog": "Repolyo", "price_per_kg": 35.00},
        {"name": "Carrots", "tagalog": "Karot", "price_per_kg": 65.00},
        {"name": "Potato", "tagalog": "Patatas", "price_per_kg": 58.00},
        {"name": "Onion", "tagalog": "Sibuyas", "price_per_kg": 72.00},
        {"name": "Garlic", "tagalog": "Bawang", "price_per_kg": 85.00},
        {"name": "Ginger", "tagalog": "Luya", "price_per_kg": 68.00},
        {"name": "Chili Pepper", "tagalog": "Siling Labuyo", "price_per_kg": 95.00},
        {"name": "Bell Pepper", "tagalog": "Siling Berde", "price_per_kg": 78.00},
        {"name": "Lettuce", "tagalog": "Letsugas", "price_per_kg": 52.00},
        {"name": "Cucumber", "tagalog": "Pipino", "price_per_kg": 36.00},
        {"name": "Radish", "tagalog": "Labanos", "price_per_kg": 44.00},
        {"name": "Mustasa (Mustard Greens)", "tagalog": "Mustasa", "price_per_kg": 38.00},
        {"name": "Kangkong (Water Spinach)", "tagalog": "Kangkong", "price_per_kg": 25.00},
    ],
    
    "fruits": [
        {"name": "Pineapple", "tagalog": "Pinya", "price_per_kg": 42.00},
        {"name": "Banana (Lakatan)", "tagalog": "Saging na Lakatan", "price_per_kg": 38.00},
        {"name": "Banana (Saba)", "tagalog": "Saging na Saba", "price_per_kg": 32.00},
        {"name": "Papaya", "tagalog": "Papaya", "price_per_kg": 35.00},
        {"name": "Mango", "tagalog": "Mangga", "price_per_kg": 85.00},
        {"name": "Calamansi", "tagalog": "Calamansi", "price_per_kg": 55.00},
        {"name": "Coconut", "tagalog": "Niyog", "price_per_kg": 28.00},
        {"name": "Guava", "tagalog": "Bayabas", "price_per_kg": 45.00},
        {"name": "Jackfruit", "tagalog": "Langka", "price_per_kg": 38.00},
        {"name": "Pomelo", "tagalog": "Suha", "price_per_kg": 62.00},
        {"name": "Santol", "tagalog": "Santol", "price_per_kg": 48.00},
        {"name": "Star Apple", "tagalog": "Kaimito", "price_per_kg": 52.00},
        {"name": "Avocado", "tagalog": "Abokado", "price_per_kg": 95.00},
        {"name": "Watermelon", "tagalog": "Pakwan", "price_per_kg": 32.00},
        {"name": "Melon", "tagalog": "Melon", "price_per_kg": 48.00},
        {"name": "Dragon Fruit", "tagalog": "Dragon Fruit", "price_per_kg": 125.00},
        {"name": "Rambutan", "tagalog": "Rambutan", "price_per_kg": 68.00},
        {"name": "Lanzones", "tagalog": "Lanzones", "price_per_kg": 75.00},
        {"name": "Durian", "tagalog": "Durian", "price_per_kg": 180.00},
        {"name": "Passion Fruit", "tagalog": "Passion Fruit", "price_per_kg": 88.00},
    ],
    
    "root_crops": [
        {"name": "Cassava", "tagalog": "Kamoteng Kahoy", "price_per_kg": 22.00},
        {"name": "Sweet Potato", "tagalog": "Kamote", "price_per_kg": 35.00},
        {"name": "Taro", "tagalog": "Gabi", "price_per_kg": 42.00},
        {"name": "Yam", "tagalog": "Ube", "price_per_kg": 58.00},
    ],
    
    "grains_legumes": [
        {"name": "Rice (Palay)", "tagalog": "Palay", "price_per_kg": 23.50},
        {"name": "Rice (Bigas)", "tagalog": "Bigas", "price_per_kg": 45.00},
        {"name": "Corn", "tagalog": "Mais", "price_per_kg": 18.00},
        {"name": "Mung Beans", "tagalog": "Munggo", "price_per_kg": 72.00},
        {"name": "Peanuts", "tagalog": "Mani", "price_per_kg": 68.00},
    ]
}


def generate_laguna_context_file(output_path: str = "laguna_agricultural_prices.txt"):
    """Generate a formatted text file from the Laguna agricultural data"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("LAGUNA PROVINCE AGRICULTURAL PRICE DATA\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Province: {LAGUNA_AGRICULTURAL_DATA['province']}\n")
        f.write(f"Last Updated: {LAGUNA_AGRICULTURAL_DATA['last_updated']}\n\n")
        
        f.write("This document contains comprehensive agricultural commodity pricing information\n")
        f.write("for Laguna province. All prices are in Philippine Peso (PHP) per kilogram.\n\n")
        
        # Vegetables
        f.write("-" * 80 + "\n")
        f.write("VEGETABLES (Gulay)\n")
        f.write("-" * 80 + "\n\n")
        for item in LAGUNA_AGRICULTURAL_DATA['vegetables']:
            f.write(f"{item['name']} ({item['tagalog']})\n")
            f.write(f"  Price: ₱{item['price_per_kg']:.2f} per kilogram\n\n")
        
        # Fruits
        f.write("-" * 80 + "\n")
        f.write("FRUITS (Prutas)\n")
        f.write("-" * 80 + "\n\n")
        for item in LAGUNA_AGRICULTURAL_DATA['fruits']:
            f.write(f"{item['name']} ({item['tagalog']})\n")
            f.write(f"  Price: ₱{item['price_per_kg']:.2f} per kilogram\n\n")
        
        # Root Crops
        f.write("-" * 80 + "\n")
        f.write("ROOT CROPS (Halamang Ugat)\n")
        f.write("-" * 80 + "\n\n")
        for item in LAGUNA_AGRICULTURAL_DATA['root_crops']:
            f.write(f"{item['name']} ({item['tagalog']})\n")
            f.write(f"  Price: ₱{item['price_per_kg']:.2f} per kilogram\n\n")
        
        # Grains and Legumes
        f.write("-" * 80 + "\n")
        f.write("GRAINS AND LEGUMES (Butil at Legumes)\n")
        f.write("-" * 80 + "\n\n")
        for item in LAGUNA_AGRICULTURAL_DATA['grains_legumes']:
            f.write(f"{item['name']} ({item['tagalog']})\n")
            f.write(f"  Price: ₱{item['price_per_kg']:.2f} per kilogram\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("END OF DOCUMENT\n")
        f.write("=" * 80 + "\n")
    
    print(f"✅ Laguna agricultural context file generated: {output_path}")
    return output_path


if __name__ == "__main__":
    # Generate the text file when this module is run directly
    import os
    
    # Save to downloads/price_index directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "downloads", "price_index")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "laguna_agricultural_prices.txt")
    generate_laguna_context_file(output_path)
