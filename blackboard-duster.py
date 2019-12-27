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
    - iterate over courses
    - iterate over course homepage elements
~*~ """

import argparse
import getpass
import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
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


def sleep(seconds):
    """uses global multiplier to delay the script"""
    global args
    time.sleep(args.delay * seconds)


def manual_login():
    """allow user to signs in manually

     waits until the Blackboard homepage appears, returns nothing
     """
    print('Please log into your university Blackboard account - I will'
          ' wait for you to reach the home page!')
    # looking for "Welcome, #### – Blackboard Learn" (the dash is NOT a
    # minus sign!)
    while not driver.title.startswith('Welcome, ') or \
            not driver.title.endswith(' – Blackboard Learn'):
        pass


def accept_cookies():
    """if the cookie notice appears, click 'accept'"""
    try:
        element = WebDriverWait(driver, args.delay * 10).until(
            EC.presence_of_element_located((By.ID, 'agree_button'))
        )
        print('I am accepting the cookie notice, I hope that is ok!')
        element.click()
    except TimeoutException:
        print('I did not see a cookie notice.')


def get_courses_home():
    """produces an array of URLs for each course's homepage"""
    global driver
    course_links = driver.find_elements_by_css_selector('div#div_25_1 a')
    result = []
    for link in course_links:
        result.append(link.get_attribute('href'))
    return result


def main():
    global args
    global driver
    argparse_setup()
    driver = webdriver.Firefox()
    driver.get(args.bb_url)
    # the course sidebar is invisible in range [320,1024]
    driver.set_window_size(1030, 700)
    manual_login()
    print('Alright, I can drive from here.')
    accept_cookies()
    course_urls = get_courses_home()
    print('I found {0:d} courses.'.format(len(course_urls)))

    print('That was all I could find! You should probably double check.')
    driver.quit()
# end main()


if __name__ == "__main__":
    main()
