import os
import argparse
from bs4 import BeautifulSoup


parser = argparse.ArgumentParser()
parser.add_argument("directory", 
                    help="The directory of photos to put into an HTML page.")
parser.add_argument("-o", "--output", 
                    help="The filepath to output the resulting HTML page to.")
parser.add_argument("-t", "--title", 
                    help="The title of the HTML page.")
arguments = parser.parse_args()


html = BeautifulSoup("<html></html>", "html.parser")
head = html.new_tag("head")
title = html.new_tag("title")
if arguments.title:
    title.string = arguments.title
else:
    title.string = "Image Gallery"

meta = html.new_tag("meta", charset="UTF-8")

head.append(title)
head.append(meta)
html.html.append(head)

body = html.new_tag("body")

h1 = html.new_tag("h1")
h1.string = title.string
body.append(h1)

filenames = os.listdir(arguments.directory)
filenames.sort()
for filename in filenames:
    filepath = os.path.join(arguments.directory, filename)
    if os.path.isfile(filepath) and filepath.split(".")[1].lower() != "html":
        paragraph = html.new_tag("p")
        link = html.new_tag("a", href=filename)
        link.string = filename.split(".")[0]
        paragraph.append(link)
        body.append(paragraph)

html.html.append(body)

if arguments.output:
    outfile = open(arguments.output, "w")
    outfile.write(html.prettify())
    outfile.flush()
else:
    print(html.prettify())


