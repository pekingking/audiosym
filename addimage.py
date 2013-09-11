import requests
import re
import logging
import sys
import os
import argparse


class getBook():
    def __init__(self):
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
        logging.debug('A debug message!')

    def findBookImageURL(self, title, series=False):
        if series:
            title = re.sub("^[0-9]+\.", "", title)
        response = requests.get("http://bigbooksearch.com/query.php?SearchIndex=books&Keywords={}&ItemPage=1".format(title))
        if response.status_code == 200:
            imageUrlArray = re.findall("<a href='[^']+'><img id='[^']+' src='([^']+)'", response.text)
            if imageUrlArray:
                return imageUrlArray[0]
        logging.error("Could not find image for {}".format(title))
        return

    def saveImage(self, url, path, name):
        if os.path.exists("{}".format(path)):
            if not os.path.exists("{}/{}".format(path.rstrip('/'), name)):
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    with open("{}/{}".format(path.rstrip('/'), name), 'wb') as image:
                        for chunk in response.iter_content():
                            image.write(chunk)
                    return True
                logging.error("Request to {} did not return content".format(path))
                return False
            logging.error("File already exists: {}/{}".format(path.rstrip('/'), name))
            return False
        logging.error("the path provided does not exist: {}".format(path))
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--destination", help="base directory to attach symlinks to")
    parser.add_argument("-s", "--series", help="is this directory part of a series 01.title, 02.title, 03.title")
    args = parser.parse_args()
    if args.destination and not os.path.exists(args.destination):
        logging.error("{} is not a valid directory".format(args.destination))
        sys.exit()
    print args.destination
    saveBook = getBook()
    if args.series:
        url = saveBook.findBookImageURL(os.path.basename(args.destination), True)
    else:
        url = saveBook.findBookImageURL(os.path.basename(args.destination))
    if not url:
        logging.error("could not find url")
    saveBook.saveImage(url, args.destination, 'folder.jpg')
if __name__ == "__main__":
    main()
