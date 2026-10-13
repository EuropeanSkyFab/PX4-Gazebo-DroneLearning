import subprocess

def get_box_pose():
    result = subprocess.run(
        ["gz", "topic", "-e", "-t", "/world/default/pose/info", "-n", "1"],
        capture_output=True, text=True, timeout=5
    )
    output = result.stdout
    lines = output.split("\n")
    for i, line in enumerate(lines):
        if 'name: "box"' in line:
            for j in range(i, min(i+15, len(lines))):
                if "position" in lines[j]:
                    x = float(lines[j+1].split(":")[1])
                    y = float(lines[j+2].split(":")[1])
                    z = float(lines[j+3].split(":")[1])
                    return x, y, z
    return None

if __name__ == "__main__":
    print("box 位置:", get_box_pose())