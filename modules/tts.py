import config
import re

from TTS.api import TTS

# Load the YourTTS model (zero-shot voice cloning)
tts = TTS(
    model_name="tts_models/multilingual/multi-dataset/your_tts",
    progress_bar=False
)
tts.to("cuda")  # Use GPU if available

NUMBER_WORDS = {
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
    "10": "ten",
    "11": "eleven",
    "12": "twelve",
    "13": "thirteen",
    "14": "fourteen",
    "15": "fifteen",
    "16": "sixteen",
    "17": "seventeen",
    "18": "eighteen",
    "19": "nineteen",
    "20": "twenty",
}

TENS_WORDS = {
    20: "twenty",
    30: "thirty",
    40: "forty",
    50: "fifty",
    60: "sixty",
    70: "seventy",
    80: "eighty",
    90: "ninety",
}


def number_to_words(value):
    if value < 0:
        return "minus " + number_to_words(abs(value))

    if value <= 20:
        return NUMBER_WORDS[str(value)]

    if value < 100:
        tens = value // 10 * 10
        remainder = value % 10
        if remainder:
            return f"{TENS_WORDS[tens]} {NUMBER_WORDS[str(remainder)]}"
        return TENS_WORDS[tens]

    if value < 1000:
        hundreds = value // 100
        remainder = value % 100
        words = f"{NUMBER_WORDS[str(hundreds)]} hundred"
        if remainder:
            words += " " + number_to_words(remainder)
        return words

    if value < 10000:
        thousands = value // 1000
        remainder = value % 1000
        words = f"{number_to_words(thousands)} thousand"
        if remainder:
            words += " " + number_to_words(remainder)
        return words

    return " ".join(NUMBER_WORDS[digit] for digit in str(value))


def normalize_for_speech(text):
    def replace_number(match):
        return number_to_words(int(match.group(0)))

    text = re.sub(r"\b\d+\b", replace_number, text)
    text = re.sub(r"\b([a-zA-Z])\)", r"\1.", text)
    return text


def text_to_speech(text, out_path, speaker_wav="./medusa_audio.wav"):
    tts.tts_to_file(
        text=normalize_for_speech(text),
        speaker_wav=speaker_wav,
        language="en",
        file_path=out_path
    )
