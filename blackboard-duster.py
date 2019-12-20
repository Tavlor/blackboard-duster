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
    - delay until user has logged in
    - click past cookie notice if needed
~*~ """

import argparse
import getpass
import json
#import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

global args
global driver

def argparse_setup():
    global args
    parser = argparse.ArgumentParser(
        description='Scrapes files from Blackboard courses')
    parser.add_argument(
        'bb_url', metavar='BB_base_URL',
        help='URL for your Blackboard instance.')
    parser.add_argument(
        '-d', '--dir', metavar='download path', default='.',
        help='directory to save your downloads in')
    parser.add_argument(
        '-s', '--sleep', metavar='sleep_time', type=int, default=5,
        help='base amount of time for delays, in seconds')
    # parser.add_argument(
    #    '-l', '--log', metavar='level',type=int,
    #    action='store',default=6,
    #    help='Priority level for logging. 1:debug, 2:info, '
    #    '3:warning, 4:error, 5:critical. '
    #    'Any value > 5 disables logging')
    # parser.add_argument(
    #    '-p', '--print', metavar='level',type=int,
    #    action='store',default=0,
    #    help='Priority level for printing, see --log.')
    # parser.add_argument(
    #    '-b', '--browser', metavar='level',
    #    help='browser to use.')
    args = parser.parse_args()
# end argparse_setup()


# def wait_for_window(driver, timeout=2):
#     time.sleep(round(timeout / 1000))
#     wh_now = driver.window_handles
#     wh_then = vars["window_handles"]
#     if len(wh_now) > len(wh_then):
#         return set(wh_now).difference(set(wh_then)).pop()


# def test_basicPDFdownload():
#     # 4 | click | linkText=asdf
#     driver.find_element(
#         By.LINK_TEXT, "asdf").click()
#     # 5 | click | id=menuPuller |  |
#     driver.find_element(By.ID, "menuPuller").click()
#     # 6 | click | css=#paletteItem\3A_1153658_1 span |  |
#     driver.find_element(
#         By.CSS_SELECTOR, "#paletteItem\\3A_1153658_1 span").click()
#     # 7 | click | css=#anonymous_element_8 > a > span |  |
#     vars["window_handles"] = driver.window_handles
#     # 8 | storeWindowHandle | root |  |
#     driver.find_element(
#         By.CSS_SELECTOR, "#anonymous_element_8 > a > span").click()
#     # 9 | selectWindow | handle=${win5193} |  |
#     vars["win5193"] = wait_for_window(2000)
#     # 10 | close |  |  |
#     vars["root"] = driver.current_window_handle
#     # 11 | selectWindow | handle=${root} |  |
#     driver.switch_to.window(vars["win5193"])
#     # 12 | click | css=#anonymous_element_8 > a > span |  |
#     driver.close()
#     # 13 | click | css=.read |  |
#     driver.switch_to.window(vars["root"])
#     # 14 | close |  |  |
#     driver.find_element(
#         By.CSS_SELECTOR, "#anonymous_element_8 > a > span").click()
#     driver.find_element(By.CSS_SELECTOR, ".read").click()
#     driver.close()
def sleep(mult):
    global args
    time.sleep(args.sleep * mult)

def main():
    global args
    global driver
    argparse_setup()
    driver = webdriver.Firefox()
    driver.get(args.bb_url)
    driver.set_window_size(850, 700)

    # user inputs ID and password via terminal
    print('NetID: ', end='')
    email = input().strip()
    password = getpass.getpass().strip()
    driver.find_element(By.ID, "netid").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "submit").click()
    # allow page time to load, a few seconds

    # bypass cookie warning, if it appears
    driver.find_element(By.ID, "agree_button").click()

    driver.quit()

# end main()


if __name__ == "__main__":
    main()
