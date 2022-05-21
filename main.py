from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import ElementNotInteractableException,\
                                        NoSuchElementException, \
                                        JavascriptException, \
                                        NoSuchWindowException, \
                                        TimeoutException, \
                                        ElementClickInterceptedException
from typing import Union
from time import sleep

from threading import Thread


WINDOW_PATCH_JS = """
funcjs['open_window'] = function (id, type, mark) {
    let sid = document.getElementById("sid").value;
    let domain = document.getElementById("domain-youtube").value;
    newWin = window.open("https://"+domain+"/view-video?sid="+sid+"&id=" + id);
  }
"""


EXPLOIT_JS = """
let hash = document.getElementById("hash").value;
let sid = document.getElementById("sid").value;

var obj = document.getElementById('tmr');
var dur = obj.innerHTML = parseInt(obj.innerHTML);
var played = dur.toFixed(14);

super_data = {'hash': hash, 'sid': sid, 'func': 'ads-check', 'time': dur, 'player_time': played};
console.log(super_data);
        $.ajax({
            url: 'https://aviso.bz/ajax/earnings/ajax-youtube-domain.php', type: 'POST',
            data: super_data,
            dataType: 'json',
            error: function (infa) {
                video_serf = 0;
            },
            success: function (infa) {
                video_serf = 0;
                $('#succes-error').html(infa.html);
            }
        });		

"""


RELOAD_WINDOW_JS = """window.location.reload()"""


class Account:

    def __init__(self, login, password):
        self.login = login
        self.password = password


accounts = \
        [
            Account('ar_sem', 'diman030405')
        ]


class UI:
    INPUT_LOGIN = 'input[name="username"]'
    INPUT_PASSWORD = 'input[name="password"]'

    BTN_LOGIN = 'button[id="button-login"]'

    VIDEO_DIV = 'div[id*="start-ads-"]'

    VIDEO_SPAN = """span[onclick*="funcjs['start_youtube']"]"""
    VIDEO_BUTTON = """span[onclick*="funcjs['open_window']"]"""


class AvisoBot(Thread):
    URL_LOGIN = "https://aviso.bz/login"
    URL_YOUTUBE = "https://aviso.bz/work-youtube"

    def __init__(self, account: Account):
        super().__init__(daemon=True)
        self.browser: Union[Chrome, None] = None
        self.account: Account = account
        self.opts = ChromeOptions()
        self.opts.add_argument('--headless')

    def create_browser(self):
        self.browser = Chrome("chromedriver", options=self.opts)

    def open_page(self, url):
        self.browser.get(url)

    def reload_wait(self):
        WebDriverWait(self.browser, 10).until(
            ec.presence_of_element_located((By.CLASS_NAME, 'user-block__info'))
        )

    def run(self):
        self.create_browser()
        self.open_page(self.URL_LOGIN)
        self.login()
        self.reload_wait()
        self.open_page(self.URL_YOUTUBE)
        self.apply_window_patch()
        self.watch_all()

    def switch_to_video_tab(self):
        self.browser.switch_to.window(self._get_child_window_name())

    def switch_to_main_tab(self):
        self.browser.switch_to.window(self._get_main_window_name())

    def kill_video_tab(self):
        self.browser.close()

    def _get_main_window_name(self):
        return self.browser.window_handles[0]

    def _get_child_window_name(self):
        return self.browser.window_handles[1]

    def apply_window_patch(self):
        self.browser.execute_script(WINDOW_PATCH_JS)

    def run_exploit(self):
        self.browser.execute_script(EXPLOIT_JS)

    def force_video(self, video_div: WebElement):
        video_div.find_element_by_css_selector(UI.VIDEO_SPAN).click()
        open_video_btn = WebDriverWait(video_div, 10).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, UI.VIDEO_BUTTON))
        )
        open_video_btn.click()
        self.switch_to_video_tab()
        sleep(4.5)
        self.run_exploit()

    def watch_all(self):
        video_list = self.find_youtube_items()
        for video_div in video_list:
            try:
                self.force_video(video_div)
            except ElementNotInteractableException:
                continue
            except NoSuchElementException:
                continue
            except NoSuchWindowException:
                self.switch_to_main_tab()
                continue
            except JavascriptException:
                self.kill_video_tab()
                sleep(1)
                self.switch_to_main_tab()
                sleep(1)
                continue
            except TimeoutException:
                continue
            except ElementClickInterceptedException:
                continue
            else:
                sleep(1)
                self.kill_video_tab()
                self.switch_to_main_tab()

        self.switch_to_main_tab()
        sleep(1)
        self.browser.execute_script(RELOAD_WINDOW_JS)
        self.reload_wait()
        sleep(5)
        self.apply_window_patch()
        self.watch_all()

    def btn_login_click(self):
        self.browser.find_element_by_css_selector(UI.BTN_LOGIN).click()

    def login(self):
        self.browser.find_element_by_css_selector(UI.INPUT_LOGIN).send_keys(self.account.login)
        sleep(1)
        self.browser.find_element_by_css_selector(UI.INPUT_PASSWORD).send_keys(self.account.password)
        sleep(1)
        self.btn_login_click()

    def find_youtube_items(self):
        item_list = self.browser.find_elements_by_css_selector(UI.VIDEO_DIV)
        return item_list


if __name__ == '__main__':
    bots = []
    for acc in accounts:
        bot = AvisoBot(acc)
        bot.start()
        bots.append(bot)
    bots[-1].join()
