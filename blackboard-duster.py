#!/usr/bin/env python3
""" ~^~
Blackboard Duster
    Scrapes course materials from your Blackboard courses, such as lecture
    notes and homework
Author: Taylor Smith, Winter 2019
Python Version: 3.7
Notes: Uses Selenium to scrape urls from Blackboard, then urllib to
    download the files
TODO:
    - avoid redundant visit to course home page (just ignore it?)
    - make notes on where css selectors come from, so users can change
        if needed
    - ignore useless navpane elements - add custom ignore arg
    - allow user to choose browser
    - log downloaded items, so they can be ignored next time
    - dump notes from items/assignments into a .txt : use div.details
    - print unrecognised MIME types
~*~ """

import argparse
import json
import urllib
from time import sleep
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from mime_types import MIME_TYPES

global args
global driver
navpane_ignore = {'Announcements', 'Calendar', 'My Grades'}


class Url:
    """contains useful information about a link

    'name': friendly name of url
    'url': url found on page, will (probably) get redirected
    'save_dir': relative to download path, usually the page's name
    """

    def __init__(self, url, name, save_dir=''):
        self.url = url
        self.name = name
        self.save_dir = save_dir

    def __repr__(self):
        return '{0:s}\n    {1:s}\n    {2:s}'.format(
            self.url, self.name, self.save_dir)


def parse_args():
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
        '--delay', metavar='delay_mult', type=int, default=1,
        help='multiplier for sleep/delays')
    parser.add_argument(
        '-w', '--webdriver', '--wd', metavar='name', default='firefox',
        help='browser WebDriver to use - either "firefox" or \
            "chrome". You must have the WebDriver in your system \
            path. Currently, only firefox is supported; that \
            will change in the future')
    parser.add_argument(
        '-b', '--binary', metavar='file', default=None,
        help='currently not working. path to the binary you want to use - use if your \
            browser binary is not in the default location')
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
    args = parser.parse_args()
    # modify arguments as needed
    args.save = os.path.abspath(args.save)
    args.webdriver = args.webdriver.lower().strip()
# end parse_args()


def get_ff_profile():
    """ sets up a profile to configure download options"""
    global args
    profile = webdriver.FirefoxProfile()
    # enable custom save location
    profile.set_preference('browser.download.folderList', 2)
    # set save location
    profile.set_preference('browser.download.dir', args.save)
    # disable showing the download manager
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    # disable save popup
    profile.set_preference(
        'browser.helperApps.neverAsk.saveToDisk', ','.join(MIME_TYPES))
    # disable built-in PDF viewer
    profile.set_preference('pdfjs.disabled', True)
    # disable scanning for plugins - in case there's other file viewers
    profile.set_preference('plugin.scan.plid.all', False)

    profile.set_preference('browser.helperApps.alwaysAsk.force', False)
    return profile


def get_ch_options():
    """ sets up a ChromeOptions object

    selenium cannot create a chrome profile so options are used
    instead.
    """
    global args
    options = webdriver.ChromeOptions()
    if args.binary is not None:
        options.binary_location = args.binary.strip()
    options.add_experimental_option("prefs", {
        'download.default_directory': args.save,
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'plugins.always_open_pdf_externally': True,
        'safebrowsing.enabled': True
    })
    print(options.binary_location)
    return options


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
        element = WebDriverWait(driver, args.delay * 4).until(
            EC.presence_of_element_located((By.ID, 'agree_button'))
        )
        print('I am accepting the cookie notice, I hope that is ok!')
        element.click()
    except TimeoutException:
        print('I did not see a cookie notice.')


def get_courses_info():
    """returns an array of Url objects for each course

    expects homepage to already be loaded
    """
    global driver
    global args
    result = []
    try:
        course_links = WebDriverWait(driver, args.delay * 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            'div#div_25_1 a'))
        )
    except TimeoutException:
        print('I did not see your course list! Aborting')
        driver.quit()
        exit()
    course_links = driver.find_elements_by_css_selector(
        'div#div_25_1 a')
    for c_l in course_links:
        link = Url(
            c_l.get_attribute('href'),
            c_l.text,
            c_l.text
        )
        result.append(link)
    return result


