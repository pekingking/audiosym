import argparse
import os
import re
import fnmatch
import requests
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", help="base directory to attach symlinks to")
    parser.add_argument("-d", "--destination", help="base directory /path/to/books/")
    args = parser.parse_args()
    scriptPath = "{}/{}".format(os.path.dirname(os.path.realpath(__file__)), 'index.txt')
    if not os.path.exists(args.source):
        print "{} is not a valid directory".format(args.source)
        sys.exit()
    if not os.path.exists(args.destination):
        print "{} is not a valid directory".format(args.destination)
        sys.exit()

    # Identify audiobook and gather book details from books.google.com api.
    bookDetails = findBookDetails(args.source.rstrip('/'))
    if not bookDetails:
        sys.exit()
    # Verify that the files are in the correct order.
    # If they are not then the audiobook will be all out of order when we symlink
    correctOrder = verifyCorrectOrder(args)
    if not correctOrder:
        sys.exit()
    # Show the user a list of the symlinks that are about to be created
    proceed = actionSummary(args, bookDetails, scriptPath)
    if not proceed:
        sys.exit()
    # Create the symlinks
    symlinkCreate = createSymlinks(args, bookDetails, scriptPath)
    if not symlinkCreate:
        sys.exit()
    #make sure we are not overwriting something


def findBookDetails(source):
    #print getSourceFileList(args.source)
    print "\nsearching for {}".format(os.path.basename(source))
    bookIndex = 0
    bookTitle = os.path.basename(source)
    while True:
        bookDetails = getBookInfo(bookTitle, bookIndex)
        print "Found {} by {} published in {}".format(bookDetails["title"], bookDetails["author"],
                                                      bookDetails["date"])
        correctBook = raw_input("would you like to continue? [yes]/no/next/manual: ")
        if correctBook == "next":
            bookIndex += 1
        elif correctBook == "manual":
            bookTitle = raw_input("what book are you looking for? ")
            bookIndex = 0
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


def verifyCorrectOrder(args):
    # we have identified the book on books.google.com so we have (title, author, description, date, thumbnail)
        print "\nidentified the following files"
        for bookFile in sorted(getSourceFileList(args.source)):
            print bookFile
        correctOrder = raw_input("did they print out in the correct order? [yes]/no: ")
        #if the files are not in order its going to be a pain in the ass to fix. Do you do one by one?
        #TODO manual option for sorting
        if correctOrder == "no":
            print "\nnot available in version 1.0 "
            print "we need to order these before we can fix this"
            return False
        # the files were in order lets print out what we plan to do
        elif correctOrder == "yes" or correctOrder == "":
            return True


def actionSummary(args, bookDetails, scriptPath):
    print "\n"
    print "planning on creating the following directory and symlinks:"
    print "source:      {}".format(args.source)
    print "destination: {}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"]))
    print ""
    print "planning on creating the following symlinks"
    print "symlink -> file"
    for index, file in enumerate(sorted(getSourceFileList(args.source))):
        print "{}.%03d{} -> {}".format(cleanTitle(bookDetails["title"]), os.path.splitext(file)[1], file) % (
            index + 1)
    print "index.php -> {}".format(scriptPath)
    proceed = raw_input("Do you want to continue? yes/[no]: ")
    if proceed == "yes":
        return True
    else:
        return False


def createSymlinks(args, bookDetails, scriptPath):
    if not os.path.exists("{}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"]))):
        print "creating directory"
        os.mkdir("{}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"])))
        if os.path.exists("{}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"]))):
            print "directory created"
            os.chdir("{}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"])))
            print "creating symlinks"
            for index, file in enumerate(sorted(getSourceFileList(args.source))):
                os.symlink("{}/{}".format(args.source.rstrip('/'), file), "{}/{}/{}.%03d{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"]), cleanTitle(bookDetails["title"]), os.path.splitext(file)[1]) % (index + 1))
            #Symlinks the index.txt to index.php in the new audiobook directory
            if os.path.exists(scriptPath):
                os.symlink(scriptPath, "{}/{}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"]), "index.php"))
            print "symlinks created"
            print "thank you for using audiosym"
            return True
    else:
        print "the following directory already exists {}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"]))
        return False


def cleanTitle(title):
    """clean up titles so they have no special characters and are . separated"""
    cleanTitle = re.sub("'", "", title)
    cleanTitle = re.sub(r'(?i)(audiobook|unabridged|abridged)', "", cleanTitle)
    cleanTitle = re.sub("\([^)]+\)", "", cleanTitle)
    cleanTitle = re.sub("\[[^\]]+\]", "", cleanTitle)
    cleanTitle = re.sub("[^a-zA-Z1-9]", ".", cleanTitle)
    cleanTitle = re.sub("\.+", ".", cleanTitle)
    cleanTitle = re.sub("^\.|\.$", "", cleanTitle)
    cleanTitle = cleanTitle.lower()
    return cleanTitle


def getSourceFileList(directory):
    """Returns a list of files in a directory"""
    fileList = []
    if os.path.exists(directory):
        os.chdir(directory)
        for dirname, dirnames, filenames in os.walk("./"):
            # print path to all filenames.
            for filename in filenames:
                if fnmatch.fnmatch(os.path.join(dirname, filename).lstrip("./"), "*.mp3") or fnmatch.fnmatch(os.path.join(dirname, filename).lstrip("./"), "*.m4b") or fnmatch.fnmatch(os.path.join(dirname, filename).lstrip("./"), "*.acc"):
                    fileList.append(os.path.join(dirname, filename).lstrip("./"))
    return fileList


def getBookInfo(title, bookIndex=0):
    """pull book information from books.google.com api and return a dictionary"""
    request = requests.get(
        "https://www.googleapis.com/books/v1/volumes?&printType=books&q={}&startIndex={}".format(title, str(bookIndex)))
    if request.status_code == 200 and len(request.text) > 0:
        books = request.json()
        bookDetails = dict()
        #print books["items"][0]["volumeInfo"]
        bookDetails["title"] = books["items"][0]["volumeInfo"]["title"]
        bookDetails["author"] = books["items"][0]["volumeInfo"]["authors"][0]
        bookDetails["date"] = books["items"][0]["volumeInfo"]["publishedDate"]
        bookDetails["description"] = books["items"][0]["volumeInfo"]["description"]
        bookDetails["thumbnailURL"] = books["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]
        #print "title: {}".format(bookDetails["title"])
        #print "author: {}".format(bookDetails["author"])
        #print "date: {}".format(bookDetails["date"])
        #print "description: {}".format(unicode(bookDetails["description"], "utf8"))
        #print "thumbnail: {}".format(bookDetails["thumbnailURL"])
        return bookDetails
    else:
        print "failed"
    return


if __name__ == '__main__':
    main()
