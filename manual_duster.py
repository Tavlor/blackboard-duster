#!/usr/bin/env python3
""" ~^~
Manual Duster
    Scrapes course materials from your Blackboard courses, such as lecture
    notes and homework - but you have to do the navagating
Author: Taylor Smith, Winter 2019
Python Version: 3.7
Notes: Uses Selenium to scrape urls from Blackboard, then requests to
    download the files
TODO:
~*~ """

import requests

from os import get_terminal_size
from pathlib import Path
from selenium import webdriver

import blackboard_duster as bd


def main():
    args = bd.parse_args()
    driver = None
    if args.webdriver == 'firefox':
        driver = webdriver.Firefox()
    elif args.webdriver == 'chrome':
        driver = webdriver.Chrome()
    else:
        print('sorry, but {0:s} is not a supported WebDriver. \
            Aborting'.format(args.webdriver))
        exit()
    driver.set_window_size(1200, 700)
    driver.get(args.bb_url)
    # choose a nice size - the navpane is invisible at small widths,
    # but selenium can still see its elements
    bd.manual_login(driver)
    # requests needs access to the Blackboard login cookie
    input('Alright, now go to the page you want to scrape, return to' +
          ' the terminal, and press enter to start.')
    while True:
        file_links = bd.gather_links(driver, delay_mult=args.delay)
        print('I gathered {} urls from the browser.'.format(
            len(file_links)))
        counters = bd.download_links(driver, file_links)
        print('\n{} files downloaded. {} duplicates ignored.'.format(
            counters['downloaded'], counters['duplicate']
        ))
        input('If there is another page you want to scrape, repeat' +
              ' what you just did. Once you are all done close the browser.')

# end main()


if __name__ == "__main__":
    main()
