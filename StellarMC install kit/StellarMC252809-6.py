import os
import json
import subprocess
import time
import msvcrt
import urllib.request

# Paths and settings
base_dir = os.path.dirname(__file__)
config_path = os.path.join(base_dir, ".stellar_launcher_config.json")

# Hardcoded paths
java_path = "java.exe"
lwjgl_path = r"C:\StellarMC-main\StellarMC install kit\Natives\lwjgl-3.3.1"
game_dir = r"C:\StellarMC-main\StellarMC install kit\needed_files\data_minecraft"
libraries_path = os.path.join(game_dir, "libraries")
assets_dir = os.path.join(game_dir, "assets")
versions_dir = os.path.join(game_dir, "versions")

# First launch setup
if not os.path.exists(config_path):
    print("First launch. Verifying game directory...")
    if not os.path.exists(game_dir):
        print("Game directory not found.")
        exit(1)
    os.makedirs(libraries_path, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump({"initialized": True}, f)

# Supported versions
versions = ["1.19.4", "1.20.4", "1.21.8"]

def select_version(versions):
    index = 0
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("StellarMC252809-6\n")
        for i, v in enumerate(versions):
            print(f"{'-> ' if i == index else '   '}{v}")
        print("\nUse arrow keys to select version. Press [SPACE] to continue.")
        key = msvcrt.getch()
        if key == b'\xe0':
            arrow = msvcrt.getch()
            if arrow == b'H' and index > 0:
                index -= 1
            elif arrow == b'P' and index < len(versions) - 1:
                index += 1
        elif key == b' ':
            return versions[index]

def fetch_version_manifest():
    url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    try:
        with urllib.request.urlopen(url) as response:
            return json.load(response)
    except Exception as e:
        print(f"Error fetching version manifest: {e}")
        return None

def download_version_files(version_id, versions_dir):
    manifest = fetch_version_manifest()
    if not manifest:
        return False

    version_info = next((v for v in manifest["versions"] if v["id"] == version_id), None)
    if not version_info:
        print(f"Version {version_id} not found in manifest.")
        return False

    try:
        with urllib.request.urlopen(version_info["url"]) as response:
            version_json = json.load(response)
    except Exception as e:
        print(f"Error downloading version JSON: {e}")
        return False

    version_path = os.path.join(versions_dir, version_id)
    os.makedirs(version_path, exist_ok=True)

    json_path = os.path.join(version_path, f"{version_id}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(version_json, f, indent=2)

    jar_info = version_json.get("downloads", {}).get("client", {})
    jar_url = jar_info.get("url")
    jar_path = os.path.join(version_path, f"{version_id}.jar")

    if jar_url:
        try:
            print(f"Downloading JAR: {version_id}")
            urllib.request.urlretrieve(jar_url, jar_path)
        except Exception as e:
            print(f"Error downloading JAR: {e}")
            return False

    print(f"Version {version_id} downloaded.")
    return True

version = select_version(versions)
version_dir = os.path.join(versions_dir, version)
version_json_path = os.path.join(version_dir, f"{version}.json")

if not os.path.exists(version_json_path):
    print(f"Version {version} not found locally. Downloading from Mojang...")
    success = download_version_files(version, versions_dir)
    if not success:
        exit(1)

with open(version_json_path, "r", encoding="utf-8") as f:
    j = json.load(f)

def download_missing_libraries(libraries, libraries_path):
    print("\nChecking and downloading missing libraries...")
    base_url = "https://libraries.minecraft.net"
    for lib in libraries:
        if "downloads" in lib and "artifact" in lib["downloads"]:
            artifact = lib["downloads"]["artifact"]
            rel_path = artifact["path"]
            url = f"{base_url}/{rel_path}"
            dest_path = os.path.join(libraries_path, rel_path)
            if not os.path.exists(dest_path):
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                try:
                    print(f"Downloading: {rel_path}")
                    urllib.request.urlretrieve(url, dest_path)
                except Exception as e:
                    print(f"Error downloading {rel_path}: {e}")
            else:
                print(f"Already exists: {rel_path}")

download_missing_libraries(j["libraries"], libraries_path)

asset_index_id = j["assetIndex"]["id"]
asset_index_path = os.path.join(assets_dir, "indexes", f"{asset_index_id}.json")
objects_dir = os.path.join(assets_dir, "objects")

def download_missing_assets(asset_index, objects_dir):
    print("\nChecking and downloading missing assets...")
    for key, obj in asset_index["objects"].items():
        hash_val = obj["hash"]
        subdir = hash_val[:2]
        file_path = os.path.join(objects_dir, subdir, hash_val)
        if not os.path.exists(file_path):
            url = f"https://resources.download.minecraft.net/{subdir}/{hash_val}"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            try:
                urllib.request.urlretrieve(url, file_path)
                print(f"Downloaded: {key}")
            except Exception as e:
                print(f"Failed to download {key}: {e}")

if os.path.exists(asset_index_path):
    with open(asset_index_path, "r", encoding="utf-8") as f:
        asset_index = json.load(f)
    download_missing_assets(asset_index, objects_dir)
else:
    print(f"Asset index not found: {asset_index_path}")

# Build classpath
classpath = [
    os.path.join(libraries_path, lib["downloads"]["artifact"]["path"])
    for lib in j["libraries"]
    if "downloads" in lib and "artifact" in lib["downloads"]
]
jar_path = os.path.join(version_dir, f"{j['id']}.jar")
classpath.append(jar_path)

# Add LWJGL jars
natives_path = os.path.join(lwjgl_path, "win-nat")
for jar in ["lwjgl.jar", "lwjgl-glfw.jar", "lwjgl-opengl.jar",
            "lwjgl-openal.jar", "lwjgl-stb.jar", "lwjgl-tinyfd.jar", "lwjgl-jemalloc.jar"]:
    classpath.append(os.path.join(lwjgl_path, jar))

# Username input
username_file = os.path.join(base_dir, "last_username.txt")
if os.path.exists(username_file):
    with open(username_file, "r") as f:
        last_username = f.read().strip()
    username = input(f"\nEnter username [{last_username}]: ") or last_username
else:
    username = input("\nEnter username: ")

with open(username_file, "w") as f:
    f.write(username)

# Launch Minecraft
print("\nLaunching Minecraft...")
try:
    with open("error_log.txt", "w") as err:
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
    time.sleep(10)
    if process.poll() is not None:
        print("Minecraft failed to launch.")
        with open("error_log.txt", "r") as err:
            print("\n--- Error Log ---")
            print(err.read())
    else:
        print("Minecraft launched successfully!")
except Exception as e:
    print(f"FATAL ERROR: {e}")
    with open("error_log.txt", "r") as err:
        print("\n--- Error Log ---")
        print(err.read())
    exit(1)