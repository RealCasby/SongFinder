"""Build INSTRUMENTALS.md from data/tracklists.md and data/results.tsv."""
import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load_tracklists():
    albums, cur = [], None
    for line in (DATA / "tracklists.md").read_text().splitlines():
        m = re.match(r"## (.+?) - (.+?) \((\d{4})\)\s*(?:\((.*)\))?$", line)
        if m:
            artist, album, year, note = m.groups()
            cur = {"artist": artist, "album": album, "year": year, "note": note, "tracks": []}
            albums.append(cur)
        elif cur and line.strip() and not line.startswith("#"):
            cur["tracks"] = [t.strip() for t in line.split(";") if t.strip()]
    return albums


def load_results():
    res = {}
    for line in (DATA / "results.tsv").read_text().splitlines():
        parts = (line.split("\t") + [""] * 5)[:5]
        key, track, url, title, alt = parts
        res[(key, track)] = {"url": url, "title": title, "alt": alt}
    return res


def search_url(artist, track):
    q = f"{artist} {track} instrumental"
    return "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(q)


def md_escape(s):
    return s.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def main():
    albums, res = load_tracklists(), load_results()
    used, counts = set(), {"video": 0, "playlist": 0, "search": 0}
    order = ["Yeat", "Playboi Carti", "EsDeeKid", "Ken Carson", "Destroy Lonely", "Homixide Gang", "Lil Uzi Vert"]
    albums.sort(key=lambda a: (order.index(a["artist"]), a["year"]))

    body = []
    for artist in order:
        body.append(f"\n## {artist}\n")
        for a in [x for x in albums if x["artist"] == artist]:
            key = f"{a['artist']}|{a['album']}"
            body.append(f"\n### {a['album']} ({a['year']})\n")
            if a["note"]:
                body.append(f"_Tracklist note: {a['note']}_\n")
            body.append("| # | Track | Instrumental | Backup |")
            body.append("|---|---|---|---|")
            for i, t in enumerate(a["tracks"], 1):
                r = res.get((key, t))
                s = search_url(a["artist"], t)
                if r and r["url"] and "playlist?list=" not in r["url"]:
                    used.add((key, t)); counts["video"] += 1
                    link = f"✅ [{md_escape(r['title'])}]({r['url']})"
                    backup = f"[alt]({r['alt']})" if r["alt"] else f"[search]({s})"
                elif r and r["url"]:
                    used.add((key, t)); counts["playlist"] += 1
                    link = f"📂 [Album instrumentals playlist]({r['url']})"
                    backup = f"[search]({s})"
                else:
                    if r: used.add((key, t))
                    counts["search"] += 1
                    link = f"🔎 [YouTube search]({s})" + (" (none found)" if r else "")
                    backup = ""
                body.append(f"| {i} | {md_escape(t)} | {link} | {backup} |")

    total = sum(counts.values())
    head = [
        "# Instrumental Links",
        "",
        "YouTube instrumentals for every track on the requested albums.",
        "",
        "**Legend**",
        "- ✅ a specific instrumental video I found (official instrumental where one exists, otherwise the closest remake / reprod)",
        "- 📂 no single video found, so this links an album instrumentals playlist that should include the track",
        "- 🔎 a YouTube search for `<artist> <track> instrumental` (not searched yet, or nothing found)",
        "",
        f"**Coverage:** {counts['video']} direct videos, {counts['playlist']} playlist fallbacks, "
        f"{counts['search']} search links, {total} tracks total.",
        "",
        "Most of these uploads are fan remakes or vocal-removed rips rather than label releases, and"
        " uploads can be taken down. Use the backup link if the main one is dead.",
    ]
    (ROOT / "INSTRUMENTALS.md").write_text("\n".join(head + body) + "\n")

    stray = set(res) - used
    for k in sorted(stray):
        print("UNMATCHED result:", k)
    print(counts, total)


if __name__ == "__main__":
    main()
