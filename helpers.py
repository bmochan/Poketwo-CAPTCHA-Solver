from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

import undetected_chromedriver as uc
import time

import requests

from pydub import AudioSegment
import speech_recognition as sr

def SolveCaptcha(url: str) -> bool:
    # Defining chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-extensions")

    # Initialising chrome
    chrome = uc.Chrome(browser_executable_path="C:\Program Files\Google\Chrome\Application\chrome.exe",
                       use_subprocess=True, chrome_options=chrome_options)
    chrome.set_window_size(1920, 1080)
    chrome.maximize_window()

    # Redirecting to URL
    chrome.get(url)

    try:
        # reCAPTCHA selectors
        captcha_selector = '#recaptcha-anchor > div.recaptcha-checkbox-border'
        audio_selector = '#recaptcha-audio-button'
        download_selector = '#rc-audio > div.rc-audiochallenge-tdownload > a'

        # Wait for CAPTCHA to be visible
        WebDriverWait(chrome, 20).until(EC.frame_to_be_available_and_switch_to_it(
            (By.CSS_SELECTOR, "iframe[title='reCAPTCHA']")))
        captcha = WebDriverWait(chrome, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, captcha_selector)))

        time.sleep(3)

        # Click the captcha
        captcha.click()

        chrome.switch_to.default_content()

        # Wait for challenge to be visible
        WebDriverWait(chrome, 20).until(EC.frame_to_be_available_and_switch_to_it(
            (By.CSS_SELECTOR, "iframe[title='recaptcha challenge expires in two minutes']")))
        audio_btn = WebDriverWait(chrome, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, audio_selector)))

        time.sleep(3)

        # Click the audio button
        audio_btn.click()

        chrome.switch_to.default_content()

        # Wait for audio challenge to be visible
        WebDriverWait(chrome, 20).until(EC.frame_to_be_available_and_switch_to_it(
            (By.CSS_SELECTOR, "iframe[title='recaptcha challenge expires in two minutes']")))
        WebDriverWait(chrome, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, download_selector)))

        # Get audio download link
        download_link = chrome.find_element(
            By.CSS_SELECTOR, download_selector).get_attribute("href")

    except TimeoutException:
        return False

    # Save the audio to disk as an MP3
    r = requests.get(download_link)
    with open('sound.mp3', 'wb') as f:
        f.write(r.content)

    # Convert audio to WAV and save to disk
    # ffmpeg must be a PATH variable for this operation
    sound = AudioSegment.from_mp3("sound.mp3")
    sound.export("sound.wav", format="wav")

    sample_audio = sr.AudioFile('sound.wav')

    # Comprehend the audio
    recognizer = sr.Recognizer()
    audio = None

    with sample_audio as source:
        audio = recognizer.record(source)

    text_keys = recognizer.recognize_google(audio)

    # Input the text from speech
    input_box = chrome.find_element(By.ID, 'audio-response')

    input_box.send_keys(text_keys.lower())
    input_box.send_keys(Keys.ENTER)

    # Get fail text; successful operation otherwise
    try:
        #Wait for fail text
        w = WebDriverWait(chrome, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#rc-audio > div.rc-audiochallenge-error-message')))

        fail_text = chrome.find_element(
            By.CSS_SELECTOR, '#rc-audio > div.rc-audiochallenge-error-message').text
        if len(fail_text) > 0:
            return False

    except TimeoutException:
        return True


async def solve(url: str) -> None:
    solved = False

    while solved == False:
        solved = SolveCaptcha(url)
