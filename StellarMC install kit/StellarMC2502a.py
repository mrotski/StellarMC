import os
import json
import subprocess
import time
import msvcrt
import urllib.request

# 🔧 Polut ja asetukset
base_dir = os.path.dirname(__file__)
settings_path = os.path.join(base_dir, "settings.txt")
config_path = os.path.join(base_dir, ".stellar_launcher_config.json")

# 🔧 Kovakoodatut polut
java_path = "java.exe"  # Oletetaan että PATHissa tai settings.txt:ssä
lwjgl_path = r"C:\StellarMC-main\StellarMC install kit\Natives\lwjgl-3.3.1"
game_dir = r"C:\StellarMC-main\StellarMC install kit\needed_files\data_minecraft"
libraries_path = os.path.join(game_dir, "libraries")
assets_dir = os.path.join(game_dir, "assets")
versions_dir = os.path.join(game_dir, "versions")

# 🧱 Ensimmäinen käynnistys
if not os.path.exists(config_path):
    print("Ensimmäinen käynnistys. Tarkistetaan tiedostot...")
    if not os.path.exists(game_dir):
        print("Game directory puuttuu.")
        exit(1)
    os.makedirs(libraries_path, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump({"initialized": True}, f)

# 🎮 Versiot
versions = ["1.19.4", "1.20.4"]

def select_version(versions):
    index = 0
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("StellarMC Launcher\n")
        for i, v in enumerate(versions):
            print(f"{'-> ' if i == index else '   '}{v}")
        print("\nValitse versio nuolinäppäimillä. [SPACE] jatkaa.")
        key = msvcrt.getch()
        if key == b'\xe0':
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

if not os.path.exists(version_json_path):
    print(f"Version JSON puuttuu: {version_json_path}")
    exit(1)

with open(version_json_path, "r", encoding="utf-8") as f:
    j = json.load(f)

# 📦 Lataa puuttuvat libraries
def download_missing_libraries(libraries, libraries_path):
    print("\nTarkistetaan puuttuvat kirjastot...")
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
                    print(f"Ladataan: {rel_path}")
                    urllib.request.urlretrieve(url, dest_path)
                except Exception as e:
                    print(f"Virhe ladattaessa {rel_path}: {e}")
            else:
                print(f"✅ Kirjasto löytyy: {rel_path}")

download_missing_libraries(j["libraries"], libraries_path)

# 📦 Lataa puuttuvat assets
asset_index_id = j["assetIndex"]["id"]
asset_index_path = os.path.join(assets_dir, "indexes", f"{asset_index_id}.json")
objects_dir = os.path.join(assets_dir, "objects")

def download_missing_assets(asset_index, objects_dir):
    print("\nTarkistetaan puuttuvat assetit...")
    for key, obj in asset_index["objects"].items():
        hash_val = obj["hash"]
        subdir = hash_val[:2]
        file_path = os.path.join(objects_dir, subdir, hash_val)
        if not os.path.exists(file_path):
            url = f"https://resources.download.minecraft.net/{subdir}/{hash_val}"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            try:
                urllib.request.urlretrieve(url, file_path)
                print(f"✅ Asset ladattu: {key}")
            except Exception as e:
                print(f"❌ Virhe assetissa {key}: {e}")

if os.path.exists(asset_index_path):
    with open(asset_index_path, "r", encoding="utf-8") as f:
        asset_index = json.load(f)
    download_missing_assets(asset_index, objects_dir)
else:
    print(f"Asset index puuttuu: {asset_index_path}")

# 🔗 Classpath
classpath = [
    os.path.join(libraries_path, lib["downloads"]["artifact"]["path"])
    for lib in j["libraries"]
    if "downloads" in lib and "artifact" in lib["downloads"]
]
jar_path = os.path.join(version_dir, f"{j['id']}.jar")
classpath.append(jar_path)

# ➕ LWJGL
natives_path = os.path.join(lwjgl_path, "win-nat")
for jar in ["lwjgl.jar", "lwjgl-glfw.jar", "lwjgl-opengl.jar",
            "lwjgl-openal.jar", "lwjgl-stb.jar", "lwjgl-tinyfd.jar", "lwjgl-jemalloc.jar"]:
    classpath.append(os.path.join(lwjgl_path, jar))

# 👤 Käyttäjänimi
username_file = os.path.join(base_dir, "last_username.txt")
if os.path.exists(username_file):
    with open(username_file, "r") as f:
        last_username = f.read().strip()
    username = input(f"\nKäyttäjänimi [{last_username}]: ") or last_username
else:
    username = input("\nSyötä käyttäjänimi: ")

with open(username_file, "w") as f:
    f.write(username)

# 🚀 Käynnistys
print("\nKäynnistetään Minecraft...")
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
        print("Odotetaan vastausta...")
    time.sleep(10)
    if process.poll() is not None:
        print("Minecraft ei käynnistynyt.")
        with open("error_log.txt", "r") as err:
            print("\n--- Virheloki ---")
            print(err.read())
    else:
        print("✅ Minecraft käynnistyi!")
except Exception as e:
    print(f"FATAL ERROR: {e}")
    with open("error_log.txt", "r") as err:
        print("\n--- Virheloki ---")
        print(err.read())
    exit(1)