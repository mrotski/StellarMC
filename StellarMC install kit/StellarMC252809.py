import os
import json
import subprocess
import time
import msvcrt
import shutil

# 📁 Paths and settings
base_dir = os.path.dirname(__file__)
settings_path = os.path.join(base_dir, "settingsbeta.txt")
config_path = os.path.join(os.getenv("APPDATA"), ".stellar_launcher_config.json")
install_source = r"C:\StellarMC-main\StellarMC install kit\needed_files\data_minecraft"

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
appdata = os.getenv("APPDATA")
game_dir = os.path.join(appdata, "data_minecraft")
libraries_path = os.path.join(game_dir, "libraries")
assets_dir = os.path.join(game_dir, "assets")
versions_dir = os.path.join(game_dir, "versions")

# 🧱 First launch setup
if not os.path.exists(config_path):
    print("First launch. Copying Minecraft files...")
    try:
        if not os.path.exists(game_dir):
            shutil.copytree(install_source, game_dir)
            print("Files copied successfully.")
        else:
            print(".minecraft already exists. Skipping copy.")
        with open(config_path, "w") as f:
            json.dump({"initialized": True}, f)
    except Exception as e:
        print(f"Error during file copy: {e}")
        exit(1)
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
        print("\nUse the arrow keys to select the version. Press the [SPACE] key to continue.")

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
for jar in ["lwjgl.jar", "lwjgl-glfw.jar", "lwjgl-opengl.jar", "lwjgl-openal.jar",
            "lwjgl-stb.jar", "lwjgl-tinyfd.jar", "lwjgl-jemalloc.jar"]:
    classpath.append(os.path.join(lwjgl_path, jar))

# 🧑 Username input with memory
username_file = os.path.join(base_dir, "last_username.txt")
if os.path.exists(username_file):
    with open(username_file, "r") as f:
        last_username = f.read().strip()
    username = input(f"\nEnter username [{last_username}]: ") or last_username
else:
    username = input("\nEnter username: ")

with open(username_file, "w") as f:
    f.write(username)

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
        print("Minecraft launched succesfully!")
except Exception as e:
    print(f"FATAL ERROR during launch: {e}")
    with open("error_log.txt", "r") as err:
        print("\n--- Error Log ---")
        print(err.read())
    exit(1)