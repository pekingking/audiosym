import argparse
import os
import glob
import re

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", help="base directory to attach symlinks to")
    parser.add_argument("-d", "--destination", help="base directory /path/to/books/")
    args = parser.parse_args()
    if not os.path.exists(args.source):
        print "{} is not a valid directory".format(args.source)
        return
    if not os.path.exists(args.destination):
        print "{} is not a valid directory".format(args.destination)
        return
    #TODO remove after debugging
    if False:
        print cleanTitle("Harry's big adventure (1asd)")
    else:
        #print getSourceFileList(args.source)
        print "\nsearching for {}".format(os.path.basename(args.source.rstrip('/')))
        bookIndex = 0
        bookTitle = os.path.basename(args.source.rstrip('/'))
        while True:
            bookDetails = getBookInfo(bookTitle, bookIndex)
            print "Found {} by {} published in {}".format(bookDetails["title"], bookDetails["author"],
                                                          bookDetails["date"])
            correctBook = raw_input("would you like to continue? [yes]/no/next/manual: ")
            if correctBook == "no":
                print "sorry we could not find your book"
                print "exiting"
                return
            elif correctBook == "next":
                bookIndex += 1
            elif correctBook == "manual":
                bookTitle = raw_input("what book are you looking for? ")
                bookIndex = 0
            elif correctBook == "yes" or correctBook == "":
                print "great lets continue"
                break
        # we have identified the book on books.google.com so we have (title, author, description, date, thumbnail)
        print "\nidentified the following files"
        for bookFile in getSourceFileList(args.source):
            print bookFile
        correctOrder = raw_input("did they print out in the correct order? [yes]/no: ")
        #if the files are not in order its going to be a pain in the ass to fix. Do you do one by one?
        #TODO manual option for sorting
        if correctOrder == "no":
            print "\nnot available in version 1.0 "
            print "we need to order these before we can fix this"
        # the files were in order lets print out what we plan to do
        elif correctOrder == "yes" or correctOrder == "":
            print "\n"
            print "planning on creating the following directory and symlinks:"
            print "source:\t\t\t{}".format(args.source)
            print "destination:\t{}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"]))
            print ""
            print "planning on creating the following symlinks"
            print "symlink -> file"
            for index, file in enumerate(getSourceFileList(args.source)):
                print "{}.%03d{} -> {}".format(cleanTitle(bookDetails["title"]), os.path.splitext(file)[1], file) % (
                    index + 1)
        #TODO create the actual directory and symlinks
            proceed = raw_input("Do you want to continue? yes/[no]: ")
            if proceed == "yes":
                #make sure we are not overwriting something
                if not os.path.exists("{}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"]))):
                    print "creating directory"
                    os.mkdir("{}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"])))
                    if os.path.exists("{}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"]))):
                        print "directory created"
                        os.chdir("{}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"])))
                        print "creating symlinks"
                        for index, file in enumerate(getSourceFileList(args.source)):
                            os.symlink("{}/{}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"]), file),
                            "{}/{}/{}.%03d{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"]), cleanTitle(bookDetails["title"]), os.path.splitext(file)[1]) % (index + 1))
                        print "symlinks created"
                        print "thank you for using audiosym"
                else:
                    print "the following directory already exists {}/{}".format(args.destination.rstrip('/'), cleanTitle(bookDetails["title"]))
                    return


def cleanTitle(title):
    """clean up titles so they have no special characters and are . separated"""
    cleanTitle = re.sub("'", "", title)
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
        for files in glob.glob("*.mp3"):
            fileList.append(files)
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