def get_navpane_info(course_url):
    """returns an array of Url objects for items in the navpane

    takes a Url object for the course, loads the page
    """
    global driver
    global args
    driver.get(course_url.url)
    try:
        WebDriverWait(driver, args.delay * 4).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'ul#courseMenuPalette_contents')
            )
        )
    except TimeoutException:
        print('I could not access the navpane! Aborting')
        driver.quit()
        exit()
    page_links = driver.find_elements_by_css_selector(
        'ul#courseMenuPalette_contents a')
    result = []
    for link in page_links:
        title = link.find_element_by_css_selector('span')
        # the page title should be the name of its folder
        link = Url(
            link.get_attribute('href'),
            title.get_attribute('title'),
            '{0}/{1}'.format(course_url.save_dir,
                             title.get_attribute('title'))
        )
        result.append(link)
    return result


def gather_urls(page_url):
    """gathers available files on the page, handles folders

    page_url: Url object
    returns Url array
    """
    global driver
    global args
    driver.get(page_url.url)
    result = []
    folders = []
    try:
        WebDriverWait(driver, args.delay * 3).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                'ul#content_listContainer'))
        )
    except TimeoutException:
        print('This page does not have a content list.')
        return result
    # get a list of all items in the content list
    page_content = driver.find_elements_by_css_selector(
        'ul#content_listContainer > li')
    for item in page_content:
        i_type = item.find_element_by_css_selector(
            'img').get_attribute('alt')
        # in the header holding the name there is a hidden <span> that
        # gets in the way; ignore it by looking for the style attribute
        i_name = item.find_element_by_css_selector('span[style]').text
        print('    {0:s}: {1:s}'.format(i_type, i_name))
        if i_type == 'File':
            # files are just a link
            link = Url(
                item.find_element_by_css_selector(
                    'a').get_attribute('href'),
                i_name,
                page_url.save_dir
            )
            print('     ~ {0:s}'.format(link.url))
            result.append(link)
        elif i_type == 'Content Folder':
            # folders contain another page
            link = Url(
                item.find_element_by_css_selector(
                    'a').get_attribute('href'),
                i_name,
                '{0}/{1}'.format(page_url.save_dir, i_name)
            )
            folders.append(link)
        else:
            print('    ** Unsupported item type - attachments will be \
                collected *')
        # look for attachments; Items and Assignments usually have
        # some
        i_files = item.find_elements_by_css_selector(
            'ul.attachments > li')
        for file in i_files:
            link = Url(
                file.find_element_by_css_selector(
                    'a').get_attribute('href'),
                file.find_element_by_css_selector('a').text.strip(),
                '{0}/{1}'.format(page_url.save_dir, i_name)
            )
            print('     - {0:s}'.format(link.name))
            print('       ~ {0:s}'.format(link.url))
            result.append(link)
    # recursivly parse each folder's page
    for folder_url in folders:
        result = result + gather_urls(folder_url)
        print('page done')
    return result


def main():
    global args
    global driver
    parse_args()
    if args.webdriver == 'firefox':
        driver = webdriver.Firefox(firefox_profile=get_ff_profile())
    elif args.webdriver == 'chrome':
        driver = webdriver.Chrome(options=get_ch_options())
    else:
        print('sorry, but {0:s} is not a supported WebDriver. \
            Aborting'.format(args.webdriver))
        exit()
    print("here we go!")
    driver.get(args.bb_url)
    # choose a nice size - the navpane is invisible at small widths,
    # but selenium can still see its elements
    driver.set_window_size(1200, 700)
    manual_login()
    print('Alright, I can drive from here.')
    # TODO are links visible behind the cookie notice?
    accept_cookies()
    courses = get_courses_info()
    print('I found {0:d} courses. I will go through each one now!'
          .format(len(courses)))
    file_urls = []
    # iterate over each course
    for course in courses[:1]:
        navpane = get_navpane_info(course)
        # iterate over each page
        for page in navpane:
            # a few pages have no (downloadable) content, skip them
            if page.name in navpane_ignore:
                print('  *SKIPPED* {0:s}'.format(page.name))
                continue
            # TODO don't reload the home page
            # TODO skip emails page - different for each school
            print('   {0:s}'.format(page.name))
            # iterate over each page in course, gathering urls
            file_urls = file_urls + gather_urls(page)
    # iterate over urls, downloading them
    print('Alright, now I can download your files.')
    for f_url in file_urls[:3]:
        print(f_url)
        # TODO hangs after opening file, ff gives "uncaught exception: 2147746132"
        driver.get(f_url.url)
        print("*** GOT FILE ***")

    print('That is all I could find! You should double check.')
    driver.quit()
# end main()


if __name__ == "__main__":
    main()
