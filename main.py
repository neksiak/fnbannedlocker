import re
from PyPDF2 import PdfReader

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
                    
                    url_entry = f"https://www.sportskeeda.com/fortnite-item-shop/item/{filtered_details}"
                    data[category].append(url_entry)

        for category, filename in categories.items():
            sorted_items = sorted(data[category])
            with open(filename, "w") as f:
                f.write("\n".join(sorted_items))
        
        print("Processing complete. Files created for each category.")
    except Exception as e:
        print(f"An error occurred: {e}")

file_path = "EpicGamesAccountData.pdf"
password = "YOUR_PASSWORD_HERE"

process_pdf(file_path, password)
