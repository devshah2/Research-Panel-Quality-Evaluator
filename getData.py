# import nltk
import util
import requests
from bs4 import BeautifulSoup
import re

link="https://icpe2020.spec.org/program-committee/"
page = requests.get(link)
soup = BeautifulSoup(page.content, 'html.parser')
soup.beautify
soup=soup.get_text()
data=list(set(re.split(r'\n|\t| {2}|:|,', soup)))

util.run(data)
ddd=util.data
citedby=[x[0] for x in ddd]
hindex=[x[1] for x in ddd]
i10index=[x[2] for x in ddd]
print("Number of people {}, Average citedby {}, Average h-index {}, Average i10-index {} ".format(len(util.data),sum(citedby)/len(citedby),sum(hindex)/len(hindex),sum(i10index)/len(i10index)))