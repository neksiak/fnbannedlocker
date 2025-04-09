# Fortnite Banned Account Locker Checker

> **Note**: Fortnite has announced they're unbanning currently banned accounts, so this tool is less necessary now unless you get banned again or you didn't get unbanned.

This tool allows you to view all your Fortnite cosmetic items by extracting them from your Epic Games account data, even if your account is banned.


## Features

- Extracts all cosmetic items from your Epic Games account data PDF
- Organizes items by category (outfits, back blings, pickaxes, etc.)
- Creates high-quality image grids for each category
- Shows item rarity with correct background colors
- Caches downloaded images for quicker subsequent runs

## Categories Supported

- Outfits (`AthenaCharacter`)
- Back Blings (`AthenaBackpack`)
- Pickaxes (`AthenaPickaxe`)
- Gliders (`AthenaGlider`)
- Contrails (`AthenaSkyDiveContrail`)
- Emotes (only dances, doesn't support sprays and emojis) (`AthenaDance`)
- Music Packs (`AthenaMusicPack`)
- Wraps (`AthenaItemWrap`)

## Requirements

- Python 3.6+
- Required libraries: `requests`, `PIL`, `PyPDF2`, `unidecode`
- Internet connection (to download cosmetics data and item images)

## Installation

1. Clone this repository or download the files
2. Install required libraries:
   ```bash
   pip install requests Pillow PyPDF2 unidecode
   ```

## Usage

### Step 1: Request Your Epic Games Account Data

1. Go to [Epic Games Account Settings](https://www.epicgames.com/account/personal)
2. Request a copy of your account data
3. Wait for the email (in rare cases can take a few days) and download your data

### Step 2: Prepare Your Files

1. Place your Epic Games account data PDF in the same folder as the script
2. Rename it to `EpicGamesAccountData.pdf` or update the file path in the script

### Step 3: Run the Script

On first run, the script will:

- Download the latest Fortnite cosmetics data
- Extract your items from the PDF (using the password provided in the PDF email)
- Download images for all your cosmetic items
- Create image grids for each category

### Step 4: View Your Collection

After running, you'll have image files for each category:

- `AthenaCharacter.png` (Outfits)
- `AthenaBackpack.png` (Backpacks)
- `AthenaPickaxe.png` (Pickaxes)
- And more...
(There are also text files with codenames if youre interested in that)


## Known Issues
- **Pets don't display properly**
- **Some Items may have black/gray background**
- **Text may overlap on certain items with longer names**

## How It Works

- The script extracts cosmetic item IDs from your Epic Games account data
- It downloads current cosmetic data from Fortnite's API
- It matches your items against the database
- Images are downloaded for each item and cached locally
- Image grids are created with proper formatting and color coding

## Credits

- Uses the [Fortnite-API.com](https://fortnite-api.com/) for cosmetics data

Need help or have suggestions? Open an issue on this repo!
