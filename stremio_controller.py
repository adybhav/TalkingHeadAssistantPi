import os
import subprocess
import time


PACKAGE = "com.stremio.one"


def _load_dotenv_if_available():
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _adb(args):
    result = subprocess.run(
        ["adb", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _current_foreground_package():
    output = _adb(["shell", "dumpsys", "window"])
    for line in output.splitlines():
        if "mCurrentFocus" in line or "mFocusedApp" in line:
            if PACKAGE in line:
                return PACKAGE
    return None


def _launch_stremio(max_attempts=3):
    for attempt in range(max_attempts):
        _adb(["shell", "monkey", "-p", PACKAGE, "-c", "android.intent.category.LAUNCHER", "1"])
        time.sleep(1.0 + attempt * 0.5)

        if _current_foreground_package() == PACKAGE:
            return True

    return False


def _press(key, delay=0.1):
    _adb(["shell", "input", "keyevent", str(key)])
    time.sleep(delay)


def _classify_title(title):
    _load_dotenv_if_available()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "unknown"

    try:
        import google.generativeai as genai
    except ImportError:
        return "unknown"

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-flash-latest")
    prompt = f"Is '{title}' a movie or a TV show? Just reply with 'movie' or 'series'."
    response = model.generate_content(prompt)
    answer = response.text.strip().lower()

    if "movie" in answer:
        return "movie"
    if "series" in answer or "tv show" in answer:
        return "series"
    return "unknown"


def _navigate_to_search():
    _press(21)
    _press(19)
    _press(66)


def _play_series():
    _press(20)
    time.sleep(0.3)
    _press(66)


def _play_movie():
    _press(66)
    time.sleep(0.5)
    _press(66)


def _search_for(title, content_type):
    safe_title = title.replace(" ", "_")
    _adb(["shell", "input", "text", safe_title])
    time.sleep(0.1)
    _press(61)
    time.sleep(0.5)

    if content_type == "series":
        _play_series()
    else:
        _play_movie()


def play_title(title):
    if not title:
        return False

    _load_dotenv_if_available()
    device_ip = os.getenv("DEVICE_IP")
    if device_ip:
        _adb(["connect", device_ip])

    if not _launch_stremio():
        return False

    content_type = _classify_title(title)
    _navigate_to_search()
    _search_for(title, content_type)
    return True
