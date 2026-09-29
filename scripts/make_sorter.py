"""Generate scripts/sort_not_sorted.ps1 from data/tracklists.md, data/results.tsv
and data/extra_links.tsv (the second-source links in missing_instrumental_links.txt).

The PowerShell script sorts downloaded instrumentals from "Music Albums\\Not Sorted"
into per-album folders. Rerun this after changing the data files.
"""
import json
import re
from pathlib import Path

from build import DATA, ROOT, load_results, load_tracklists

# Extra names an artist may appear under in a filename.
ARTIST_ALIASES = {
    "Ken Carson": ["Ken Car$on", "Ken Car on"],
    "Homixide Gang": ["HXG", "Homixide"],
    "Lil Uzi Vert": ["Uzi"],
    "Playboi Carti": ["Carti"],
    "Destroy Lonely": ["Lone"],
}

# Other names an album folder may already use. The first entry is also the folder
# name the script creates when the album name has characters Windows rejects.
ALBUM_ALIASES = {
    "</3³": ["Broken Hearts 3", "BH3", "3"],
    "MUSIC": ["I AM MUSIC"],
    "ADL": ["A Dangerous Lyfe"],
    "5TH AMNDMNT": ["5th Amendment"],
    "LOVE LASTS FOREVER": ["LLF"],
    "If Looks Could Kill": ["ILCK"],
    "Whole Lotta Red": ["WLR"],
    "Eternal Atake": ["EA"],
    "Eternal Atake 2": ["EA2"],
    "Luv Is Rage 2": ["LIR2"],
    "Playboi Carti": ["Self Titled", "Self-Titled"],
}

# Other spellings of a track name seen in downloaded file names, keyed by
# (artist|album, track).
TRACK_ALIASES = {
    ("Yeat|Up 2 Më", "Morning mudd"): ["Mornin Mudd", "Mornin Mud"],
    ("Yeat|Up 2 Më", "Ya Ya"): ["Yaya"],
    ("Yeat|2 Alivë", "Still Countin"): ["Still Counting"],
    ("Playboi Carti|MUSIC", "EVIL J0RDAN"): ["EVIL JORDAN"],
    ("Playboi Carti|Whole Lotta Red", "JumpOutTheHouse"): ["Jump Out The House"],
    ("Destroy Lonely|NO STYLIST", "NOSTYLIST"): ["NO STYLIST"],
}


def load_extra_links():
    """Second-source links from data/extra_links.tsv, keyed like load_results()."""
    extra = {}
    lines = (DATA / "extra_links.tsv").read_text(encoding="utf-8").splitlines()[1:]
    for line in lines:
        key, track, url, title = line.split("\t")
        extra.setdefault((key, track), []).append((url, title))
    return extra


def main():
    results = load_results()
    extra = load_extra_links()
    albums = []
    for a in load_tracklists():
        key = f"{a['artist']}|{a['album']}"
        tracks = []
        for t in a["tracks"]:
            r = results.get((key, t), {})
            links = [(r.get("url", ""), r.get("title", "")), (r.get("alt", ""), "")]
            links += extra.get((key, t), [])
            ids, titles = [], []
            for u, title in links:
                m = re.search(r"v=([\w-]{11})", u)
                if m:
                    ids.append(m.group(1))
                if title and not title.startswith("(no "):
                    titles.append(title)
            tracks.append({"name": t, "aliases": TRACK_ALIASES.get((key, t), []),
                           "ids": ids, "titles": titles})
        albums.append({
            "artist": a["artist"],
            "artistAliases": ARTIST_ALIASES.get(a["artist"], []),
            "album": a["album"],
            "albumAliases": ALBUM_ALIASES.get(a["album"], []),
            "year": a["year"],
            "tracks": tracks,
        })

    data = json.dumps(albums, ensure_ascii=False, indent=1)
    assert "\n'@" not in data
    template = (ROOT / "scripts" / "sort_not_sorted.template.ps1").read_text(encoding="utf-8")
    out = template.replace("__ALBUM_DATA__", data)
    # UTF-8 with BOM so Windows PowerShell 5.1 reads the accented names correctly.
    (ROOT / "scripts" / "sort_not_sorted.ps1").write_text(out, encoding="utf-8-sig", newline="\r\n")
    known = {(f"{a['artist']}|{a['album']}", t["name"]) for a in albums for t in a["tracks"]}
    assert not set(TRACK_ALIASES) - known, set(TRACK_ALIASES) - known
    print(f"wrote sort_not_sorted.ps1: {len(albums)} albums, "
          f"{sum(len(a['tracks']) for a in albums)} tracks")


if __name__ == "__main__":
    main()
