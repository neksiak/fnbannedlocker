import concurrent.futures
import difflib
import json
import math
import os
import re
import threading
import time
import traceback
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfReader
from unidecode import unidecode

categories = {
    "AthenaCharacter": "AthenaCharacter.txt",
    "AthenaBackpack": "AthenaBackpack.txt",
    "AthenaPickaxe": "AthenaPickaxe.txt",
    "AthenaGlider": "AthenaGlider.txt",
    "AthenaSkyDiveContrail": "AthenaSkyDiveContrail.txt",
    "AthenaDance": "AthenaDance.txt",
    "AthenaMusicPack": "AthenaMusicPack.txt",
    "AthenaItemWrap": "AthenaItemWrap.txt",
}

pattern = re.compile(r"(\bAthena\w+):\s*(.+)", re.IGNORECASE)


class ImageDownloader:
    def __init__(self, max_workers=10, cache_dir="image_cache"):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.cache_dir = cache_dir
        self.max_workers = max_workers
        self.rate_limit = threading.Semaphore(max_workers)
        
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def download_image(self, url, size):
        if not url:
            return None
            
        cache_filename = os.path.join(
            self.cache_dir, 
            re.sub(r'[^\w]', '_', url) + f"_{size[0]}x{size[1]}.png"
        )
        
        if os.path.exists(cache_filename):
            try:
                return Image.open(cache_filename)
            except Exception:
                pass
        
        with self.rate_limit:
            try:
                response = self.session.get(url, timeout=5)
                response.raise_for_status()
                
                img = Image.open(BytesIO(response.content))
                img = img.resize(size)
                
                img.save(cache_filename)
                
                return img
            except Exception as e:
                print(f"Error downloading {url}: {e}")
                return None


def normalize_string(s):
    if not s:
        return ""
    return re.sub(r'[^a-z0-9]', '', unidecode(s).lower())


def process_pdf(file_path, password=None):
    try:
        reader = PdfReader(file_path)
        
        if reader.is_encrypted:
            if password:
                reader.decrypt(password)
            else:
                raise ValueError("Password is required for encrypted PDF.")

        data = {key: [] for key in categories}

        for page in reader.pages:
            text = page.extract_text()
            matches = pattern.findall(text)
            for category, details in matches:
                if category in categories:
                    filtered_details = re.sub(r'1$', '', details.strip())
                    filtered_details = filtered_details.replace('_', '-')
                    
                    if category == "AthenaDance" and not filtered_details.startswith("eid-"):
                        continue
                        
                    url_entry = filtered_details
                    data[category].append(url_entry)

        for category, filename in categories.items():
            sorted_items = sorted(data[category])
            with open(filename, "w") as f:
                f.write("\n".join(sorted_items))
        
        print("Processing complete. Files created for each category.")
    except Exception as e:
        print(f"An error occurred: {e}")


