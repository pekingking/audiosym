from rauth.service import OAuth1Service, OAuth1Session
import argparse
import os
import re
import fnmatch
import requests
import sys
import logging
import config
import readline
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

class audiosym():
    def __init__(self):
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
        logging.debug('A debug message!')

    def findBookDetails(self, source):
        #print getSourceFileList(args.source)
        print "################################################################"
        print "\nsearching for {}".format(os.path.basename(source))
        bookIndex = 0
        bookTitle = os.path.basename(source)
        print "\nsearch term = {}".format(self.cleanTitle(bookTitle))
        while True:
            bookDetails = self.getBookInfo(bookTitle, bookIndex)
            print "Found {} by {} released on {}".format(bookDetails["title"], bookDetails["author"], bookDetails["date"])
            if bookDetails["series"] and bookDetails["seriesNumber"]:
                print "Book {} in {}".format(bookDetails["seriesNumber"], bookDetails["series"])
            print "https://www.goodreads.com/book/show/{}".format(bookDetails["goodreadsID"])
            print "Folder would look like {}{}:{}".format(self.cleanTitle(bookDetails["series"]) + "/" if bookDetails["series"] else "",self.cleanTitle(bookDetails[seriesNumber] + bookDetails["title"]), self.cleanTitle(bookDetails["author"]))
            correctBook = raw_input("would you like to continue? [yes]/no/next/search/manual/modify: ")
            if correctBook == "next":
                bookIndex += 1
            elif correctBook == "search":
                bookTitle = raw_input("what book are you looking for? ")
                bookIndex = 0
            elif correctBook == "manual":
                bookTitle = raw_input("what would you like to call the book? ")
                bookAuthor = raw_input("who wrote this book? ")
                bookID = raw_input("what is the goodreads id? ")
                bookIndex = 0
                if bookTitle and bookAuthor and bookID:
                    bookDetails = dict()
                    bookDetails["title"] = bookTitle
                    #TODO manual the rest of the stuff
                    bookDetails["author"] = bookAuthor
                    bookDetails["date"] = ""
                    bookDetails["description"] = ""
                    bookDetails["thumbnailURL"] = ""
                    bookDetails["goodreadsID"] = bookID
                    return bookDetails
                else:
                    print "no title provided or author"
                    return
            elif correctBook == "modify":
                bookTitle = self.input("title: ", bookDetails["title"])
                bookAuthor = self.input("author:  ", bookDetails["author"])
                bookID = self.input("goodreads id: ", bookDetails["goodreadsID"])
                if bookTitle and bookAuthor and bookID:
                    bookDetails = dict()
                    bookDetails["title"] = bookTitle
                    bookDetails["author"] = bookAuthor
                    bookDetails["goodreadsID"] = bookID
                    bookDetails["date"] = ""
                    bookDetails["description"] = ""
                    bookDetails["thumbnailURL"] = ""
                    return bookDetails
                else:
                    print "no title provided or author"
                    return
            elif correctBook == "yes" or correctBook == "":
                print "great lets continue"
                return bookDetails
            elif correctBook == "no":
                print "sorry we could not find your book"
                print "exiting"
                return
            else:
                print "did not recognize your command."
                print "exiting"
                return False

    def verifyCorrectOrder(self, args):
        # we have identified the book on books.google.com so we have (title, author, description, date, thumbnail)
            exit = False
            print "\nidentified the following files"
            orderedFileList = self.getSourceFileList(args.source)
            for bookFile in orderedFileList:
                print bookFile
            correctOrder = raw_input("did they print out in the correct order? [yes]/no: ")
            #if the files are not in order its going to be a pain in the ass to fix. Do you do one by one?
            #TODO manual option for sorting
            if correctOrder == "no" and not exit:
                exit = True
                print "\nidentified the following files (alternate sorting)"
                orderedFileList = self.getSourceFileList(args.source, True)
                for bookFile in orderedFileList:
                    print bookFile
                correctOrder = raw_input("did they print out in the correct order this time? [yes]/no: ")
            if correctOrder == "no" and exit:
                print "\nnot available in version 1.0 "
                print "we need to order these before we can fix this"
                return
            # the files were in order lets print out what we plan to do
            if correctOrder == "yes" or correctOrder == "":
                return orderedFileList
            return

    def actionSummary(self, args, bookDetails, scriptPath, orderedFileList, prepend=""):
        print "\n"
        print "planning on creating the following directory and symlinks:"
        print "source:      {}".format(args.source)
        print "destination: {}/{}".format(args.destination.rstrip('/'), prepend + self.cleanTitle(bookDetails["title"]) + ":" + self.cleanTitle(bookDetails["author"]))
        print ""
        print "planning on creating the following symlinks"
        print "symlink -> file"
        for index, file in enumerate(orderedFileList):
            print "{}.%03d{} -> {}".format(self.cleanTitle(bookDetails["title"]), os.path.splitext(file)[1], file) % (
                index + 1)
        print "index.php -> {}".format(scriptPath)
        proceed = raw_input("Do you want to continue? [yes]/no: ")
        if proceed == "yes" or proceed == "":
            return True
        else:
            return False

    def createSymlinks(self, args, bookDetails, scriptPath, orderedFileList, prepend=""):
        if not os.path.exists("{}/{}".format(args.destination.rstrip('/'), prepend + self.cleanTitle(bookDetails["title"]) + ":" + self.cleanTitle(bookDetails["author"]))):
            print "creating directory"
            os.mkdir("{}/{}".format(args.destination.rstrip('/'), prepend + self.cleanTitle(bookDetails["title"]) + ":" + self.cleanTitle(bookDetails["author"])))
            if os.path.exists("{}/{}".format(args.destination.rstrip('/'), prepend + self.cleanTitle(bookDetails["title"]) + ":" + self.cleanTitle(bookDetails["author"]))):
                print "directory created"
                os.chdir("{}/{}".format(args.destination.rstrip('/'), prepend + self.cleanTitle(bookDetails["title"]) + ":" + self.cleanTitle(bookDetails["author"])))
                print "creating symlinks"
                for index, file in enumerate(orderedFileList):
                    os.symlink("{}/{}".format(args.source.rstrip('/'), file), "{}/{}/{}.%03d{}".format(args.destination.rstrip('/'), prepend + self.cleanTitle(bookDetails["title"]) + ":" + self.cleanTitle(bookDetails["author"]), self.cleanTitle(bookDetails["title"]), os.path.splitext(file)[1]) % (index + 1))
                #Symlinks the index.txt to index.php in the new audiobook directory
                if os.path.exists(scriptPath):
                    os.symlink(scriptPath, "{}/{}/{}".format(args.destination.rstrip('/'), prepend + self.cleanTitle(bookDetails["title"]) + ":" + self.cleanTitle(bookDetails["author"]), "index.php"))
                print "symlinks created"
                return True
        else:
            print "the following directory already exists {}/{}".format(args.destination.rstrip('/'), prepend + self.cleanTitle(bookDetails["title"]) + ":" + self.cleanTitle(bookDetails["author"]))
            return False

    def cleanTitle(self, title):
        """clean up titles so they have no special characters and are . separated"""
        cleanTitle = re.sub("'", "", title)
        cleanTitle = re.sub(r'(?i)(audiobook|unabridged|abridged|chapterized)', "", cleanTitle)
        cleanTitle = re.sub("\([^)]+\)", "", cleanTitle)
        cleanTitle = re.sub("\[[^\]]+\]", "", cleanTitle)
        cleanTitle = re.sub("[^a-zA-Z1-9]", ".", cleanTitle)
        cleanTitle = re.sub("\.+", ".", cleanTitle)
        cleanTitle = re.sub("^\.|\.$", "", cleanTitle)
        cleanTitle = cleanTitle.lower()
        return cleanTitle

    def getSourceFileList(self, directory, sortDigits = False):
        """Returns a list of files in a directory"""
        fileList = []
        if os.path.exists(directory):
            os.chdir(directory)
            for dirname, dirnames, filenames in os.walk("./"):
                # print path to all filenames.
                for filename in filenames:
                    if fnmatch.fnmatch(os.path.join(dirname, filename).lstrip("./").lower(), "*.mp3") or fnmatch.fnmatch(os.path.join(dirname, filename).lstrip("./").lower(), "*.m4a") or fnmatch.fnmatch(os.path.join(dirname, filename).lstrip("./").lower(), "*.m4b") or fnmatch.fnmatch(os.path.join(dirname, filename).lstrip("./").lower(), "*.acc"):
                        fileList.append(os.path.join(dirname, filename).lstrip("./"))
            fileList = sorted(fileList)
            if not sortDigits:
                return fileList
            sortingList = []
            #extract and order all integers in the files name to fix the issues of 1,10,11,12,13,2,3,4,5,6,7,8,9
            for name in fileList:
                integers = re.findall("\d+", name)
                integers = map(int, integers)
                integers.append(name)
                sortingList.append(integers)
            orderedFiles = []
            for name in sorted(sortingList):
                orderedFiles.append(name[-1])
            return orderedFiles
        else:
            print "Directory does not exist: " + directory
            return

    # def getBookInfo(self, title, bookIndex=0):
    #     """pull title information from custome google search on libraryofthings and return a dictionary"""
    #     request = requests.get("https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&rsz=filtered_cse&num=1&hl=en&prettyPrint=false&cx=003480712083187615526:3bc2u714j5u&q={}&start={}".format(self.cleanTitle(title).replace(".", " "), str(bookIndex)))
    #     if request.status_code == 200 and len(request.text) > 0:
    #         info = request.json()
    #         bookDetails = dict()
    #         bookDetails["title"] = "NOT FOUND"
    #         bookDetails["author"] = "NOT FOUND"
    #         bookDetails["date"] = ""
    #         bookDetails["description"] = ""
    #         bookDetails["thumbnailURL"] = ""
    #         if "results" in info and info["results"] and "richSnippet" in info["results"][0] and "metatags" in info["results"][0]["richSnippet"] and "twitterTitle" in info["results"][0]["richSnippet"]["metatags"]:
    #             if info["results"][0]["richSnippet"]["metatags"]["twitterTitle"].find(" by "):
    #                 title, author = info["results"][0]["richSnippet"]["metatags"]["twitterTitle"].rsplit(" by ", 1)
    #                 if title:
    #                     bookDetails["title"] = title
    #                 else:
    #                     print "no title found"
    #                 if author:
    #                     bookDetails["author"] = author
    #                 else:
    #                     print "no author found"
    #                 return bookDetails
    #     print "problem finding book"
    #     return bookDetails

    def getBookInfo(self, title, bookIndex=0):
        """get goodreadsID"""
        request = requests.get("https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&num=1&hl=en&prettyPrint=true&cx=003836925080131241610:4lgjbsogluc&q={}&start={}".format(self.cleanTitle(title).replace('.', '+'), str(bookIndex)))
        if request.status_code == 200 and len(request.text) > 0:
            info = request.json()
            bookDetails = dict()
            bookDetails["title"] = "NOT FOUND"
            bookDetails["author"] = "NOT FOUND"
            bookDetails["series"] = ""
            bookDetails["seriesNumber"] = ""
            bookDetails["goodreadsID"] = "0"
            bookDetails["date"] = ""
            if "results" in info and info["results"] and "richSnippet" in info["results"][0] and "person" in info["results"][0]["richSnippet"] and "name" in info["results"][0]["richSnippet"]["person"]:
                bookDetails["author"] = info["results"][0]["richSnippet"]["person"]["name"]
            else:
                print "no author found"
            if "results" in info and info["results"] and "richSnippet" in info["results"][0] and "book" in info["results"][0]["richSnippet"] and "name" in info["results"][0]["richSnippet"]["book"]:
                bookDetails["title"] = info["results"][0]["richSnippet"]["book"]["name"]
                series = re.search("\(([^(]+)\s+#([^#(]+)\)$", bookDetails["title"])
                if series:
                    bookDetails["series"] = series.group(1)
                    bookDetails["seriesNumber"] = series.group(2)
            else:
                print "no title found"
            if "results" in info and info["results"] and "content" in info["results"][0]:
                date = re.findall("^(\w+\s+\d+,\s+\d+)", info["results"][0]["content"])
                if date:
                    bookDetails["date"] = date[0]
            bookid = re.search("(?:https?://www.goodreads.com/book/show/(\d+))",request.text)
            if bookid:
                bookDetails["goodreadsID"] = bookid.group(1)
            else:
                print "no bookid found"
            return bookDetails
        print "problem finding book"
        return bookDetails


    def addToGoodreads(self, id):
        # Get a real consumer key & secret from: http://www.goodreads.com/api/keys
        new_session = OAuth1Session(
            consumer_key=config.CONSUMER_KEY,
            consumer_secret=config.CONSUMER_SECRET,
            access_token=config.ACCESS_TOKEN,
            access_token_secret=config.ACCESS_TOKEN_SECRET,
        )
        data = {'name': 'to-read', 'book_id': int(id)}
        response = new_session.post('http://www.goodreads.com/shelf/add_to_shelf.xml', data)
        if response.status_code != 201:
            print "could not add id to bookshelf: " + id + "    status code:" + str(response.status_code)
        else:
            print 'Book added to goodreads bookshelf: ' + id

    # def getBookInfo(self, title, bookIndex=0):
    #     """pull book information from books.google.com api and return a dictionary"""
    #     request = requests.get("https://www.googleapis.com/books/v1/volumes?&printType=books&q={}&startIndex={}".format(self.cleanTitle(title).replace(".", " "), str(bookIndex)))
    #     if request.status_code == 200 and len(request.text) > 0:
    #         books = request.json()
    #         bookDetails = dict()
    #         if "items" in books and "volumeInfo" in books["items"][0]:
    #             #print books["items"][0]["volumeInfo"]
    #             if "title" in books["items"][0]["volumeInfo"]:
    #                 bookDetails["title"] = books["items"][0]["volumeInfo"]["title"]
    #             else:
    #                 print "no title found"
    #                 bookDetails["title"] = "NOT FOUND"
    #             if "authors" in books["items"][0]["volumeInfo"]:
    #                 bookDetails["author"] = books["items"][0]["volumeInfo"]["authors"][0]
    #             else:
    #                 print "no title found"
    #                 bookDetails["author"] = "NOT FOUND"
    #             if "publishedDate" in books["items"][0]["volumeInfo"]:
    #                 bookDetails["date"] = books["items"][0]["volumeInfo"]["publishedDate"]
    #             else:
    #                 bookDetails["date"] = ""
    #             if "description" in books["items"][0]["volumeInfo"]:
    #                 bookDetails["description"] = books["items"][0]["volumeInfo"]["description"]
    #             else:
    #                 bookDetails["description"] = ""
    #             if "imageLinks" in books["items"][0]["volumeInfo"] and "thumbnail" in books["items"][0]["volumeInfo"]["imageLinks"]:
    #                 bookDetails["thumbnailURL"] = books["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]
    #             else:
    #                 bookDetails["thumbnailURL"] = ""
    #             #print "title: {}".format(bookDetails["title"])
    #             #print "author: {}".format(bookDetails["author"])
    #             #print "date: {}".format(bookDetails["date"])
    #             #print "description: {}".format(unicode(bookDetails["description"], "utf8"))
    #             #print "thumbnail: {}".format(bookDetails["thumbnailURL"])
    #             return bookDetails
    #     print "Google API search came back empty"
    #     bookDetails = dict()
    #     bookDetails["title"] = "NOT FOUND"
    #     bookDetails["author"] = "NOT FOUND"
    #     bookDetails["date"] = ""
    #     bookDetails["description"] = ""
    #     bookDetails["thumbnailURL"] = ""
    #     return bookDetails

    def findBookImageURL(self, title, series=False):
        if series:
            logging.debug("extrating number from title: {}".format(title))
            title = re.sub("^\d+\.", "", title)
        if title == '':
            logging.error("Book title is blank")
            return
        return "https://hdbookcover.appspot.com/{}".format(re.sub('[^\w\.]+', '+', title))
        #response = requests.get("http://bigbooksearch.com/query.php?SearchIndex=books&Keywords={}&ItemPage=1".format(title))
        #if response.status_code == 200:
        #    imageUrlArray = re.findall("<a href='[^']+'><img id='[^']+' src='([^']+)'", response.text)
        #    if imageUrlArray:
        #        return imageUrlArray[0]
        #logging.error("Could not find image for {}".format(title))
        #return

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

    def input(self, prompt, prefill=''):
       readline.set_startup_hook(lambda: readline.insert_text(prefill))
       try:
          return raw_input(prompt)
       finally:
          readline.set_startup_hook()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", help="base directory to attach symlinks to")
    parser.add_argument("-d", "--destination", help="base directory /path/to/books/")
    parser.add_argument("-p", "--prepend", default="", help="prepend a string to the folder name (use for series)")
    args = parser.parse_args()
    scriptPath = "{}/{}".format(os.path.dirname(os.path.realpath(__file__)), 'index.txt')
    if not os.path.exists(args.source):
        print "{} is not a valid directory".format(args.source)
        sys.exit()
    if not os.path.exists(args.destination):
        print "{} is not a valid directory".format(args.destination)
        sys.exit()

    audiosymlink = audiosym()

    # Identify audiobook and gather book details from books.google.com api.
    bookDetails = audiosymlink.findBookDetails(args.source.rstrip('/'))
    if not bookDetails:
        sys.exit()
    # Verify that the files are in the correct order.
    # If they are not then the audiobook will be all out of order when we symlink
    orderedFileList = audiosymlink.verifyCorrectOrder(args)
    if not orderedFileList:
        sys.exit()
    # Show the user a list of the symlinks that are about to be created
    proceed = audiosymlink.actionSummary(args, bookDetails, scriptPath, orderedFileList, args.prepend)
    if not proceed:
        sys.exit()
    # Create the symlinks
    symlinkCreate = audiosymlink.createSymlinks(args, bookDetails, scriptPath, orderedFileList, args.prepend)
    if not symlinkCreate:
        sys.exit()
    #make sure we are not overwriting something
    folder = '{}:{}'.format(audiosymlink.cleanTitle(bookDetails["title"]), audiosymlink.cleanTitle(bookDetails["author"]))
    url = audiosymlink.findBookImageURL(folder)
    if not url:
        logging.error("could not find url")
    else:
        audiosymlink.saveImage(url, "{}/{}".format(args.destination.rstrip('/'), folder), 'folder.jpg')

if __name__ == '__main__':
    main()
