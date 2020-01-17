# Blackboard Duster
A scraper script for Blackboard, built with python, selenium and the requests library. Pulls files uploaded into classes.

## Requirements
- Python 3
- [Selenium](https://selenium.dev/selenium/docs/api/py/index.html) for python

  `pip install selenium`
- The [requests library](https://2.python-requests.org/en/master/)

  `pip install requests`
- The WebDriver for your browser - make sure its version matches your browser version!
   - [Firefox WebDriver](https://github.com/mozilla/geckodriver)

      macOS users with homebrew can use `brew install geckodriver`
   - [Chrome WebDriver](https://sites.google.com/a/chromium.org/chromedriver/)

      macOS users with homebrew can use `brew cask install chromedriver`


# Usage
If you are using __Firefox__, the easiest way to get started is with
```bash
python blackboard-duster.py "www.myschool.edu/blackboard"
```
where `www.myschool.edu/blackboard` is the URL for your school's Blackboard instance. Firefox will launch and load the page. The script will wait for you to reach the homepage.

To use __Google Chrome__, use the `-w chrome` option:
```bash
python blackboard-duster.py "www.myschool.edu/blackboard" -w chrome
```

To use a __Chromium-based__ browser, use both `-w chrome` and `-b` with the path to your browser's executable:
```bash
python blackboard-duster.py "www.myschool.edu/blackboard" -w chrome -b "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
```
No other browsers are currently supported.

## How it works
When it first runs, the script waits for the Blackboard home page to appear, so you can sign in or even navagate to Blackboard if needed.
This script works in 2 phases:
1. It gathers URLs from your courses, visiting pages using the navpane on the side.
0. It visits each URL to trigger a download. By default downloads are saved in your working directory, but the `-s <DIRECTORY PATH>` option lets you change that.
    ```bash
    python blackboard-duster.py "www.myschool.edu/blackboard" -s "/Users/me/school"
    ```
    The path is evaluated using `os.path.abspath`, so it can be absolute or relative to your working directory.

# Troubleshooting
### "The script does not wait long enough for the pages to load!"
Use the `--delay <#>` option, which sets a delay multiplier. The example below will give pages twice as long as normal for pages to load.
```bash
python blackboard-duster.py "www.myschool.edu/blackboard" --delay 2
```

### "The cookie notice never goes away!"
This actually isn't a problem, just an irritation. Because the script uses URLs to navagate, it never needs to click on anything (except the cookie notice). The entire page is accessible to Selenium even if it can't _click_ on anything.

### "The script says there are no courses, but I can see them on the home page!"
Your course list might be using a different css tag, and you will need to change the [css selector](https://saucelabs.com/resources/articles/selenium-tips-css-selectors) in the code. The `get_courses_info()` function looks for the course list; replace every instance of `div#div_25_1` (there are 2) with your list's selector. Both [Firefox](https://developer.mozilla.org/en-US/docs/Tools/Page_Inspector) and [Chrome](https://developers.google.com/web/tools/chrome-devtools/) have built in page inspectors. Highlight __this__ element:
![course list](art/locate_homepage_courselist.png)

### "The script can't find the navpane!"
This is similar to the course list problem. The `get_navpane_info()` function handles the navpane; replace every instance of `ul#courseMenuPalette_contents` (there are 2) with your navpane's selector. Highlight __this__ element; you may need to make the page wider to see it:
![navpane](art/locate_navpane.png)
