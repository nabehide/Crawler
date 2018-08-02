import os
import sys
import time
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
import selenium.common.exceptions as EC
import colorama
from colorama import Fore

from Crawler.SendGmail import SendGmail


class Crawler(object):

    def __init__(self, config):

        self.options = webdriver.ChromeOptions()

        self._loadConfig(config)

        if self.headless:
            self.options.add_argument("--headless")
            self.options.add_argument("--disable-gpu")
            self.options.add_argument("--window-size=1280x1696")
        else:
            import pyautogui
            pyautogui.FAILSAFE = False

        self.options.add_argument("--disable-application-cache")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--hide-scrollbars")
        self.options.add_argument("--enable-logging")
        self.options.add_argument("--log-level=0")
        self.options.add_argument("--v=99")
        self.options.add_argument("--single-process")
        self.options.add_argument("--ignore-certificate-errors")
        self.options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64)" +
            "AppleWebkit/537.36 (KHTML, like Gecko) " +
            "Chrome/61.0.3163.100 Safari/537.36")
        if self.profile:
            self.options.add_argument("--user-data-dir=" + self.profile)

        colorama.init(autoreset=True)

        self.timeout = 60

    def _loadConfig(self, config):
        if "driverPath" in config.keys():
            self.driverPath = config["driverPath"]
        else:
            self.driverPath = "./chromedriver"

        if "debug" in config.keys():
            self.debug = config["debug"]
        else:
            self.debug = False

        if "headless" in config.keys():
            self.headless = config["headless"]
        else:
            self.headless = False

        if "mailAddress" in config.keys() and "mailPassword" in config.keys():
            self.flagMail = True
            self.mailAddress = config["mailAddress"]
            self.mailPassword = config["mailPassword"]
            self.sendmail = SendGmail(self.mailAddress, self.mailPassword)
        else:
            self.flagMail = False

        if "profile" in config.keys():
            self.profile = config["profile"]
        else:
            self.profile = False

        if "binaryLocation" in config.keys():
            self.options.binary_location = config["binaryLocation"]

        self.wait = config["wait"] if "wait" in config.keys() else 1

    def open(self, twice=False):
        if twice:
            self.timeout *= 2
            print("timeout", self.timeout)

        while True:
            try:
                self.driver = webdriver.Chrome(
                    self.driverPath, chrome_options=self.options,
                )
                break
            except (ConnectionResetError, BrokenPipeError,
                    ConnectionRefusedError) as e:
                print("retry")
                time.sleep(5)

        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(self.timeout)

        return self._outputMessage("success", sys._getframe().f_code.co_name)

    def close(self):
        try:
            self.driver.quit()
            return self._outputMessage(
                "success", sys._getframe().f_code.co_name)
        except AttributeError:
            return self._outputMessage("fail", sys._getframe().f_code.co_name)

    def _outputMessage(self, status, method, message=""):
        normalColor = Fore.WHITE
        statusColor = Fore.RED if status == "error" else Fore.BLUE
        if self.debug:
            print(normalColor + self._timeStamp(), end="")
            print(statusColor + "[" + status + "]", end="")
            print(normalColor + self.__class__.__name__ + " ", end="")
            print(normalColor + method + " ", end="")
            print(normalColor + message)
        return (self._timeStamp() + "[success]" +
                self.__class__.__name__ + " " + method + " " + message)

    def _mail(self, message):
        self.sendmail.send(
            subject=os.uname()[1] + " " + self.__class__.__name__,
            message=message,
        )

    def _activateWindow(self, index=0, reopen=True):
        try:
            handles = self.driver.window_handles
            self.driver.switch_to.window(handles[index])
            return True

        except (EC.TimeoutException, EC.WebDriverException):
            if reopen:
                print("re-open")
                self.close()
                self.open(True)
                self.login()
            raise True

    def _clickElement(self, el, mouse=False):
        window = self.driver.get_window_position()

        for i in range(2):
            self._activateWindow()
            for x in [-5, 0, 5]:
                for y in [-5, 0, 5]:
                    el.location_once_scrolled_into_view
                    size = el.size
                    offset = self.driver.execute_script(
                        "return window.pageYOffset;")
                    pyautogui.moveTo(
                        [el.location['x'] + window['x'] +
                         size["width"] / 2 + x,
                         el.location['y'] + window['y'] + 74
                         + size["height"] / 2 + y - offset]
                    )
                time.sleep(0.2)

        time.sleep(1)
        if mouse:
            self._activateWindow()
            pyautogui.click()
        else:
            self._click(el, reopen=False)

    def _closeOtherWindows(self, reopen=True):
        try:
            handles = self.driver.window_handles
            for i in list(range(len(handles)))[:0:-1]:
                self.driver.switch_to.window(handles[i])
                self.driver.close()
            self.driver.switch_to.window(handles[0])
            return True

        except (EC.TimeoutException, EC.WebDriverException, IndexError):
            if reopen:
                print("re-open")
                self.close()
                self.open(True)
                self.login()
            raise EC.TimeoutException

    def _timeStamp(self):
        return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

    def _getSoupText(self, reopen=True):
        try:
            text = self.driver.page_source
            soup = BeautifulSoup(text, "html.parser")
            return soup, text
        except (EC.WebDriverException, TypeError):
            currentURL = self.driver.current_url
            if reopen:
                print("re-open _getSoupText")
                self.close()
                self.open(True)
                self.login()
            self.driver.get(currentURL)
            text = self.driver.page_source
            soup = BeautifulSoup(text, "html.parser")
            return soup, text

    def _findElements(self, method, target, retry=3, reopen=True):
        url = self.driver.current_url
        for i in range(retry):
            try:
                return eval("self.driver.find_elements_by_" +
                            method + "(\"" + target + "\")"
                            )
            except (EC.TimeoutException, EC.WebDriverException):
                print(
                    "timeout: Retrying " + target + ' ' +
                    str(i + 1) + "/" + str(retry),
                )
                try:
                    self.driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);")
                except EC.WebDriverException:
                    break
            except (ConnectionResetError, BrokenPipeError,
                    ConnectionRefusedError) as e:
                print(str(e))
                break
            except Exception as e:
                print("other exception", e)
            time.sleep(3)
        if reopen:
            print("re-open")
            self.close()
            self.open(True)
            self.login()
            try:
                self.driver.get(url)
                return eval("self.driver.find_elements_by_" +
                            method + "(\"" + target + "\")"
                            )
            except (EC.TimeoutException, EC.WebDriverException):
                print("Could not find elements", target)
        raise EC.TimeoutException

    def _click(self, element, retry=3, reopen=True):
        url = self.driver.current_url
        for i in range(retry):
            try:
                element.location_once_scrolled_into_view
                time.sleep(self.wait)
                element.click()
            except (EC.TimeoutException, EC.WebDriverException):
                print(
                    "timeout: Retrying click " + str(i + 1) + "/" + str(retry),
                )
                try:
                    self.driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);")
                except EC.WebDriverException:
                    break
            except (ConnectionResetError, BrokenPipeError,
                    ConnectionRefusedError) as e:
                print(str(e))
                break
            except Exception as e:
                print("other exception", e)
            else:
                return True
            time.sleep(3)
        if reopen:
            print("re-open")
            self.close()
            self.open(True)
            self.login()
            self.driver.get(url)
            return True
        raise EC.TimeoutException

    def _getRetry(self, target, retry=3, reopen=True):
        for i in range(retry):
            try:
                time.sleep(self.wait)
                self.driver.get(target)
            except (EC.TimeoutException, EC.WebDriverException):
                print(
                    "timeout: Retrying... " + str(i + 1) + "/" + str(retry),
                    target,
                )
                try:
                    self.driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);")
                except EC.WebDriverException:
                    print("could not scroll")
                    break
            except (ConnectionResetError, BrokenPipeError,
                    ConnectionRefusedError) as e:
                print(str(e))
                break
            else:
                return True
        if reopen:
            print("re-open")
            self.close()
            self.open(True)
            self.login()
            self.driver.get(target)
            return True
        raise EC.TimeoutException
