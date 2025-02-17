from imports import *

class Bot:
    def __init__(self):
        self.start_driver()

    def start_driver(self):
        options = webdriver.ChromeOptions()
        options.debugger_address = "127.0.0.1:9222"
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        print("Bot started")
        self.driver.set_window_size(1920 / 3, 1080 / 3)
        self.driver.get("https://special.pikabu.ru/myoffice_dlya_doma")

    def kill_driver(self):
        if hasattr(self, "driver"):
            self.driver.quit()

    def __del__(self):
        if hasattr(self, "driver"):
            self.kill_driver()
