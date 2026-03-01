#!/usr/bin/env python3

"""
usage:
 $ git switch master
 $ ./gun-list.py
 $ git switch new-branch
 $ ./gun-list.py -N
then check !gun_info.md and !gun_table.md files
make changes to new-branch
then update lists:
 $ ./gun-list.py -N
"""

import argparse
import json
from pathlib import Path


table_dict = {}

json_gun = []
json_mag = {}
json_ammo = {}
json_ammo_type = {}


def make_table(path_table_old, path_table_new):

    with open(path_table_old, encoding="utf-8") as fp:
        table_old = json.load(fp)
    with open(path_table_new, encoding="utf-8") as fp:
        table_new = json.load(fp)

    table = ""
    i = 1
    for ko, vo in table_old.items():
        vn = table_new.get(ko)
        if vo != vn:
            if vo["name"] != vn["name"]:
                table += f"{i}. 🟪{vo['name']} --> {vn['name']}\n"
            else:
                table += f"{i}. 🟪{vo['name']}\n"
            vo_var = vo.get("variants")
            vn_var = vn.get("variants")
            if vo_var != vn_var:
                table += f"    * ◻️{vo_var} --> {vn_var}\n"
            i += 1

    with open("!gun_table.md", "w", encoding="utf-8") as fp:
        fp.write(table)


def get_name(e, suffix=False, plural=True):
    s = ""
    n = e["name"]
    if type(n) is str:
        n = { "str": n }
    if not plural:
        s = n.get("str_sp") or n.get("str")
    elif name := n.get("str_sp"):
        if plural:
            s = f"{name} | STR-SP"
        else:
            s = f"{name}"
    elif name := n.get("str_pl"):
        s = f"{n['str']} // {name} | STR-PL"
    else:
        name = n["str"]
        s = f"{name} // {name}s"
    if suffix:
        s = f"{suffix}{s}"
    return s


def process_gun(data):
    
    for entry in data:
        table_entry = {}

        if entry.get("abstract") or \
           not entry.get("subtypes"):
            continue

        if "GUN" in entry["subtypes"]:
            json_gun.append(get_name(entry, "* 🟪"))
            table_entry["name"] = get_name(entry, plural=False)

        if entry.get("variants"):
            table_entry["variants"] = []
            for v in entry["variants"]:
                json_gun.append(get_name(v, "   * ◻️"))
                table_entry["variants"].append(get_name(v, plural=False))

        if entry.get("pocket_data"):
            for pocket_data in entry["pocket_data"]:
                pocket = pocket_data.get("item_restriction") or []
                pocket += pocket_data.get("allowed_speedloaders") or []
                if pocket:
                    for i in pocket:
                        if k := json_mag.get(i):
                            json_gun.append(f"       * 🔹{k}")

                if ammo := pocket_data.get("ammo_restriction"):
                    for i in ammo.keys():
                        k = json_ammo.get(i)
                        if not k:
                            if k_type := json_ammo_type.get(i):
                                k = json_ammo.get(k_type["default"]) or k_type["name"]
                        if k:
                            json_gun.append(f"       * 🔸{k}")

        if table_entry:
            table_dict[entry["id"]] = table_entry


def process_mag(data):
    for entry in data:
        if entry.get("abstract"):
            continue

        if "MAGAZINE" in entry["subtypes"] or "magazine" in entry["subtypes"]:
            s = get_name(entry, plural=False)

            if entry.get("variants"):
                for v in entry["variants"]:
                    s = f"{s} || {get_name(v, plural=False)}"

            json_mag[entry["id"]] = s
    

def process_ammo(data):
    for entry in data:
        if entry.get("abstract"):
            continue

        if "AMMO" in entry["subtypes"] or "ammo" in entry["subtypes"]:
            d = get_name(entry, plural=False)

            if entry.get("variants"):
                for v in entry["variants"]:
                    d = f"{d} || {get_name(v, plural=False)}"
            
            ident = entry.get("id") or entry.get("abstract")
            json_ammo[ident] = d


def process_ammo_type(data):
    for entry in data:
        if entry["type"].lower() == "ammunition_type":
            json_ammo_type[entry["id"]] = entry


def main(new):

    # READING

    for f in sorted(Path("data/json/items/ammo/").rglob("*.json")):
        with open(f, encoding="utf-8") as fp:
            process_ammo(json.load(fp))

    with open("data/json/items/ammo_types.json", encoding="utf-8") as fp:
        process_ammo_type(json.load(fp))

    for f in sorted(Path("data/json/items/magazine/").rglob("*.json")):
        with open(f, encoding="utf-8") as fp:
            process_mag(json.load(fp))

    for f in sorted(Path("data/json/items/gun/").rglob("*.json")):
        json_gun.append(f"#### [{f}]({f})")
        with open(f, encoding="utf-8") as fp:
            process_gun(json.load(fp))

    # WRITING

    table_old = Path("!gun_table_old.json")
    table_new = Path("!gun_table_new.json")
    if table_dict:
        table_filename = table_new if new else table_old
        with open(table_filename, "w", encoding="utf-8") as fp:
            json.dump(table_dict, fp, indent="  ")

    if table_old.is_file() and table_new.is_file():
        make_table(table_old, table_new)

    s_out = ""

    for s in json_gun:
        s_out += f"{s}\n"

    s_out += "\n\n# ALL MAGAZINES\n"
    for s in sorted(json_mag.values()):
        s_out += f"* {s}\n"

    s_out += "\n\n# ALL AMMO\n"
    for s in sorted(json_ammo.values()):
        s_out += f"* {s}\n"

    s_out += "\n\n# ALL AMMO TYPES\n"
    for s in sorted(json_ammo_type.values(), key=lambda k: k["name"]):
        s_out += f"* {s['name']}"
        if s1 := json_ammo.get(s['default']):
            s_out += f": {s1}"
        s_out += "\n"

    with open("!gun_info.md", "w", encoding="utf-8") as fp:
        fp.write(s_out)


def _parse_args():
    argparser = argparse.ArgumentParser(
        description="Создаёт список оружия, а также таблицу изменений."
    )
    argparser.add_argument("-N", "--new",
                           action="store_true",
                           help="is the git branch new?")
    return argparser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    main(args.new)
