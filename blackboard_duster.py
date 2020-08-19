#!/usr/bin/env python3
"""
Copyright (C) 2020  Taylor Smith

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see https://www.gnu.org/licenses/


 ~^~
Blackboard Duster
    Scrapes course materials from your Blackboard courses, such as
    lecture notes and homework
Author: Taylor Smith, Winter 2019
Python Version: 3.7
Notes: Uses Selenium to scrape urls from Blackboard, then urllib to
    download files
TODO:
    - avoid redundant visit to course home page (just ignore it?)
    - dump notes from items/assignments into a .txt : use div.details
    - don't abort if navpane is missing, reload or skip
    - put a 'download progress' label on progress bar
    - use etag instead of last-modified date (note - etag may not always be available)
~*~ """

import argparse
import json
import requests

from enum import Enum
from datetime import datetime
from os import get_terminal_size
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import unquote

# Last Modified value in the header has a timezone. Once it is
# converted to a datetime object, the timezone info is lost
lastmod_parse_fmt = '%a, %d %b %Y %H:%M:%S %Z'
lastmod_save_fmt = '%a, %d %b %Y %H:%M:%S'


class Link:
    """contains useful information about a link

    'url': url found on page, will (probably) get redirected
    'name': friendly name of link
    'save_path': relative to download path, usually the page's name
    'element': the selenium Element that the url came from
    'lastmod': last modified date
    'full_path': full save path, used for troubleshooting
    """

    def __init__(self, url, name='', save_path=None, element=None):
        self.url = url
        self.name = name
        self.save_path = save_path
        self.element = element
        self.lastmod = None
        self.full_path = None

    def __repr__(self):
        return f'{self.url}\n\t{self.name}\n\t{self.save_path}'

    def set_lastmod(self, datestr):
        self.lastmod = datetime.strptime(
            datestr.strip(), lastmod_parse_fmt)

    def json(self):
        result = {
            'url': self.url,
            'name': self.name,
            'save_path': self.save_path.as_posix(),
            'lastmod': self.lastmod.strftime(lastmod_save_fmt)
        }
        return result


class DLResult(Enum):
    """represents various download results"""
    COLLISION = 0
    DOWNLOADED = 1
    DUPLICATE = 2
    UPDATED = 3


def apply_style(driver, element, res_code):
    style = 'border: '
    if res_code == DLResult.COLLISION:
        style += '4px dotted red'
    elif res_code == DLResult.DOWNLOADED:
        style += '4px solid green'
    elif res_code == DLResult.DUPLICATE:
        style += '4px dashed cyan'
    elif res_code == DLResult.UPDATED:
        style += '4px solid blue'
    else:  # PENDING DOWNLOAD
        style += '1px dotted magenta'
    driver.execute_script(
        'arguments[0].setAttribute("style", arguments[1]);',
        element, style)


def parse_args():
    navpane_ignore = {'Announcements', 'Calendar',
                    'My Grades', 'Blackboard Collaborate'}
    parser = argparse.ArgumentParser(
        description='Scrapes files from Blackboard courses')
    parser.add_argument(
        'bb_url', metavar='BB_base_URL',
        help='URL for your Blackboard instance.')
    parser.add_argument(
        '-s', '--save', metavar='path', default='.',
        help='directory to save your downloads in')
    parser.add_argument(
        '--historypath', '--history', metavar='json',
        default='BlackboardDuster.json',
        help='path to blackboard duster history file. Relative to' +
        ' download directory unless path is absolute. The file' +
        ' will be created if it does not exit.')
    parser.add_argument(
        '--delay', metavar='delay_mult', type=int, default=1,
        help='multiplier for sleep/delays')
    parser.add_argument(
        '-w', '--webdriver', '--wd', metavar='name', default='firefox',
        help='browser WebDriver to use - either "firefox" or' +
        ' "chrome". You must have the WebDriver in your system' +
        ' path. Currently, only firefox is supported; that' +
        ' will change in the future')
    parser.add_argument(
        '-a', '--auto', action='store_true',
        help='disable user input. The script will continue after' +
        ' parsing a page')
    parser.add_argument(
        '-b', '--binary', metavar='file', default=None,
        help='Path to the binary you want to use - use if your' +
        ' browser binary is not in the default location')
    parser.add_argument(
        '-i', '--ignore', metavar='name', action='append',
        help=f'Name of a page in the navpane to ignore; repeat this argument' +
        f' to ignore multiple pages. Defaults are {navpane_ignore}')
    args = parser.parse_args()
    # convert given path string into a Path object
    args.save = Path(args.save)
    # if history path isn't absolute, make it relative to save
    args.historypath = Path(args.historypath)
    if not args.historypath.is_absolute():
        args.historypath = args.save / args.historypath
    # sterilize webdriver name
    args.webdriver = args.webdriver.lower().strip()
    # combine args.ignore with navpane_ignore
    if args.ignore:
        navpane_ignore.update(args.ignore)
    args.ignore = navpane_ignore
    # inform user about auto mode
    print(f'running in {"auto" if args.auto else "manual"} mode')
    return args
