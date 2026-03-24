import json
import re
import shutil
from pathlib import Path

IMPORT_DIR = Path("import")
EXPORT_DIR = Path("export")

VALID_ARMOR_ITEMS = {
    "leather_helmet", "leather_chestplate", "leather_leggings", "leather_boots",
    "golden_helmet", "golden_chestplate", "golden_leggings", "golden_boots",
    "iron_helmet", "iron_chestplate", "iron_leggings", "iron_boots",
    "diamond_helmet", "diamond_chestplate", "diamond_leggings", "diamond_boots",
    "netherite_helmet", "netherite_chestplate", "netherite_leggings", "netherite_boots",
    "chainmail_helmet", "chainmail_chestplate", "chainmail_leggings", "chainmail_boots",
    "turtle_helmet"
}

MATERIALS = ["leather", "golden", "iron", "diamond", "netherite", "chainmail", "copper"]


def parse_properties(file_path):
    props = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            props[key.strip()] = value.strip()
    return props


def convert_unicode(text):
    try:
        return text.encode('utf-8').decode('unicode_escape')
    except:
        return text


def get_names_from_display(name_str):
    if not name_str:
        return []
    
    name_str = convert_unicode(name_str)
    
    if "iregex:(" in name_str:
        match = re.search(r'iregex:\(([^)]+)\)', name_str)
        if match:
            inner = match.group(1)
            if "|" in inner:
                return [n.strip() for n in inner.split("|")]
            return [inner.strip()]
    
    if "|" in name_str:
        return [n.strip() for n in name_str.split("|")]
    return [name_str]


LAYER1_ITEMS = {"helmet", "chestplate", "boots"}
LAYER2_ITEMS = {"leggings", "pants"}


def process_file(file_path, props, converted_layer1, converted_layer2, textures_set):
    armor_type = props.get("type", "")
    match_items = props.get("matchItems") or props.get("Items") or props.get("Item", "")
    
    if armor_type == "armor":
        pass
    elif armor_type in ("item", "elytra"):
        if not match_items:
            return
        items_list = match_items.split()
        has_valid = any(item in VALID_ARMOR_ITEMS for item in items_list)
        if not has_valid:
            return
    else:
        return
    
    names = get_names_from_display(props.get("nbt.display.Name", ""))
    if not names:
        return
    
    items_list = match_items.split()
    
    for material in MATERIALS:
        layer1_key = f"texture.{material}_layer_1"
        layer2_key = f"texture.{material}_layer_2"
        
        has_layer1 = any(item for item in items_list if any(t in item for t in LAYER1_ITEMS))
        has_layer2 = any(item for item in items_list if any(t in item for t in LAYER2_ITEMS))
        
        texture_layer1 = props.get(layer1_key)
        texture_layer2 = props.get(layer2_key)
        
        if texture_layer1 and has_layer1:
            target = converted_layer1
            target_key = material
            
            if target_key not in target:
                target[target_key] = []
            
            case = {
                "when": names,
                "child": {
                    "type": "rpt:apply",
                    "value": f"textures/{texture_layer1}.png"
                }
            }
            
            already_exists = any(
                c.get("child", {}).get("value") == case["child"]["value"] and
                set(c.get("when", [])) == set(case["when"])
                for c in target[target_key]
            )
            
            if not already_exists:
                target[target_key].append(case)
            
            folder = Path(file_path).parent
            for png_file in folder.glob(f"{texture_layer1}.png"):
                textures_set.add((png_file, texture_layer1))
            for png_file in folder.glob(f"{texture_layer1}_icon.png"):
                textures_set.add((png_file, f"{texture_layer1}_icon"))
        
        if texture_layer2 and has_layer2:
            target = converted_layer2
            target_key = material
            
            if target_key not in target:
                target[target_key] = []
            
            case = {
                "when": names,
                "child": {
                    "type": "rpt:apply",
                    "value": f"textures/{texture_layer2}.png"
                }
            }
            
            already_exists = any(
                c.get("child", {}).get("value") == case["child"]["value"] and
                set(c.get("when", [])) == set(case["when"])
                for c in target[target_key]
            )
            
            if not already_exists:
                target[target_key].append(case)
            
            folder = Path(file_path).parent
            for png_file in folder.glob(f"{texture_layer2}.png"):
                textures_set.add((png_file, texture_layer2))
            for png_file in folder.glob(f"{texture_layer2}_icon.png"):
                textures_set.add((png_file, f"{texture_layer2}_icon"))


def main():
    import os
    import shutil
    if os.path.exists("export"):
        pass
    
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    rpt_dir_layer1 = EXPORT_DIR / "assets" / "minecraft" / "rpt" / "swappers" / "textures" / "entity" / "equipment" / "humanoid"
    rpt_dir_layer2 = EXPORT_DIR / "assets" / "minecraft" / "rpt" / "swappers" / "textures" / "entity" / "equipment" / "humanoid_leggings"
    rpt_dir_layer1.mkdir(parents=True, exist_ok=True)
    rpt_dir_layer2.mkdir(parents=True, exist_ok=True)
    
    textures_dir = EXPORT_DIR / "assets" / "minecraft" / "textures"
    textures_dir.mkdir(parents=True, exist_ok=True)
    
    all_files = list(IMPORT_DIR.rglob("*.properties"))
    
    converted_layer1 = {}
    converted_layer2 = {}
    textures_set = set()
    
    for file_path in all_files:
        if "_icon" in Path(file_path).stem:
            continue
        
        props = parse_properties(file_path)
        process_file(file_path, props, converted_layer1, converted_layer2, textures_set)
    
    for material, cases in converted_layer1.items():
        output = {
            "type": "rpt:component",
            "component": "custom_name",
            "cases": cases
        }
        
        output_file = rpt_dir_layer1 / f"{material}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)
        print(f"Created: {output_file}")
    
    for material, cases in converted_layer2.items():
        output = {
            "type": "rpt:component",
            "component": "custom_name",
            "cases": cases
        }
        
        output_file = rpt_dir_layer2 / f"{material}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)
        print(f"Created: {output_file}")
    
    for src_path, texture_name in textures_set:
        dest_path = textures_dir / f"{texture_name}.png"
        shutil.copy2(src_path, dest_path)
        print(f"Copied texture: {dest_path}")
    
    print(f"\nTotal JSON files: {len(converted_layer1) + len(converted_layer2)}")
    print(f"Total textures copied: {len(textures_set)}")


if __name__ == "__main__":
    main()