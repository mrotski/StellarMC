import os
import json
import subprocess
import time
import msvcrt
import shutil
import urllib.request

# 📁 Paths and settings
base_dir = os.path.dirname(__file__)
settings_path = os.path.join(base_dir, "settingsbeta.txt")
config_path = os.path.join(base_dir, ".stellar_launcher_config.json")
game_dir = r"C:\StellarMC-main\StellarMC install kit\needed_files\data_minecraft"

# 🔧 Load settings
def load_settings(path):
    settings = {}
    if not os.path.exists(path):
        print(f"Settings file not found: {path}")
        exit(1)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                settings[key] = os.path.normpath(os.path.join(base_dir, value))
    return settings

settings = load_settings(settings_path)
java_path = settings.get("java21", "")
lwjgl_path = settings.get("lwjgl_331", "")

# 📁 Minecraft folders
libraries_path = os.path.join(game_dir, "libraries")
assets_dir = os.path.join(game_dir, "assets")
versions_dir = os.path.join(game_dir, "versions")

# 🧱 First launch setup
if not os.path.exists(config_path):
    print("First launch. Verifying Minecraft files...")
    if not os.path.exists(game_dir):
        print("Game directory not found. Please check the path.")
        exit(1)
    with open(config_path, "w") as f:
        json.dump({"initialized": True}, f)
else:
    print("Minecraft files are in place. Continuing...")

# 🎮 Supported versions
versions = ["1.19.4", "1.20.2"]

# 🧭 Version selector
def select_version(versions):
    index = 0
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("StellarMC252809 \n")
        for i, v in enumerate(versions):
            print(f"{'-> ' if i == index else '   '}{v}")
        print("\nUse arrow keys to select version. Press [SPACE] to continue.")

        key = msvcrt.getch()
        if key == b'w' and index > 0:
            index -= 1
        elif key == b's' and index < len(versions) - 1:
            index += 1
        elif key == b'\xe0':
            arrow = msvcrt.getch()
            if arrow == b'H' and index > 0:
                index -= 1
            elif arrow == b'P' and index < len(versions) - 1:
                index += 1
        elif key == b' ':
            return versions[index]

version = select_version(versions)
version_dir = os.path.join(versions_dir, version)
version_json_path = os.path.join(version_dir, f"{version}.json")

# 📄 Load version JSON
if not os.path.exists(version_json_path):
    print(f"Version JSON not found: {version_json_path}")
    exit(1)

with open(version_json_path, "r", encoding="utf-8") as f:
    j = json.load(f)

# 🧑 Username input
username_file = os.path.join(base_dir, "last_username.txt")
if os.path.exists(username_file):
    with open(username_file, "r") as f:
        last_username = f.read().strip()
    username = input(f"\nEnter username [{last_username}]: ") or last_username
else:
    username = input("\nEnter username: ")

with open(username_file, "w") as f:
    f.write(username)

# 📄 Load asset index and download missing objects
asset_index_id = j["assetIndex"]["id"]
asset_index_path = os.path.join(assets_dir, "indexes", f"{asset_index_id}.json")
objects_dir = os.path.join(game_dir, "assets", "objects")

def download_missing_assets(asset_index, objects_dir):
    print("\nChecking and downloading missing assets...")

    total = len(asset_index["objects"])
    downloaded = 0

    for key, obj in asset_index["objects"].items():
        hash_val = obj["hash"]
        subdir = hash_val[:2]
        file_path = os.path.join(objects_dir, subdir, hash_val)

        if not os.path.exists(file_path):
            url = f"https://resources.download.minecraft.net/{subdir}/{hash_val}"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            try:
                urllib.request.urlretrieve(url, file_path)
            except Exception as e:
                print(f"\nFailed to download {key}: {e}")

        downloaded += 1
        percent = int((downloaded / total) * 100)
        bars = int(percent / 10)
        progress_bar = "[" + "/" * bars + "." * (10 - bars) + f"] {percent}%"
        print(f"\rDownloading assets: {progress_bar}", end="", flush=True)

    print("\nAsset download complete!")

if os.path.exists(asset_index_path):
    with open(asset_index_path, "r", encoding="utf-8") as f:
        asset_index = json.load(f)
    download_missing_assets(asset_index, objects_dir)
else:
    print(f"Asset index not found: {asset_index_path}")

# 🔗 Build classpath
classpath = [
    os.path.join(libraries_path, lib["downloads"]["artifact"]["path"])
    for lib in j["libraries"]
    if "downloads" in lib and "artifact" in lib["downloads"]
]

jar_path = os.path.join(version_dir, f"{j['id']}.jar")
classpath.append(jar_path)

# ➕ Add LWJGL jars
natives_path = os.path.join(lwjgl_path, "win-nat")
for jar in ["lwjgl.jar", "lwjgl-glfw.jar", "lwjgl-opengl.jar",
            "lwjgl-openal.jar", "lwjgl-stb.jar", "lwjgl-tinyfd.jar", "lwjgl-jemalloc.jar"]:
    classpath.append(os.path.join(lwjgl_path, jar))

# 🐞 Checks
if not os.path.exists(java_path):
    print(f"Java path not found: {java_path}")
    exit(1)

if not os.path.exists(natives_path):
    print(f"Natives folder not found: {natives_path}")
    exit(1)
elif not any(fname.endswith(".dll") for fname in os.listdir(natives_path)):
    print(f"Natives folder missing DLL files: {natives_path}")

# 🚀 Launch Minecraft
print("\nLaunching Minecraft...")
try:
    with open("error_log.txt", "w") as err:
        print("Starting Java process...")
        process = subprocess.Popen([
            java_path,
            "-Xmx2G", "-Xms1G",
            f"-Djava.library.path={natives_path}",
            "-cp", ";".join(classpath),
            j["mainClass"],
            "--username", username,
            "--version", version,
            "--gameDir", game_dir,
            "--assetsDir", assets_dir,
            "--assetIndex", j["assetIndex"]["id"],
            "--uuid", "00000000-0000-0000-0000-000000000000",
            "--accessToken", "stellar-access-token",
            "--userType", "mojang"
        ], stdout=err, stderr=err)
        print("Waiting for Minecraft to respond...")

    time.sleep(100)
    if process.poll() is not None:
        print("Minecraft failed to launch.")
        with open("error_log.txt", "r") as err:
            print("\n--- Error Log ---")
            print(err.read())
    else:
        print("Minecraft launched successfully!")
except Exception as e:
    print(f"FATAL ERROR during launch: {e}")
    with open("error_log.txt", "r") as err:
        print("\n--- Error Log ---")
        print(err.read())
    exit(1)