# end parse_args()


def setup_history(path):
    # set up the download history JSON object
    history = None
    try:
        with path.open('r') as file:
            history = json.load(file)
    except json.decoder.JSONDecodeError:
        print('current history file will not parse, aborting')
        exit()
    except IOError:
        print('history file not found, creating new history')
        history = json.loads('{"links":[]}')
    return history


def setup_session(driver):
    """copies login cookies from WebDriver into a requests session"""
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])
    return session


def manual_login(driver):
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


def accept_cookies(driver, delay_mult):
    """if the cookie notice appears, click 'accept'"""
    try:
        element = WebDriverWait(driver, delay_mult * 4).until(
            EC.presence_of_element_located((By.ID, 'agree_button'))
        )
        print('I am accepting the cookie notice, I hope that is ok!')
        element.click()
    except TimeoutException:
        print('I did not see a cookie notice.')


def get_courses_info(driver, delay_mult, save_root):
    """returns an array of link objects for each course

    driver: a selenium WebDriver
    delay_mult: delay multiplier
    save_root: base directory for downloads
    expects homepage to already be loaded
    """
    result = []
    # TODO course announcements are included in the list
    try:
        # wait for the course list to load
        course_links = WebDriverWait(driver, delay_mult * 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div#div_25_1 a')
            )
        )
    except TimeoutException:
        print('I did not see your course list! Aborting')
        driver.quit()
        exit()
    # be more specific when selecting the links - the wait statement's
    # selector includes announcement links, which we don't want
    course_links = driver.find_elements_by_css_selector(
        'div#div_25_1 > div > ul > li > a')
    for c_l in course_links:
        link = Link(
            c_l.get_attribute('href'),
            c_l.text,
            (save_root / c_l.text)
        )
        result.append(link)
    return result


def get_navpane_info(driver, course_link, delay_mult):
    """returns an array of Links for items in the navpane

    driver: a selenium WebDriver
    course_link: Link object representing the course homepage - this
        link will be loaded
    delay_mult: delay multiplier
    returns a Link array
    """
    driver.get(course_link.url)
    try:
        WebDriverWait(driver, delay_mult * 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'ul#courseMenuPalette_contents')
            )
        )
    except TimeoutException:
        print('I could not access the navpane! skipping')
        return []
    page_link_elements = driver.find_elements_by_css_selector(
        'ul#courseMenuPalette_contents a')
    result = []
    for element in page_link_elements:
        title = element.find_element_by_css_selector(
            'span').get_attribute('title')
        link = Link(
            element.get_attribute('href'),
            title,
            (course_link.save_path / title)
        )
        result.append(link)
    return result


