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
    chrome_options.add_argument(
        '--disable-blink-features=AutomationControlled')

    # Initialising chrome
    chrome = uc.Chrome(browser_executable_path="C:\Program Files\Google\Chrome\Application\chrome.exe",
                       use_subprocess=True, chrome_options=chrome_options)
    # chrome.set_window_size(1920, 1080)
    # chrome.maximize_window()

    # Redirecting to URL
    chrome.get(url)

    try:
        # reCAPTCHA selectors
        captcha_selector = '#recaptcha-anchor > div.recaptcha-checkbox-border'
        audio_selector = '#recaptcha-audio-button'
        download_selector = '#rc-audio > div.rc-audiochallenge-tdownload > a'

        # Wait for CAPTCHA iframe to be visible
        WebDriverWait(chrome, 20).until(EC.frame_to_be_available_and_switch_to_it(
            (By.CSS_SELECTOR, "iframe[title='reCAPTCHA']")))
        captcha = WebDriverWait(chrome, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, captcha_selector)))

        time.sleep(2)

        # Click the CAPTCHA
        captcha.click()

        chrome.switch_to.default_content()

        # Wait for challenge to be visible
        WebDriverWait(chrome, 20).until(EC.frame_to_be_available_and_switch_to_it(
            (By.CSS_SELECTOR, "iframe[title='recaptcha challenge expires in two minutes']")))
        audio_btn = WebDriverWait(chrome, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, audio_selector)))

        time.sleep(2)

        # Click the audio button
        audio_btn.click()

        chrome.switch_to.default_content()

        # Wait for audio challenge to be visible
        WebDriverWait(chrome, 20).until(EC.frame_to_be_available_and_switch_to_it(
            (By.CSS_SELECTOR, "iframe[title='recaptcha challenge expires in two minutes']")))
        WebDriverWait(chrome, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, download_selector)))

        time.sleep(2)
        # Get audio download link
        download_link = chrome.find_element(
            By.CSS_SELECTOR, download_selector).get_attribute("href")

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

        text = recognizer.recognize_google(audio)

        # Input the text from speech
        input_box = chrome.find_element(By.ID, 'audio-response')

        time.sleep(2)

        input_box.send_keys(text.lower())
        input_box.send_keys(Keys.ENTER)

    except Exception:
        # Check if CAPTCHA has already been solved
        checkmark_selector = '#recaptcha-anchor > div.recaptcha-checkbox-checkmark'

        try:
            # Wait for CAPTCHA iframe to be visible
            WebDriverWait(chrome, 20).until(EC.frame_to_be_available_and_switch_to_it(
                (By.CSS_SELECTOR, "iframe[title='reCAPTCHA']")))
            WebDriverWait(chrome, 10).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, checkmark_selector)))

            # No errors, so CAPTCHA is solved
            chrome.close()
            return True

        except Exception:
            chrome.close()
            return False

    # Get fail text; successful operation otherwise
    try:
        # Wait for fail text
        WebDriverWait(chrome, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#rc-audio > div.rc-audiochallenge-error-message')))

        fail_text = chrome.find_element(
            By.CSS_SELECTOR, '#rc-audio > div.rc-audiochallenge-error-message').text

        if len(fail_text) > 0:
            chrome.close()
            return False

    except TimeoutException:
        # CAPTCHA was solved
        chrome.switch_to.default_content()

        verify_btn = chrome.find_element(By.TAG_NAME, "button")

        time.sleep(2)

        # Finally, click the verify button
        verify_btn.click()

        chrome.close()

        time.sleep(5)
        return True


async def solve(url: str) -> None:
    solved = False

    while solved == False:
        solved = SolveCaptcha(url)

    return
