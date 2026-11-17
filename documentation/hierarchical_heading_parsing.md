# over view

Diamond organized its Customer Order Form (_COF.txt) into a predictable hierarchy of Major Category Headers, Publisher/Tier Subheaders, and Imprint/Sub-line Sub-subheaders before transitioning into non-comic merchandise sections.
Because publisher contracts and tiers shifted over the 20+ years of archived files (such as DC leaving in 2020, Marvel shifting in 2021, and the introduction of the "Deluxe Tier" in 2022), the exact roster of publishers inside each tier changed over time.

## 1. Top-Level Structure of the Order Form

In the plain-text order forms, Diamond separated the comic/book portion from the merchandise portion using major all-caps category headers (often padded with dashes or equals signs, such as --- PREMIER PUBLISHERS --- or COMICS & GRAPHIC NOVELS):
* Premier Publishers Section: Every Premier publisher gets its own dedicated top-level section block at the very front of the file, ordered either alphabetically or by contract priority (historically DARK HORSE COMICS, DC COMICS, IDW PUBLISHING, IMAGE COMICS, MARVEL COMICS).
* Deluxe Publishers Section (Added September 2022): Introduced as DELUXE PUBLISHERS (or DELUXE TIER) right after the Premier section to give mid-sized exclusive partners dedicated placement.
* The Umbrella Comics Section (COMICS & GRAPHIC NOVELS): Every other comic, graphic novel, trade paperback, and manga publisher is grouped alphabetically under one giant umbrella header—usually titled COMICS & GRAPHIC NOVELS (or COMICS/GRAPHIC NOVELS in older files). Inside this section, each publisher name appears as an all-caps subheader above its block of SKUs.
* The Merchandise Boundary (Where to Stop Parsing): Right after the last alphabetical publisher in COMICS & GRAPHIC NOVELS (typically ZENESCOPE ENTERTAINMENT), Diamond begins the non-comic sections. Your parser can safely stop or switch modes once it hits any of these top-level headers:
    * MAGAZINES (Note: occasionally contains comic-adjacent magazines like Heavy Metal or Mad, though most are hobby/pop-culture)
    * BOOKS (Prose novels, art books, and reference guides)
    * COLLECTIBLES & NOVELTIES (or TOYS, STATUES & MODELS)
    * APPAREL
    * TRADING CARDS
    * GAMES
    * SUPPLIES (Bags, boards, boxes)

## 2. Publishers by Diamond Tier

Because Diamond changed its publisher tiers over the years, your parser should recognize these specific publisher headers across the different eras:
* Premier Publishers (Dedicated Front-of-Book Sections):
    * The Core Five (2000s–2020): Dark Horse Comics, DC Comics (left in 2020), IDW Publishing, Image Comics, and Marvel Comics.
    * Later Premier Additions (2010s–2024): BOOM! Studios, Dynamite Entertainment, and Titan Comics were elevated to Premier status at various points in the late 2010s and 2020s.
* Deluxe Publishers (Dedicated Section, Sept 2022–2025):
    * Diamond created this tier specifically for four publishers: ABLAZE Publishing, AfterShock Comics, Frank Miller Presents (FMP), and Titan Comics.
* Major Publishers Inside COMICS & GRAPHIC NOVELS (All Other Publishers):
    * Hundreds of indie and manga publishers rotated through this alphabetical section, including Aardvark-Vanaheim, Abstract Studio, AHOY Comics, Albatross Funnybooks, Antarctic Press, Archie Comic Publications, Aspen MLT, Avatar Press, AWA (Artists Writers & Artisans), Black Mask Studios, Bongo Comics, Chronicle Books, Cobra / Action Lab, Drawn & Quarterly, DSTLRY, Fantagraphics Books, First Second, Kodansha Comics, Legendary Comics, Mad Cave Studios, NBM, Oni Press, Papercutz, Rebellion / 2000 AD, Scholastic, Scout Comics, Seven Seas Entertainment, Source Point Press, Tokyopop, Top Shelf Productions, UDON Entertainment, Valiant Entertainment, Vault Comics, VIZ Media, Yen Press, and Zenescope Entertainment.

## 3. Sub-Subheaders & Imprints (How to Avoid False Publishers)

Inside both the Premier sections and the COMICS & GRAPHIC NOVELS section, Diamond frequently inserted sub-subheaders that look visually similar to publisher names. If your parser treats every non-SKU text line as a new publisher, these will overwrite the true publisher:
* Publisher Imprints: Major publishers group their lines under sub-headers (for example, VERTIGO, WILDSTORM, and DC BLACK LABEL under DC COMICS; ICON or MAX under MARVEL COMICS; SKYBOUND or TOP COW under IMAGE COMICS; ARCHAIA under BOOM! STUDIOS).
* Product-Type Subheaders: Inside a publisher's block, Diamond frequently inserts divider lines for GRAPHIC NOVELS, TRADE PAPERBACKS, HARDCOVERS, MANGA, REPRINTS, or NEW PRINTINGS to separate single issues from collected editions.
* Release Date Subheaders: Newer files (roughly 2018–2025) insert lines like In-Store Date: MM/DD/YYYY or FOC: MM/DD/YYYY within each publisher block.
* Franchise / Event Banners: Special crossover events or major lines occasionally get a banner line (such as STAR WARS under Dark Horse or Marvel, or X-MEN / SPIDER-MAN blocks).

## 4. Structural Parsing Strategy

Instead of relying solely on a hardcoded list of hundreds of indie publishers, you can reliably identify the Publisher vs. Sub-header using structural state rules:
1. Before COMICS & GRAPHIC NOVELS: Every major header you encounter before hitting the COMICS & GRAPHIC NOVELS banner is a Premier (or Deluxe) publisher. Any secondary text lines inside that block before the next Premier publisher header are Imprints or Format Subheaders (e.g., GRAPHIC NOVELS).
2. Inside COMICS & GRAPHIC NOVELS: Publishers are listed in strict alphabetical order (A through Z). If you encounter a header line (a line with no leading MMMYYNNNN SKU and no $ price) that follows alphabetical progression relative to the previous publisher—and is not a reserved format keyword (GRAPHIC NOVELS, MANGA, TRADE PAPERBACKS, HARDCOVERS, COMICS, REPRINTS, MERCHANDISE)—it is a new Publisher. If it breaks alphabetical order (e.g., VERTIGO appearing after DC COMICS, or GRAPHIC NOVELS appearing under FANTAGRAPHICS), treat it as a sub-header/imprint belonging to the current active publisher.
3. Stop Trigger: Terminate comic parsing as soon as your parser reads MAGAZINES, BOOKS, COLLECTIBLES & NOVELTIES, TOYS, GAMES, or SUPPLIES.

# architecture / solution possiblities

we maintain some tables as Slowly Changing Dimensions (SCD) to track publisher changes and header changes over time. 

for headers we'd maintain their ID, name, level (1, 2, 3, ...) and start & end effective dates. The headings would be used to identify what the active publisher is for the items in the current section.

For publishers we'd maintain their ID, name, tier, and start & end effective dates.

