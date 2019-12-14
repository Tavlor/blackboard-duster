#!/usr/bin/env python3
""" ~^~
Blackboard Duster
    Scrapes course materials from your Blackboard courses, such as lecture
    notes and homework
Author: Taylor Smith, Winter 2019
Python Version: 3.7
Notes:
TODO:
    - restructure selenium generated code
    - user login
    - click past cookie notice if needed
~*~ """

import argparse
import json
#import pytest
import time
from selenium import webdriver


def __argparse_setup():
    psr = argparse.ArgumentParser(
        description='Scrapes files from Blackboard classes')
    psr.add_argument('bb_url', metavar='Blackboard base URL',
                     help='URL for your Blackboard instance.')
    psr.add_argument('-d', '--dir', metavar='download path',
                     help='directory to save your downloads in',
                     default='.')
    # psr.add_argument('-l', '--log', metavar='level',type=int,
    #                  action='store',default=6,
    #                  help='Priority level for logging. 1:debug, 2:info, '
    #                  '3:warning, 4:error, 5:critical. '
    #                  'Any value > 5 disables logging')
    # psr.add_argument('-p', '--print', metavar='level',type=int,
    #                  action='store',default=0,
    #                  help='Priority level for printing, see --log.')

    return psr
# end argparse_setup()


def wait_for_window(driver, timeout=2):
    time.sleep(round(timeout / 1000))
    wh_now = driver.window_handles
    wh_then = vars["window_handles"]
    if len(wh_now) > len(wh_then):
        return set(wh_now).difference(set(wh_then)).pop()


def test_basicPDFdownload():
    # Test name: basic PDF download
    # Step # | name | target | value | comment
    # 3 | click | id=agree_button |  |
    self.driver.find_element(By.ID, "agree_button").click()
    # 4 | click | linkText=asdf
    self.driver.find_element(
        By.LINK_TEXT, "asdf").click()
    # 5 | click | id=menuPuller |  |
    self.driver.find_element(By.ID, "menuPuller").click()
    # 6 | click | css=#paletteItem\3A_1153658_1 span |  |
    self.driver.find_element(
        By.CSS_SELECTOR, "#paletteItem\\3A_1153658_1 span").click()
    # 7 | click | css=#anonymous_element_8 > a > span |  |
    self.vars["window_handles"] = self.driver.window_handles
    # 8 | storeWindowHandle | root |  |
    self.driver.find_element(
        By.CSS_SELECTOR, "#anonymous_element_8 > a > span").click()
    # 9 | selectWindow | handle=${win5193} |  |
    self.vars["win5193"] = self.wait_for_window(2000)
    # 10 | close |  |  |
    self.vars["root"] = self.driver.current_window_handle
    # 11 | selectWindow | handle=${root} |  |
    self.driver.switch_to.window(self.vars["win5193"])
    # 12 | click | css=#anonymous_element_8 > a > span |  |
    self.driver.close()
    # 13 | click | css=.read |  |
    self.driver.switch_to.window(self.vars["root"])
    # 14 | close |  |  |
    self.driver.find_element(
        By.CSS_SELECTOR, "#anonymous_element_8 > a > span").click()
    self.driver.find_element(By.CSS_SELECTOR, ".read").click()
    self.driver.close()


def main():

    parser = __argparse_setup()
    args = parser.parse_args()
    driver = webdriver.Firefox()

    driver.get(args.bb_url)
    driver.set_window_size(550, 700)

    # TODO allow user to log in

    driver.quit()

# end main()


if __name__ == "__main__":
    main()
