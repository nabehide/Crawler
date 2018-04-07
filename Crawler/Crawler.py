import sys
import time
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
import selenium.common.exceptions as EC
from selenium.webdriver.chrome.options import Options
import pyautogui
from colorama import Fore

from Crawler.SendGmail import SendGmail


class Crawler(object):

    def __init__(self, config):

        self.driverPath = config["driverPath"]
        self.debug = config["debug"]
        self.headless = config["headless"]
        self.mailAddress = config["mailAddress"]
        self.mailPassword = config["mailPassword"]
        self.profile = config["profile"]

        self.options = Options()
        if self.headless:
            self.options.add_argument("--headless")
        self.options.add_argument("--disable-application-cache")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--no-sandbox")
        if self.profile:
            self.options.add_argument(
                "--user-data-dir=./profile_" + self.__class__.__name__)

        self.sendmail = SendGmail(self.mailAddress, self.mailPassword)

        self.open()
        self.close()

    def open(self):
        while True:
            try:
                self.driver = webdriver.Chrome(
                    self.driverPath, chrome_options=self.options,
                )
                break
            except ConnectionResetError:
                print("retry")
                time.sleep(5)

        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(60)

        return self._outputMessage("success", sys._getframe().f_code.co_name)

    def close(self):
        self.driver.quit()
        return self._outputMessage("success", sys._getframe().f_code.co_name)

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

    def _activateWindow(self, index=0, reopen=True):
        try:
            handles = self.driver.window_handles
            self.driver.switch_to.window(handles[index])
            return True

        except (EC.TimeoutException, EC.WebDriverException):
            if reopen:
                print("re-open")
                self.close()
                self.open()
                self.login()
            raise True

    def _clickElement(self, el, mouse=False):
        position = self.driver.get_window_position()
        self._activateWindow()
        el.location_once_scrolled_into_view
        size = el.size
        offset = self.driver.execute_script("return window.pageYOffset;")
        pyautogui.moveTo(
            [el.location['x'] + position['x'] + size["width"] / 2 + 1,
             el.location['y'] + position['y'] + 74 + size["height"] / 2 + 1
             - offset]
        )

        time.sleep(1)
        self._activateWindow()
        el.location_once_scrolled_into_view
        offset = self.driver.execute_script("return window.pageYOffset;")
        pyautogui.moveTo(
            [el.location['x'] + position['x'] + size["width"] / 2,
             el.location['y'] + position['y'] + 74 + size["height"] / 2
             - offset]
        )

        time.sleep(2)
        if mouse:
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
                self.open()
                self.login()
            raise EC.TimeoutException

    def _timeStamp(self):
        return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

    def _getSoupText(self, reopen=True):
        try:
            text = self.driver.page_source
            soup = BeautifulSoup(text, "html.parser")
            return soup, text
        except EC.WebDriverException:
            currentURL = self.driver.current_url
            if reopen:
                print("re-open _getSoupText")
                self.close()
                self.open()
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
            except ConnectionResetError as e:
                print("ConnectionResetError", e)
                break
            except Exception as e:
                print("other exception", e)
            time.sleep(3)
        if reopen:
            print("re-open")
            self.close()
            self.open()
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
                time.sleep(1)
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
            except ConnectionResetError as e:
                print("ConnectionResetError", e)
                break
            except Exception as e:
                print("other exception", e)
            else:
                return True
            if i == 0:
                time.sleep(5)
            else:
                time.sleep(3)
        if reopen:
            print("re-open")
            self.close()
            self.open()
            self.login()
            self.driver.get(url)
            return True
        raise EC.TimeoutException

    def _getRetry(self, target, retry=3, reopen=True):
        for i in range(retry):
            try:
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
            except ConnectionResetError as e:
                print("ConnectionResetError", e)
                break
            else:
                return True
        if reopen:
            print("re-open")
            self.close()
            self.open()
            self.login()
            self.driver.get(target)
            return True
        raise EC.TimeoutException
