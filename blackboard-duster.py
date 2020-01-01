#!/usr/bin/env python3
""" ~^~
Blackboard Duster
    Scrapes course materials from your Blackboard courses, such as lecture
    notes and homework
Author: Taylor Smith, Winter 2019
Python Version: 3.7
Notes:
TODO:
    - avoid redundant visit to course home page (just ignore it?)
    - download items directly?
    - make notes on where css selectors come from, so users can change
        if needed
    - ignore useless navpane elements - add custom ignore arg
    - log downloaded items, so they can be ignored next time
~*~ """

import argparse
import getpass
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

global args
global driver
navpane_ignore = {'Announcements', 'Calendar', 'My Grades'}


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


def wait_for_element(locator, delay_time=3, exit_on_fail=False,
                     msg_success='', msg_fail=''):
    """waits until given item appears, optionally exit on failure

    locator is a tuple: (By.constant, string)
    if messages are empty no newline will be generated
    returns the element waited for
    """
    global args
    global driver
    element = None
    try:
        element = WebDriverWait(
            driver, args.delay * delay_time).until(
            EC.presence_of_element_located(locator))
        if msg_success:
            print(msg_success)
    except TimeoutException:
        if msg_fail:
            print(msg_fail)
        if exit_on_fail:
            driver.quit()
            exit()
    return element


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
    # try:
    #     element = WebDriverWait(driver, args.delay * 3).until(
    #         EC.presence_of_element_located((By.ID, 'agree_button'))
    #     )
    #     print('I am accepting the cookie notice, I hope that is ok!')
    #     element.click()
    # except TimeoutException:
    #     print('I did not see a cookie notice.')
    cookie_bttn = wait_for_element(
        (By.ID, 'agree_button'),
        msg_success='I am accepting the cookie notice, I hope that is ok!',
        msg_fail='I did not see a cookie notice.')
    if cookie_bttn is not None:
        print("clicking cookie button!")
        cookie_bttn.click


def get_courses_info():
    """returns an array of dicts with info about each course

    each dict contains {'name', 'url'}
    """
    global driver
    global args
    result = []
    # try:
    #     course_links=WebDriverWait(driver, args.delay * 5).until(
    #         EC.presence_of_element_located((By.CSS_SELECTOR,
    #                                         'div#div_25_1 a'))
    #     )
    # except TimeoutException:
    #     print('I did not see your course list! Aborting')
    #     driver.quit()
    #     exit()
    wait_for_element(
        (By.CSS_SELECTOR, 'div#div_25_1 a'), exit_on_fail=True,
        msg_fail='I did not see your course list! Aborting')
    course_links = driver.find_elements_by_css_selector(
        'div#div_25_1 a')
    for link in course_links:
        result.append({
            'name': link.text,
            'url': link.get_attribute('href')
        })
    return result


def get_navpane_info():
    """returns an array of dicts for items in the navpane

    each dict contains {'name', 'url'}
    """
    global driver
    wait_for_element(
        (By.CSS_SELECTOR, 'ul#courseMenuPalette_contents'),
        exit_on_fail=True,
        msg_fail='I could not access the navpane! Aborting')
    page_links = driver.find_elements_by_css_selector(
        'ul#courseMenuPalette_contents a')
    result = []
    for link in page_links:
        title = link.find_element_by_css_selector('span')
        result.append({
            'name': title.get_attribute('title'),
            'url': link.get_attribute('href')
        })
    return result


def parse_page(page_url):
    """returns an array of dicts for each file link in page

    recursivly handles folders
    takes the url as a string
    each dict contains {'name', 'url'}
    """
    global driver
    driver.get(page_url)
    content_list = wait_for_element(
        (By.CSS_SELECTOR, 'ul#content_listContainer'),
        msg_fail='This page does not have a content list.')
    if content_list is not None:
        return []
    page_content = driver.find_elements_by_css_selector(
        'ul#content_listContainer li')
    result = []
    for item in page_content:
        i_type = item.find_element_by_css_selector(
            'img').get_attribute('alt')
        if i_type == 'File':
            # files are just a link
            result.append({
                'name': item.find_element_by_css_selector(
                    'a span').text,
                'url': item.find_element_by_css_selector(
                    'a').get_attribute('href')
            })
        elif i_type == 'Item':
            # items contain attachments
            # TODO handle items
            pass
        elif i_type == 'Assignment':
            # assignments contain attachments
            # TODO handle assignments
            pass
        elif i_type == 'Content Folder':
            # folders contain another page
            child_url = item.find_element_by_css_selector(
                'a').get_attribute('href')
            my_url = page_url
            result.append(parse_page(child_url))
            driver.get(my_url)
            pass
    return result


def main():
    global args
    global driver
    argparse_setup()
    driver = webdriver.Firefox()
    driver.get(args.bb_url)
    # choose a nice size - the navpane is invisible at small widths,
    # but selenium can still see its elements
    driver.set_window_size(850, 700)
    manual_login()
    print('Alright, I can drive from here.')
    # TODO are links visible behind the cookie notice?
    accept_cookies()
    courses = get_courses_info()
    print('I found {0:d} courses. I will go through each one now!'
          .format(len(courses)))

    # iterate over each course
    for course in courses:
        print(course['name'])
        driver.get(course['url'])
        navpane = get_navpane_info()
        for page in navpane:
            # a few pages have no (downloadable) content, skip them
            if page['name'] in navpane_ignore:
                print('  *SKIPPED* ' + page['name'])
                continue
            # TODO don't reload the home page
            # TODO skip emails page - different for each school
            print('   ' + page['name'])
            for item in parse_page(page['url']):
                print('    ' + item['name'])
                print('      ' + item['url'])
    print('That is all I could find! You should double check.')
    driver.quit()
# end main()


if __name__ == "__main__":
    main()