def gather_links(page_link, driver, delay_mult=1):
    """gathers and highlights available file urls on the given page

    page should already be loaded

    driver: a selenium WebDriver
    page_link: Link object
    delay_mult: delay multiplier

    returns a dictionary:
        links: a list of Link objects
        folders: a list of sub-folders on the page
    """
    results = {
        'links': [],
        'folders': []
    }
    try:
        WebDriverWait(driver, delay_mult * 3).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                'ul#content_listContainer'))
        )
    except TimeoutException:
        print('This page does not have a content list.')
        return results
    # get a list of all items in the content list
    page_content = driver.find_elements_by_css_selector(
        'ul#content_listContainer > li')
    for item in page_content:
        i_type = item.find_element_by_css_selector(
            'img').get_attribute('alt')
        # in the header holding the name there is a hidden <span> that
        # gets in the way; ignore it by looking for the style attribute
        i_name = item.find_element_by_css_selector('span[style]').text
        # print(f'    {i_type}: {i_name}'
        if i_type == 'File':
            # files are just a link
            link_element = item.find_element_by_css_selector(
                'a')
            link = Link(
                link_element.get_attribute('href'),
                i_name,
                page_link.save_path,
                link_element
            )
            apply_style(driver, link.element, None)
            results['links'].append(link)
        elif i_type == 'Content Folder':
            # folders contain another page
            # no need to track its element
            link = Link(
                item.find_element_by_css_selector(
                    'a').get_attribute('href'),
                i_name,
                (page_link.save_path / i_name)
            )
            results['folders'].append(link)
        elif i_type == 'Web Link':
            # TODO dump links into a per-page file (markdown?)
            # TODO ignore webpages but download files
            pass
        elif i_type == 'Item':
            # TODO dump info into a per-page file (markdown?)
            pass
        else:
            # FIXME this is really ugly
            print(f'    ** {i_type} is not a supported item',
                  ' type - attachments will still be collected **')

        # find attachments; Items and Assignments usually have some
        i_files = item.find_elements_by_css_selector(
            'ul.attachments > li')
        # if there are multiple attachments on the item, stick them in
        # a new folder
        save_path = page_link.save_path
        if len(i_files) > 1:
            save_path = save_path / i_name
        for file in i_files:
            link_element = file.find_element_by_css_selector('a')
            link = Link(
                link_element.get_attribute('href'),
                file.find_element_by_css_selector('a').text.strip(),
                save_path,
                link_element
            )
            # print(f'     - {link.name}')
            apply_style(driver, link.element, None)
            results['links'].append(link)
    return results


def dowload_file(session, link, history):
    """uses requests to download a file"""
    # set up download result code
    res_code = DLResult.DOWNLOADED
    # get the link's last modified date
    response = session.head(link.url, allow_redirects=True)
    link.set_lastmod(response.headers['last-modified'])
    # look for link in history
    dupe = None
    for hist_link in history['links']:
        if link.url == hist_link['url']:
            dupe = hist_link
            continue
    # compare link's last modified date to historical date
    if dupe is not None:
        hist_lastmod = datetime.strptime(
            dupe['lastmod'].strip(), lastmod_save_fmt)
        if link.lastmod <= hist_lastmod:
            return DLResult.DUPLICATE
        else:
            res_code = DLResult.UPDATED
    # download the file
    result = session.get(link.url)
    # setup the file's full path and create any needed directories
    link.save_path.mkdir(parents=True, exist_ok=True)
    file_name = unquote(result.url.rsplit('/', 1)[1])
    file_path = link.save_path / file_name
    try:
        with file_path.open('xb') as file:
            file.write(result.content)
        # FIXME updated files still trigger exception
    except:
        # hang onto the full path to report it later
        link.full_path = file_path
        res_code = DLResult.COLLISION
        # TODO hash the two files to see if they are the same
        # FIXME collided files are still added to history, collision is forgotten
    # add link to history or update lastmod
    if dupe is None:
        history['links'].append(link.json())
    else:
        dupe['lastmod'] = link.lastmod.strftime(lastmod_parse_fmt)
    return res_code


