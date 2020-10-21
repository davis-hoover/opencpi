#!/usr/bin/env python3

import argparse
import re
from pathlib import Path
from xml.etree import ElementTree

XMLNS = {
    "text": "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Removes 'tracked changes' from libreoffice files.")
    parser.add_argument(
        "-o", "--outfile",
        help="Write changes to OUTFILE instead of overwriting input file. "
             "If OUTFILE exists it will be overwritten."
    )
    parser.add_argument(
        "--show-changes",
        help="Show changes and whether they are insertions or deletions",
        action="store_true"
    )
    parser.add_argument(
        "infile",
        help="Input file to remove tracked changes from"
    )
    return parser.parse_args()


def get_change(raw_text: bytes) -> bytes:
    s = b""
    read_ndx = 0
    while read_ndx < len(raw_text):
        # Remove leading "\n  " stuff
        if raw_text[read_ndx] == ord(b"\n"):
            read_ndx += 1
            while raw_text[read_ndx] == ord(b"\n") or raw_text[read_ndx] == ord(b" "):
                read_ndx += 1

        # Find start of next tag
        i = raw_text.find(b"<", read_ndx)
        if i == -1:
            # No more tags
            s += raw_text[read_ndx:]
            break

        # Copy stuff before start of next tag
        s += raw_text[read_ndx:i]
        read_ndx = i

        # Find end of tag
        i = raw_text.find(b">", read_ndx)
        if i == -1:
            #  Hmm, no end tag?
            continue
        # Skip over tag
        read_ndx = i + 1

    return s


def remove_empty_lines(raw_data: bytes) -> bytes:
    lines = raw_data.split(b"\n")
    rv = []
    for line in lines:
        match = re.match(rb"\s+$", line)
        if match is None:
            rv.append(line)
    return b"\n".join(rv)


def remove_tracked_changes_meta(raw_data: bytes) -> bytes:
    # Stuff to delete is between <text:tracked-changes .*</text:tracked-changes>
    start_tag = b"<text:tracked-changes "
    end_tag = b"</text:tracked-changes>"
    start_ndx = raw_data.index(start_tag)
    end_ndx = raw_data.index(end_tag, start_ndx)
    rv = raw_data[:start_ndx]
    rv += raw_data[end_ndx + len(end_tag):]
    return rv


def save_file(fname: Path, data: bytes):
    fname.parent.mkdir(parents=True, exist_ok=True)
    with open(str(fname), "wb") as fd:
        fd.write(data)


def main():
    args = parse_args()
    infile = Path(args.infile)
    if not infile.exists():
        raise RuntimeError(f"Input file does not exist: '{infile}'")
    outfile = infile
    if args.outfile is not None:
        outfile = Path(args.outfile)

    # Load raw file into memory
    # "b" is used as there is a weird decoding error when building docs in CI pipeline
    with open(str(infile), "rb") as fd:
        raw_file_lines = fd.readlines()
    raw_file = b"".join(raw_file_lines)
    outfile_data = b""

    # Use ElementTree to find tags of interest. We do not use ElementTree to
    # change the underlying xml file. This is due to the attributes being
    # stored in a dictionary which is not ordered. This results in the
    # attributes of all tags changing order causing unnecessary differences.
    # Raw file manipulation is used instead to reduce these unnecessary
    # differences. The sole purpose is to have an easy to understand `git diff`
    # of the changed files.
    tree = ElementTree.fromstring(raw_file)
    change_starts = tree.findall(f".//{XMLNS['text']}change-start")
    changed_regions = tree.findall(f".//{XMLNS['text']}changed-region")

    if len(change_starts) == 0 or len(changed_regions) == 0:
        save_file(outfile, raw_file)
        return 0

    # Main loop that loops over all '<text:change-start ...>' tags, figures out
    # the type of change (insertion or deletion), and removes appropriate text.
    read_ndx = 0
    for change_start in change_starts:
        # Find changed region node so we can determine if this was an insertion or a deletion
        change_id = change_start.attrib[XMLNS["text"] + "change-id"]
        change_type = None
        for region in changed_regions:
            if change_id != region.attrib[XMLNS["text"] + "id"]:
                continue
            child = region[0]
            change_type = child.tag.replace(XMLNS["text"], "")
            break
        if change_type is None:
            raise RuntimeError(f"Could not determine type of change for change id '{change_id}'")

        # Build change-start and change-end tags
        change_start_tag = f'<text:change-start text:change-id="{change_id}"/>'.encode()
        change_end_tag = f'<text:change-end text:change-id="{change_id}"/>'.encode()

        # Find index in raw file for change-start and change-end tags
        start_ndx = raw_file.index(change_start_tag)
        end_ndx = raw_file.index(change_end_tag, start_ndx)

        # Copy data we want, up to start_ndx
        outfile_data += raw_file[read_ndx:start_ndx]
        read_ndx = start_ndx + len(change_start_tag)

        if args.show_changes:
            change = get_change(raw_file[start_ndx + len(change_start_tag):end_ndx])
            print(f"{change_type}: {change}")

        # Remove change from file
        if change_type == "insertion":
            # Only need to delete change-start and change-end tags
            # So we need to copy "the stuff in-between" to the out file
            outfile_data += raw_file[read_ndx:end_ndx]
            read_ndx = end_ndx + len(change_end_tag)
        elif change_type == "deletion":
            # Need to delete everything in between change-start and change-end tags
            # Advance read_ndx to the end of the change_end_tag
            read_ndx = end_ndx + len(change_end_tag)
        else:
            raise RuntimeError(f"Error: unknown change type: '{change_type}'")

    # Copy remaining data to new file
    outfile_data += raw_file[read_ndx:]

    # Need to remove meta data about tracked changes now
    outfile_data = remove_tracked_changes_meta(outfile_data)

    # Remove all empty lines that have at least one space
    outfile_data = remove_empty_lines(outfile_data)

    # Finally, write data to new file
    save_file(outfile, outfile_data)

    return 0


if __name__ == "__main__":
    exit(main())
