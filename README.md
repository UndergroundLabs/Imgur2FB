# Imgur2FB

Imgur2FB downloads a random image from imgur.com and uploads the image to your Facebook page.

The script will also pick a top comment from the Imgur image page, and post the comment as the status message for the image when uploading to Facebook.

## Usage

    imgur2fb.py joe@bloggs.com secretpassword https://facebook.com/joebloggspage http://imgur.com/search?q=funny

## Help

    imgur2fb.py -h

    usage: imgur2fb.py [-h] username password pageURL imgurURL

    Facebook Power Suite

    positional arguments:
      username    Facebook username
      password    Facebook password
      pageURL     Facebook page URL. Format: https://www.facebook.com/weedhumor
      imgurURL    Imgur URL. Format: http://imgur.com/search?q=funny

    optional arguments:
      -h, --help  show this help message and exit

