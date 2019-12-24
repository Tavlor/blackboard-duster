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
~*~ """

import argparse
import getpass
import json
# import pytest
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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
        '-s', '--save', metavar='save_path', default='.',
        help='directory to save your downloads in')
    parser.add_argument(
        '-d', '--delay', metavar='delay_mult', type=int, default=1,
        help='multiplier for sleep/delays')
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


def sleep(seconds):
    """uses global multiplier to delay the script"""
    global args
    time.sleep(args.delay * seconds)


def main():
    global args
    global driver
    argparse_setup()
    driver = webdriver.Firefox()
    driver.get(args.bb_url)
    driver.set_window_size(850, 700)

    # user signs in manualy - script waits until the homepage appears
    print('Please log into your university Blackboard account - I will'
        ' wait for you to reach the home page!')
    while not driver.title.startswith('Welcome, ') or \
            not driver.title.endswith(' – Blackboard Learn'):
        # looking for "Welcome, #### – Blackboard Learn" (the dash is
        # NOT a minus sign!)
        pass
    # bypass cookie warning, if it appears
    print('Alright, I can drive from here.')
    try:
        element = WebDriverWait(driver, args.delay * 10).until(
            EC.presence_of_element_located((By.ID, 'agree_button'))
        )
        print('I am accepting the cookie notice, I hope that is ok!')
        element.click()
    except TimeoutException:
        print('I did not see a cookie notice.')
    print('That was all I could find! You should probably double check.')
    driver.quit()

# end main()


if __name__ == "__main__":
    main()