def download_links(links, driver, session, history):
    """uses requests to download files, shows a progress bar

    driver: a WebDriver object
    links: a list of Link objects
    history: a JSON object with prevoius download history
    returns a list of counters
    """
    # set up download tracking variables
    counters = [0]*len(DLResult)
    # watch for collisions
    collided = []
    # set progress bar length
    prog_len = get_terminal_size().columns-2
    for count, link in enumerate(links):
        res_code = dowload_file(session, link, history)
        counters[res_code.value] += 1
        # mark link to indicate download result to user
        apply_style(driver, link.element, res_code)
        # if it's a collision, hang onto the link
        if res_code == DLResult.COLLISION:
            collided.append(link)
        # draw progress bar
        progress = (count + 1) * int(prog_len / len(links))
        print('|{}{}|'.format('#'*progress, '-'*(prog_len-progress)),
              end='\r')
    # erase progress bar using a ansi escape code
    # \033[K' clears the row
    print('\033[K', end='\r')
    # TODO let user know how many items downloaded ect
    # let user know what collided
    if len(collided) > 0:
        print('Some of the files on this page could not download',
              'beacuse another file was in the way:')
        for link in collided:
            print(f'  ~ "{link.full_path}"')
        print('The associated links are marked with a dotted red',
              'outline if you need to manually download these files.')
    return counters


def process_page(page_link, driver, session, history, args):
    """gathers urls and downloads file from a page, handles folders

    page_link: link object
    driver: a selenium WebDriver
    session: a requests Session, with blackboard cookies
    history: the JSON download history
    args: the parsed arguments object

    returns a list of counters, indexed by DLResult values
    """
    print(f'  {page_link.name}')
    driver.get(page_link.url)
    gather_results = gather_links(page_link, driver, args.delay)
    counters = download_links(
        gather_results['links'], driver, session, history)
    # save history after every page
    try:
        with args.historypath.open('w') as file:
            json.dump(history, file, indent=4)
    except IOError:
        print('failed to save download history! You may want to',
              'investigate before continuing to the next page.')
    if not args.auto:
        # wait for user input
        input('Press enter here once you are ready to move on: ')
        # erase prompt using ansi escape codes since a newline was printed
        # '\033[A' moves cursor up once, '\033[K' clears the row
        print('\033[A\033[K', end='\r')
    for folder_link in gather_results['folders']:
        sub_counters = process_page(
            folder_link, driver, session, history, args)
        for i, s_ctr in enumerate(sub_counters):
            counters[i] += s_ctr
    return counters


def main():
    args = parse_args()
    history = setup_history(args.historypath)
    # set up the WebDriver
    driver = None
    if args.webdriver == 'firefox':
        # driver = webdriver.Firefox(firefox_profile=get_ff_profile(args))
        driver = webdriver.Firefox()
    elif args.webdriver == 'chrome':
        # driver = webdriver.Chrome(options=get_ch_options(args))
        driver = webdriver.Chrome()
    else:
        print(
            f'sorry, but {args.webdriver} is not a supported WebDriver. Aborting')
        exit()

    print("here we go!")
    # choose a nice size - the navpane is invisible at small widths,
    # but selenium can still see its elements
    driver.set_window_size(1200, 700)
    driver.get(args.bb_url)
    manual_login(driver)
    session = setup_session(driver)
    print('Alright, I can drive from here.')
    # links are visible behind the cookie notice, but it gets annoying
    # plus, there might be legal implications - so accept and move on
    accept_cookies(driver, args.delay)
    courses = get_courses_info(driver, args.delay, args.save)
    print(f'I found {len(courses)} courses. I will go through each one now!')
    counters = [0]*len(DLResult)
    for course in courses:
        print(f'{course.name}')
        navpane = get_navpane_info(driver, course, args.delay)
        for page in navpane:
            # a few pages have no (downloadable) content, skip them
            if page.name in args.ignore:
                print(f'  *SKIPPED* {page.name}')
                continue
            page_counters = process_page(
                page, driver, session, history, args)
            for i, p_ctr in enumerate(page_counters):
                counters[i] += p_ctr
    print('#'*get_terminal_size().columns)
    print('I am all done! Here are the stats:')
    for res_code in DLResult:
        print(f'  {res_code.name}: {counters[res_code.value]}')
    driver.quit()
# end main()


if __name__ == "__main__":
    main()
