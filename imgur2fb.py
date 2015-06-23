#!/usr/bin/env python

import argparse
import datetime
import json
import logging
import re
import random
import requests
import shutil
from pyquery import PyQuery as pq


def main(username, password, page, imgurURL):

    logging.basicConfig(filename='imgur2fb.log', level=logging.DEBUG)

    session = requests.session()

    TerminalLog('Downloading a random image from Imgur')
    image, comment = getRandomImageFromImgur(imgurURL)

    TerminalLog('Logging into Facebook')
    uid, dtsg = login(session, username, password)

    TerminalLog('Switching to page: %s' % page)
    pageID = switchToPage(session, dtsg, uid, page)

    TerminalLog('Uploading image to Facebook')
    imageID = uploadImageToFacebook(session, pageID, dtsg, 100, 100, image)

    TerminalLog('Posting image to page')
    postImageToPage(session, dtsg, pageID, imageID, comment)

    TerminalLog('Done :)')

def TerminalLog(message):

    print '[%s] %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), message)

def login(session, username, password):

    '''
    Login to Facebook
    '''

    # Navigate to the Facebook homepage
    response = session.get('https://facebook.com')

    # Construct the DOM
    dom = pq(response.text)

    # Get the lsd value from the HTML. This is required to make the login request
    lsd = dom('[name="lsd"]').val()

    # Perform the login request
    response = session.post('https://www.facebook.com/login.php?login_attempt=1', data={
        'lsd': lsd,
        'email': username,
        'pass': password,
        'default_persistent': '0',
        'timezone': '-60',
        'lgndim': '',
        'lgnrnd': '',
        'lgnjs': '',
        'locale':'en_GB',
        'qsstamp': ''
    })

    '''
    Get the users ID and fb_dtsg token. The fb_dtsg token is required when making requests as a logged in user. It
    never changes, so we only need to grab this token once.

    If the login was successful a cookie 'c_user' is set by Facebook. If the login failed, the 'c_user' cookie
    will not be present. This will raise an exception.
    '''
    try:
        uid = session.cookies['c_user']
        dtsg = re.search('dtsg" value="([0-9a-zA-Z-_]+)"', response.text).group(1)
    except KeyError:
        raise Exception('Login Failed!')

    return uid, dtsg

def getPageID(session, page):

    '''
    Return the numeric ID of a page
    '''

    resp = session.get(page)
    pageID = re.search('pageID":([0-9]+)', resp.text)

    if not pageID:
        raise Exception('Page ID not found for page: %s' % page)

    return pageID.group(1)

def switchToPage(session, dtsg, uid, page):

    '''
    Switch to a Facebook page
    '''

    pageID = getPageID(session, page)

    response = session.post('https://www.facebook.com/identity_switch.php', allow_redirects=False, data={
        'user_id': pageID,
        'url': page,
        'nctr[_mod]': 'pagelet_bluebar',
        '__user': uid,
        '__a': 1,
        '__dyn': '',
        '__req': 'b',
        'fb_dtsg': dtsg,
        'ttstamp': '',
        '__rev': ''
    })

    if pageID not in response.cookies['i_user']:
        raise Exception('Failed to switch to page!')

    return pageID

def uploadImageToFacebook(session, pageID, dtsg, imageWidth, imageHeight, image):

    '''
    Uploads a JPG image to Facebook
    '''

    params = {
        'target_id': pageID,
        'image_height': imageHeight,
        'image_width': imageWidth,
        'letterbox': 0,
        'av': pageID,
        'qn': '990',
        '__user': pageID,
        '__a': 1,
        '__dyn': '',
        '__req': '',
        'fb_dtsg': dtsg,
        'ttstamp': '',
        '__rev': ''
    }

    data = {
        'fb_dtsg': dtsg,
        'source': 8,
        'profile_id': pageID,
        'grid_id': 'u_n_3',
        'qn': '',
        'upload_id': '990'
    }

    image = 'images/%s.jpg' % image

    response = session.post('https://upload.facebook.com/ajax/composerx/attachment/media/saveunpublished',
                            files={
                                'farr': (image, open(image, 'rb'),
                                         'image/jpg')
                            },
                            params=params,
                            data=data)

    j = json.loads(response.text[9:])

    return j['jsmods']['instances'][0][2][2]['fbid']

