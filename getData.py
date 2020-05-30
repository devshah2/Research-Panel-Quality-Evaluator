import sys
import util
import requests
from bs4 import BeautifulSoup
import re
import argparse

parser = argparse.ArgumentParser(description='Find data about researchers')
parser.add_argument('-l','--link', action="store", help="Enter link to scrape", dest="link")
parser.add_argument('-n','--names', action="store", help="Enter list of names seperated by commas", dest="names")
args = parser.parse_args()
#test link="https://icpe2020.spec.org/program-committee/"
if(args.link!=None):
    link=args.link
    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')
    soup.beautify
    soup=soup.get_text()
    data=list(set(re.split(r'\n|\t| {2}|:|,', soup)))
elif(args.names!=None):
    data=args.names.split(",")
else:
    print("Enter some value try -h for help")
    sys.exit()
util.run(data)
ddd=util.data
citedby=[x[0] for x in ddd]
hindex=[x[1] for x in ddd]
i10index=[x[2] for x in ddd]
if(len(citedby)>0):
    print("Number of people {}, Average citedby {}, Average h-index {}, Average i10-index {} ".format(len(util.data),sum(citedby)/len(citedby),sum(hindex)/len(hindex),sum(i10index)/len(i10index)))
else:
    print("No researcher found")
