import psutil
import platform
import subprocess
import shutil


def get_cpu_name():
    with open("/proc/cpuinfo") as f:
        for line in f:
            if "model name" in line:
                return line.split(":")[1].strip()
    return "Unknown"


def get_cpu_usage():
    return psutil.cpu_percent(interval=1)


def get_cpu_temp():
    try:
        temps = psutil.sensors_temperatures()

        for name, entries in temps.items():
            for entry in entries:
                if entry.current:
                    return f"{entry.current}°C"

        return "No temperature data"

    except Exception as e:
        return str(e)


def get_ram_info():
    ram = psutil.virtual_memory()

    return {
        "total_gb": round(ram.total / (1024 ** 3), 2),
        "used_gb": round(ram.used / (1024 ** 3), 2),
        "percent": ram.percent
    }


def get_disk_info():
    disks = []

    partitions = psutil.disk_partitions()

    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)

            disks.append({
                "device": part.device,
                "mount": part.mountpoint,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "percent": usage.percent
            })

        except:
            pass

    return disks


def get_fan_speed():
    try:
        fans = psutil.sensors_fans()

        result = []

        for name, entries in fans.items():
            for entry in entries:
                result.append({
                    "fan": name,
                    "speed_rpm": entry.current
                })

        return result if result else "No fan data"

    except Exception as e:
        return str(e)


def get_disk_health():
    disks = []

    if not shutil.which("smartctl"):
        return "smartctl not installed"

    try:
        result = subprocess.check_output(
            ["lsblk", "-d", "-n", "-o", "NAME"],
            text=True
        )

        for disk in result.splitlines():
            path = f"/dev/{disk}"

            try:
                smart = subprocess.check_output(
                    ["smartctl", "-H", path],
                    stderr=subprocess.DEVNULL,
                    text=True
                )

                health = "UNKNOWN"

                if "PASSED" in smart:
                    health = "PASSED"
                elif "FAILED" in smart:
                    health = "FAILED"

                disks.append({
                    "disk": path,
                    "health": health
                })

            except:
                pass

    except Exception as e:
        return str(e)

    return disks