def postImageToPage(session, dtsg, pageID, imageID, message):

    '''
    Posts image to Facebook page

    dtsg:    fb_dtsg token
    pageID:  ID of facebook page
    imageID: ID of image uploaded to Facebook (use uploadImageToFacebook())
    message: Status message
    '''

    params = {
        'av': pageID,
        '__user': pageID,
        '__a': '1',
        '__dyn': '',
        '__req': '',
        'fb_dtsg': dtsg,
        'ttstamp': '',
        '__rev': ''
    }

    data = {
        'composer_session_id': '',
        'fb_dtsg': dtsg,
        'xhpc_content': 'profile',
        'xhpc_ismeta': '1',
        'xhpc_timeline': '',
        'xhpc_composerid': '',
        'xhpc_finch': '1',
        'xhpc_targetid': pageID,
        'xhpc_publish_type': 1,
        'clp': '',
        'xhpc_message_text': message,
        'xhpc_message': message,
        'composer_unpublished_photo[]': imageID,
        'composer_has_crop[' + imageID + ']': '',
        'composer_has_filter[' + imageID + ']': '',
        'album_type': 128,
        'is_file_form': 1,
        'oid': '',
        'qn': '',
        'application': 'composer',
        'is_explicit_place': '',
        'composertags_place': '',
        'composertags_place_name': '',
        'tagger_session_id': '',
        'action_type_id[]': '',
        'object_str[]': '',
        'object_id[]': '',
        'hide_object_attachment': 0,
        'og_suggestion_mechanism': '',
        'og_suggestion_logging_data': '',
        'icon_id': '',
        'composertags_city': '',
        'disable_location_sharing': False,
        'composer_predicted_city': '',
        'future_date': '',
        'future_time': '',
        'scheduled': '',
        'draft': '',
        'backdated_date[year]': '',
        'backdated_date[month]': '',
        'backdated_date[day]': '',
        'hide_from_newsfeed': '',
    }

    response = session.post('https://upload.facebook.com/media/upload/photos/composer/',
                            params=params,
                            data=data,
                            headers = {'content-type': 'multipart/form-data'})

    j = json.loads(response.text[9:])

    return j['payload']['photo_fbid']

def getRandomImageFromImgur(url):

    '''
    Fetch a random image from Imgur
    '''

    response = requests.get(url)

    dom = pq(response.text)
    image = random.choice(dom('.image-list-link'))
    image = pq(image).attr('href').split('/')[2]

    response = requests.get('http://i.imgur.com/%s.jpg' % image, stream=True)

    with open('images/%s.jpg' % image, 'wb') as f:
        shutil.copyfileobj(response.raw, f)

    # Get the top comment from the Imgur page
    response = requests.get('http://imgur.com/gallery/%s/comment/best/hit.json' % image)

    j = json.loads(response.text)

    for caption in reversed(j['data']['captions']):

        # Skip the comment if comment contains a URL.
        if any(s in caption['caption'] for s in ['http', 'www']):
            continue

        comment = caption['caption']
        break

    if not comment:
        comment = ''

    return image, comment

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Imgur2FB')
    parser.add_argument('username', help='Facebook username')
    parser.add_argument('password', help='Facebook password')
    parser.add_argument('pageURL', help='Facebook page URL. Format: https://www.facebook.com/weedhumor')
    parser.add_argument('imgurURL', help='Imgur URL. Format: http://imgur.com/search?q=funny')

    args = parser.parse_args()

    print 'Imgur2FB - Automated Facebook Page Building'
    print 'Developer: James Jeffery <jameslovescode@gmail.com>'

    try:
        main(args.username, args.password, args.pageURL, args.imgurURL)
    except Exception, e:
        logging.exception(e)
        print e