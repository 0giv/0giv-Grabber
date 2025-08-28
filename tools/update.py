import os
from time import sleep
from zipfile import ZipFile

import requests


class Update():
    def __init__(self):
        self.version = '1.0'
        self.github = 'https://raw.githubusercontent.com/0giv/0giv-Grabber/main/tools/update.py'
        self.zipfile = 'https://github.com/0giv/0giv-Grabber/archive/refs/heads/main.zip'
        self.update_checker()

    def update_checker(self):
        code = requests.get(self.github).text
        if "self.version = '1.0'" in code:
            print('This version is up to date!')
            print('Exiting...')
            sleep(2)
            exit()
        else:
            print('''
                    ███╗   ██╗███████╗██╗    ██╗    ██╗   ██╗██████╗ ██████╗  █████╗ ████████╗███████╗██╗
                    ████╗  ██║██╔════╝██║    ██║    ██║   ██║██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██║
                    ██╔██╗ ██║█████╗  ██║ █╗ ██║    ██║   ██║██████╔╝██║  ██║███████║   ██║   █████╗  ██║
                    ██║╚██╗██║██╔══╝  ██║███╗██║    ██║   ██║██╔═══╝ ██║  ██║██╔══██║   ██║   ██╔══╝  ╚═╝
                    ██║ ╚████║███████╗╚███╔███╔╝    ╚██████╔╝██║     ██████╔╝██║  ██║   ██║   ███████╗██╗
                    ╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝      ╚═════╝ ╚═╝     ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝
                                      Your version of 0giv Grabber is outdated!''')
            choice = input('\nWould you like to update? (y/n): ')
            if choice.lower() == 'y':
                new_version_source = requests.get(self.zipfile)
                with open("0giv-Grabber-main.zip", 'wb')as zipfile:
                    zipfile.write(new_version_source.content)
                with ZipFile("0giv-Grabber-main.zip", 'r') as filezip:
                    filezip.extractall(path=os.path.join(os.path.expanduser("~"), "Desktop"))
                os.remove("0giv-Grabber-main.zip")
                print('The new version is now on your desktop.\nUpdate Complete!')
                print("Exiting...")
                sleep(5)
            if choice.lower() == 'n':
                print('Exiting...')
                sleep(2)
                exit()


if __name__ == '__main__':
    Update()
