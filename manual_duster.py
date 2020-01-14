#!/usr/bin/env python3
""" ~^~
Manual Duster
    Scrapes course materials from your Blackboard courses, such as lecture
    notes and homework - but you have to do the navagating
Author: Taylor Smith, Winter 2019
Python Version: 3.7
Notes: Uses Selenium to scrape urls from Blackboard, then urllib to
    download the files
TODO:
~*~ """

from urllib import request

from selenium import webdriver

from mime_types import MIME_TYPES
import blackboard_duster as bd


def main():
    args = bd.parse_args()
    driver = None
    if args.webdriver == 'firefox':
        driver = webdriver.Firefox(firefox_profile=bd.get_ff_profile(args))
    elif args.webdriver == 'chrome':
        driver = webdriver.Chrome(options=bd.get_ch_options(args))
    else:
        print('sorry, but {0:s} is not a supported WebDriver. \
            Aborting'.format(args.webdriver))
        exit()
    driver.get(args.bb_url)
    # choose a nice size - the navpane is invisible at small widths,
    # but selenium can still see its elements
    driver.set_window_size(1200, 700)
    bd.manual_login(driver)
    # urllib needs access to the Blackboard login cookie
opener.addheaders.append(('Cookie', 'cookiename=cookievalue'))
    input('Alright, now go to the page you want to scrape, return to' +
          ' the terminal, and press enter to start.')
    while True:
        links = bd.gather_links(driver, delay_mult=args.delay)
        for link in links[:1]:
            # link.element.click()
            # driver.get(link.url)
            pass
        input('If there is another page you want to scrape, repeat' +
              ' what you just did. Once you are all done close the browser.')

# end main()


if __name__ == "__main__":
    main()
