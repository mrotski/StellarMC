import os
import json
import subprocess
import time
import msvcrt

# 📄 Lue asetukset settings.txt:stä
java8_path = ""
java21_path = ""
lwjgl_321_path = ""
lwjgl_331_path = ""

base_dir = os.path.dirname(__file__)  # suhteellinen polku launcherin sijainnista

with open(os.path.join(base_dir, "settings.txt"), "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("java8="):
            java8_path = os.path.normpath(os.path.join(base_dir, line.strip().split("=", 1)[1]))
        elif line.startswith("java21="):
            java21_path = os.path.normpath(os.path.join(base_dir, line.strip().split("=", 1)[1]))
        elif line.startswith("lwjgl_321="):
            lwjgl_321_path = os.path.normpath(os.path.join(base_dir, line.strip().split("=", 1)[1]))
        elif line.startswith("lwjgl_331="):
            lwjgl_331_path = os.path.normpath(os.path.join(base_dir, line.strip().split("=", 1)[1]))

# 📁 Minecraft-kansiot
appdata = os.getenv("APPDATA")
game_dir = os.path.join(appdata, ".minecraft")
libraries_path = os.path.join(game_dir, "libraries")
assets_dir = os.path.join(game_dir, "assets")

# 🎮 Tuetut versiot
versions = ["1.16.5", "1.19.4", "1.20.6", "1.21.8"]
selected_index = 0

# 🌀 Animaatio
frames = ["[/         ]", "[//        ]", "[///       ]",
          "[////      ]", "[/////     ]", "[//////    ]",
          "[///////   ]", "[////////  ]", "[///////// ]", "[//////////]"]

for frame in frames:
    print("\r" + frame, end="", flush=True)
    time.sleep(0.5)
print("\n\n")

# 🧭 Versiovalinta
while True:
    os.system("cls" if os.name == "nt" else "clear")
    print("StellarMC 20251509 New Zealand")
    print("Choose version with arrow keys (↑/↓):\n")
    for i, v in enumerate(versions):
        prefix = "> " if i == selected_index else "  "
        print(f"{prefix}{v}")
    print("\nPress [SPACE] to continue")

    key = msvcrt.getch()
    if key == b'w' and selected_index > 0:
        selected_index -= 1
    elif key == b's' and selected_index < len(versions) - 1:
        selected_index += 1
    elif key == b'\xe0':
        arrow = msvcrt.getch()
        if arrow == b'H' and selected_index > 0:
            selected_index -= 1
        elif arrow == b'P' and selected_index < len(versions) - 1:
            selected_index += 1
    elif key == b' ':
        break

version = versions[selected_index]
version_dir = os.path.join(game_dir, "versions", version)
version_json_path = os.path.join(version_dir, f"{version}.json")

# 📄 Lue JSON
if not os.path.exists(version_json_path):
    print(f"JSON file not found: {version_json_path}")
    exit(1)

with open(version_json_path, "r", encoding="utf-8") as f:
    j = json.load(f)

# 🔗 Classpath
classpath = []
for lib in j["libraries"]:
    try:
        path = lib["downloads"]["artifact"]["path"]
        classpath.append(os.path.join(libraries_path, path))
    except:
        continue

jar_path = os.path.join(version_dir, f"{j['id']}.jar")
classpath.append(jar_path)

# LWJGL mukaan versioiden mukaan
if version == "1.16.5":
    for jar in ["lwjgl.jar", "lwjgl-glfw.jar", "lwjgl-opengl.jar", "lwjgl-openal.jar",
                "lwjgl-stb.jar", "lwjgl-tinyfd.jar", "lwjgl-jemalloc.jar"]:
        classpath.append(os.path.join(lwjgl_321_path, "jar", jar))

elif version in ["1.19.4", "1.20.6", "1.21.8"]:
    for jar in ["lwjgl.jar", "lwjgl-glfw.jar", "lwjgl-opengl.jar", "lwjgl-openal.jar",
                "lwjgl-stb.jar", "lwjgl-tinyfd.jar", "lwjgl-jemalloc.jar"]:
        classpath.append(os.path.join(lwjgl_331_path, jar))

# 🧑 Käyttäjänimi
print("\nEnter username: ", end="", flush=True)
username = input()

# 🧠 Java-komento
main_class = j["mainClass"]
asset_index = j["assetIndex"]["id"]
uuid = "00000000-0000-0000-0000-000000000000"
access_token = "stellar-access-token"

# Valitse Java ja natives
if version in ["1.19.4", "1.20.6", "1.21.8"]:
    java_final = java21_path
    natives_path = os.path.join(lwjgl_331_path, "win-nat")
elif version == "1.16.5":
    java_final = java8_path
    natives_path = os.path.join(lwjgl_321_path, "win-natives")

cmd = [
    java_final,
    "-Xmx2G", "-Xms1G",
    f"-Djava.library.path={natives_path}",
    "-cp", f'"{";".join(classpath)}"',
    main_class,
    "--username", username,
    "--version", version,
    "--gameDir", game_dir,
    "--assetsDir", assets_dir,
    "--assetIndex", asset_index,
    "--uuid", uuid,
    "--accessToken", access_token,
    "--userType", "mojang"
]

# 🚀 Käynnistä Minecraft
print("\nLaunching Minecraft...")
try:
    with open("error_log.txt", "w") as err:
        subprocess.Popen(cmd, stderr=err)
    print("Minecraft launched successfully!")
except Exception as e:
    print(f"Launch failed: {e}")