def download_fortnite_cosmetics():
    url = "https://fortnite-api.com/v2/cosmetics/br"
    
    print("Downloading Fortnite cosmetics data...")
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Successfully retrieved {len(data['data'])} cosmetic items")
            
            with open("fortnite_cosmetics.json", "w") as f:
                json.dump(data, f, indent=4)
            print("Data saved to fortnite_cosmetics.json")
            return True
        else:
            print(f"Error: API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


def ensure_cosmetics_data():
    if not os.path.exists("fortnite_cosmetics.json"):
        print("Fortnite cosmetics data not found. Downloading...")
        return download_fortnite_cosmetics()
    else:
        print("Using existing Fortnite cosmetics data.")
        return True


def create_locker_image():
    print("Starting create_locker_image function...")
    start_time = time.time()
    
    try:
        print("Loading cosmetics data from JSON file...")
        load_start = time.time()
        with open("fortnite_cosmetics.json", "r") as f:
            cosmetics_data = json.load(f)
        print(f"JSON loaded in {time.time() - load_start:.2f} seconds")
        
        print("Creating optimized lookup dictionaries...")
        dict_start = time.time()
        
        cosmetics_lookup = {}
        type_specific_lookup = {cat: {} for cat in categories}
        
        for item in cosmetics_data.get("data", []):
            if isinstance(item, dict) and "id" in item and "type" in item:
                item_id = item["id"].lower()
                cosmetics_lookup[item_id] = item
                
                item_type = item.get("type", {}).get("backendValue", "")
                if item_type in type_specific_lookup:
                    type_specific_lookup[item_type][item_id] = item
                    
                    if "name" in item:
                        normalized_name = normalize_string(item["name"])
                        type_specific_lookup[item_type][normalized_name] = item
                        
                        if item_type == "AthenaGlider" and "umbrella" in item_id:
                            type_specific_lookup[item_type]["umbrella"] = item
                        
                        if "-" in item_id:
                            without_prefix = item_id.split("-", 1)[1]
                            type_specific_lookup[item_type][without_prefix] = item
        
        print(f"Optimized dictionaries created in {time.time() - dict_start:.2f} seconds")
        
        downloader = ImageDownloader(max_workers=15, cache_dir="cosmetics_cache")
        fuzzy_match_count = {}
        
        def find_item_match(item_id, category):
            item_id = item_id.strip().lower()
            
            if item_id in cosmetics_lookup:
                item = cosmetics_lookup[item_id]
                if item.get("type", {}).get("backendValue", "") == category:
                    return item
            
            if item_id in type_specific_lookup[category]:
                return type_specific_lookup[category][item_id]
            
            if category == "AthenaBackpack" and "petcarrier-" in item_id:
                for id_key, item in type_specific_lookup[category].items():
                    if "petcarrier-" in id_key and id_key.split("petcarrier-")[1] in item_id:
                        return item
                    elif "petcarrier-" in id_key and item_id.replace("petcarrier-", "") in id_key:
                        return item
            
            if "-" in item_id:
                without_prefix = item_id.split("-", 1)[1]
                if without_prefix in type_specific_lookup[category]:
                    return type_specific_lookup[category][without_prefix]
            
            variation = item_id.replace("-", "_")
            if variation in type_specific_lookup[category]:
                return type_specific_lookup[category][variation]
            
            if category == "AthenaGlider" and "umbrella" in item_id:
                if "umbrella" in type_specific_lookup[category]:
                    return type_specific_lookup[category]["umbrella"]
            
            normalized_id = normalize_string(item_id)
            
            if fuzzy_match_count.get(category, 0) < 10:
                fuzzy_match_count[category] = fuzzy_match_count.get(category, 0) + 1
                
                best_match = None
                best_score = 0.65
                
                for id_key, item in type_specific_lookup[category].items():
                    if len(id_key) < 3:
                        continue
                        
                    similarity = difflib.SequenceMatcher(None, normalized_id, id_key).ratio()
                    if similarity > best_score:
                        best_score = similarity
                        best_match = item
                
                if best_match:
                    return best_match
            
            return None
        
        def process_category(category):
            category_start = time.time()
            print(f"\nStarting category: {category}")
            
            if not os.path.exists(f"{category}.txt"):
                print(f"File not found: {category}.txt")
                return None
                
            with open(f"{category}.txt", "r") as f:
                item_ids = [line.strip() for line in f.read().strip().split("\n")]
            
            if not item_ids:
                print(f"No items found in {category}.txt")
                return None
            
            print(f"Category: {category}, Items found: {len(item_ids)}")
            
            item_count = len(item_ids)
            cols = math.ceil(math.sqrt(item_count * 1.5))
            rows = math.ceil(item_count / cols)
            
            thumbnail_size = max(60, min(150, int(900 / cols)))
            horizontal_spacing = max(8, thumbnail_size // 10)
            vertical_spacing = max(40, thumbnail_size // 2)
            text_height = max(16, thumbnail_size // 6)
            padding = 3
            
            margin = 60
            canvas_width = margin * 2 + cols * (thumbnail_size + horizontal_spacing)
            canvas_height = margin * 2 + rows * (thumbnail_size + vertical_spacing + text_height)
            
            locker_image = Image.new('RGB', (canvas_width, canvas_height), (25, 25, 35))
            draw = ImageDraw.Draw(locker_image)
            
            font_size = max(12, thumbnail_size // 8)
            title_font_size = max(24, font_size * 1.8)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
                title_font = ImageFont.truetype("arial.ttf", title_font_size)
            except IOError:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()
            
            category_name = category.replace("Athena", "")
            title = f"{category_name} ({item_count} ITEMS)"
            draw.text((canvas_width//2, margin//2), title, fill=(255, 255, 255), font=title_font, anchor="ma")
            
            found_count = 0
            not_found_count = 0
            
            def process_item(args):
                i, item_id = args
                row = i // cols
                col = i % cols
                
                x = margin + col * (thumbnail_size + horizontal_spacing)
                y = margin + row * (thumbnail_size + vertical_spacing + text_height) + 60
                
                result = {
                    'i': i, 'x': x, 'y': y, 'item_id': item_id,
                    'found': False, 'image': None, 'item_data': None
                }
                
                try:
                    item_data = find_item_match(item_id, category)
                    
                    if item_data and "images" in item_data:
                        result['found'] = True
                        result['item_data'] = item_data
                        
                        icon_url = None
                        for img_key in ["icon", "smallIcon", "featured"]:
                            if img_key in item_data["images"] and item_data["images"][img_key]:
                                icon_url = item_data["images"][img_key]
                                break
                                
                        if not icon_url and "lego" in item_data["images"]:
                            for lego_key in ["large", "small"]:
                                if lego_key in item_data["images"]["lego"] and item_data["images"]["lego"][lego_key]:
                                    icon_url = item_data["images"]["lego"][lego_key]
                                    break
                        
                        if icon_url:
                            image = downloader.download_image(icon_url, (thumbnail_size, thumbnail_size))
                            if image:
                                result['image'] = image
                except Exception as e:
                    print(f"Error processing {item_id}: {e}")
                
                return result
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                item_results = list(executor.map(process_item, enumerate(item_ids)))
            
            for result in item_results:
                i = result['i']
                x = result['x']
                y = result['y']
                item_id = result['item_id']
                
                if result['found'] and result['image']:
                    found_count += 1
                    
                    item_data = result['item_data']
                    rarity = item_data.get("rarity", {}).get("value", "common")
                    bg_colors = {
                        "common": (150, 150, 150),
                        "uncommon": (96, 170, 58),
                        "rare": (73, 172, 242),
                        "epic": (177, 91, 226),
                        "legendary": (211, 120, 65),
                        "mythic": (235, 227, 88),
                        "marvel": (197, 51, 52),
                        "dc": (84, 117, 199),
                        "icon": (63, 181, 181),
                        "starwars": (32, 85, 128),
                    }
                    bg_color = bg_colors.get(rarity, (100, 100, 100))
                    
                    draw.rectangle([x-2, y-2, x+thumbnail_size+2, y+thumbnail_size+2], fill=(0, 0, 0))
                    draw.rectangle([x, y, x+thumbnail_size, y+thumbnail_size], fill=bg_color)
                    
                    locker_image.paste(result['image'], (x, y), mask=result['image'] if result['image'].mode == 'RGBA' else None)
                    
                    name_to_display = item_data.get("name", item_id)
                    if len(name_to_display) > thumbnail_size // 4:
                        name_to_display = name_to_display[:thumbnail_size // 4] + "..."
                    
                    text_y = y + thumbnail_size + 8
                    
                    text_width = draw.textlength(name_to_display, font=font)
                    
                    bg_rect = [
                        x + (thumbnail_size - text_width) // 2 - padding,
                        text_y - padding,
                        x + (thumbnail_size + text_width) // 2 + padding,
                        text_y + font_size + padding
                    ]
                    
                    draw.rectangle(bg_rect, fill=(0, 0, 0, 180))
                    
                    shadow_offset = 1
                    draw.text(
                        (x + thumbnail_size // 2 + shadow_offset, text_y + shadow_offset), 
                        name_to_display, 
                        fill=(0, 0, 0), 
                        font=font, 
                        anchor="mt"
                    )
                    draw.text(
                        (x + thumbnail_size // 2, text_y), 
                        name_to_display, 
                        fill=(255, 255, 255), 
                        font=font, 
                        anchor="mt"
                    )
                else:
                    not_found_count += 1
                    draw.rectangle([x, y, x+thumbnail_size, y+thumbnail_size], fill=(50, 50, 50))
                    draw.rectangle([x+3, y+3, x+thumbnail_size-3, y+thumbnail_size-3], fill=(40, 40, 40))
                    
                    display_name = item_id
                    if len(display_name) > 12:
                        display_name = display_name[:10] + "..."
                    
                    draw.text(
                        (x + thumbnail_size // 2, y + thumbnail_size // 2 - 10), 
                        "?", 
                        fill=(180, 180, 180), 
                        font=title_font, 
                        anchor="mm"
                    )
                    
                    draw.text(
                        (x + thumbnail_size // 2, y + thumbnail_size // 2 + 15), 
                        display_name, 
                        fill=(180, 180, 180), 
                        font=font, 
                        anchor="mm"
                    )
                    
                    text_y = y + thumbnail_size + 8
                    draw.rectangle(
                        [x, text_y, x + thumbnail_size, text_y + font_size + 6],
                        fill=(100, 30, 30)
                    )
                    draw.text(
                        (x + thumbnail_size // 2, text_y + 3),
                        "Not Found", 
                        fill=(255, 200, 200), 
                        font=font, 
                        anchor="mt"
                    )
            
            filename = f"{category}.png"
            locker_image.save(filename)
            
            category_time = time.time() - category_start
            print(f"Created image for {category}: {found_count} items found, {not_found_count} not found")
            print(f"Total time for {category}: {category_time:.2f}s")
            
            return {
                'category': category,
                'found': found_count,
                'not_found': not_found_count,
                'time': category_time
            }
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_category, category) for category in categories]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
    
    except Exception as e:
        print(f"Error in create_locker_image: {e}")
        traceback.print_exc()
    
    total_time = time.time() - start_time
    print(f"\nTotal execution time: {total_time:.2f} seconds")
    print("Summary:")
    for result in sorted(results, key=lambda x: x['category']):
        print(f"  {result['category']}: {result['found']} found, {result['not_found']} not found, {result['time']:.2f}s")


def main():
    file_path = "EpicGamesAccountData.pdf"
    
    if not os.path.exists(file_path):
        print(f"\nError: File '{file_path}' not found.")
        alt_path = input("Enter the path to your Epic Games Account Data PDF (or press Enter to exit): ")
        if not alt_path:
            print("Exiting program.")
            return
        file_path = alt_path
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' still not found. Exiting.")
            return
    
    try:
        reader = PdfReader(file_path)
        is_encrypted = reader.is_encrypted
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return
    
    password = None
    if is_encrypted:
        print("\nThe PDF file is encrypted and requires a password.")
        print("The password should be in the email you received from Epic Games.")
        
        while True:
            password = input("Enter password (or press Enter to exit): ")
            
            if not password:
                print("No password entered. Exiting program.")
                return
                
            try:
                test_reader = PdfReader(file_path)
                test_reader.decrypt(password)
                print("Password accepted!")
                break
            except Exception:
                print("Incorrect password. Please try again.")
    
    process_pdf(file_path, password)

    if ensure_cosmetics_data():
        create_locker_image()
    else:
        print("Failed to obtain cosmetics data. Cannot create locker image.")


if __name__ == "__main__":
    main()
