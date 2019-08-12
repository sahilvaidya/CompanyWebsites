# Code written by Sahil Vaidya and Jianchen Gu 2019

# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
from bs4 import BeautifulSoup
from googlesearch import search
import unidecode
import logging
import time


# mySQL linkage
import mysql.connector
from mysql.connector import Error
from configparser import ConfigParser

# list of obvious non-company URLs
blacklist = ['wikipedia', 'facebook', 'linkedin', 'download', 'indeed', '.pdf', 'dictionary',
             'wyndhamhotels.com', 'twitter','tripadvisor','proff', 'rocketreach', 'statista',
             'marketwatch', 'simplyhired', 'free-apply', 'bloomberg', 'foursquare.', 'amazon.',
             'youtube']

# filters out URLs that we don't want/blacklisted URLs
# @param url_list: is the current list of URLs we got from search1 and search2
# @return url_list: is the current list of URLs after removing all blacklisted URLs
def clean(url_list):
    to_remove = []
    for oneurl in url_list:
        for word in blacklist:
            if word in oneurl:
                to_remove.append(oneurl)
    for elems in to_remove:
        try:
            url_list.remove(elems)
        except:
            pass
    return url_list


# removes extraneous parts of the URL to leave us with the website name
# for easier comparison later on
# "stripped" will always refer to the stripped URL in the program
# @param strip_url: is a complete URL
# @return stripped: is the website domain of @param strip_url
def urlstrip(strip_url):
    stripped = strip_url.replace('http://', '')
    stripped = stripped.replace('www.', '')
    stripped = stripped.replace('https://', '')
    stripped = stripped[:stripped.index('.')]
    return stripped


# lowercases all parameters for uniform comparison
# checks if either company name or acronym are the same as the website domain name
# @param company_name: is the decoded company name
# @param url_name: is the domain name (stripped website URL)
# @param company_acronym: is the company name acronym
# @return boolean: is True if @param company_name or @param company_acronym are equal to
#                      @param url)name
#                  if False otherwise
def checkurl(company_name, url_name, company_acronym):
    if company_name.lower() == url_name.lower() or company_acronym.lower() == url_name.lower():
        return True


# sequence to find <title> tag of website html
# check if name belongs in the title of website, vice versa using sets
# @param siteurl: is a cleaned URL
# @param company_name: is the decoded company name
# @return boolean: is True if the set format of "company_name" is
#                      a subset of the set format of "siteurl", and vice versa
#                  is False otherwise
def findtitletag(siteurl, company_name):
    try:
        request = urllib.request.Request(siteurl, headers={'User-Agent': user_agent})
        html = urllib.request.urlopen(request,timeout = 5).read()
        soup = BeautifulSoup(html, 'html.parser', from_encoding="utf-8")
        # <title> tag
        title = soup.find('title').text.lower()
        title = title.replace(',', '')
        title_words = title.split()

        company_name = company_name.lower()
        company_words = company_name.split()


        # checks for university keyword and doesn't add it to company_words_decoded
        # for comparison to the title tag
        company_words_decoded = []
        for words in company_words:
            if not isUniversity(unidecode.unidecode(words)):
                company_words_decoded.append(unidecode.unidecode(words))

        # check if we need "the" in university name/tags

        # replace 'de' with 'of' since many university <title> tags are in Spanish
        strDe = 'de'
        count1 = 0
        for words in company_words_decoded:
            if strDe in words:
                company_words_decoded[count1] = company_words_decoded[count1].replace('de', 'of')
            count1 += 1
        company_words_decoded = set(company_words_decoded)

        # print(company_words_decoded)

        title_words_decoded = []
        for words in title_words:
            if isUniversity(unidecode.unidecode(words)):
                continue
            title_words_decoded.append(unidecode.unidecode(words))

        count2 = 0
        for words in title_words_decoded:
            if strDe in words:
                title_words_decoded[count2] = title_words_decoded[count2].replace('de', 'of')
            count2 += 1
        title_words_decoded = set(title_words_decoded)

    #   [FOR TESTING]
    #   print(siteurl)
    #   print(title_words_decoded)
    #   print(title_words_decoded.issubset(company_words_decoded))
    #   print(company_words_decoded.issubset(title_words_decoded))

        if company_words_decoded.issubset(title_words_decoded) or title_words_decoded.issubset(company_words_decoded):
            return True
        else:
            return False
    except Exception:
        return False


# lowercases and removes all spaces in company name
# checks if either company is substring of name (URL), vice versa
# @param company_name: is the decoded company name
# @param url_name: is the domain name (stripped website URL)
# @return boolean: is True if company name is substring of website URL, and vice versa
def contains(company_name, url_name):
    company_name_loc = company_name.lower()
    company_name_loc = company_name_loc.replace(" ", "")
    if str(company_name_loc) in str(url_name) or str(url_name) in str(company_name_loc):
        return True


extra_words = ['GS', 'A/S', 'LLC', 'ADW', 'S.C.', 'A.C.', 'IIJ']

# removes extraneous words in the company name that can affect our search results
# @param company_name: is the decoded company name
# @return company_name: is removed of extra words and stripped of whitespace
def cut(company_name):
    for word in extra_words:
        if word in company_name:
            company_name = company_name.replace(word, '')
    company_name = company_name.strip()
    return company_name


invalid_words = ['professor', 'self-employed', 'autonomo', 'freelance',
                 'researcher', 'retired', 'independent', 'independiente', 'self employed', 'n/a', 'free lance']
# Independent Film Producer

# checks if a company name is a case we don't care about
# @param company_name: is the decoded company name
# @return boolean: is True if blank company name, non-alphanumeric name, or is an invalid word
#                  is False if company name is valid
def notValid(company_name):
    if not company_name or not any(letter.isalpha() for letter in company_name):
        return True
    company_name = company_name.lower()
    for invalid in invalid_words:
        if invalid in company_name:
            return True
    return False


uni_words = ['university', 'universidad', 'universitat', 'universidade',
             'universite', 'universaidad', 'college']

# checks if a company name is a university
# @param company_name: is the decoded company name
# @return boolean: is True if any university word is in company_name
#                  is False if university word is NOT in company_name
def isUniversity(company_name):
    company_name = company_name.lower()
    for uni in uni_words:
        if uni in company_name:
            return True
    return False

logging.basicConfig(filename='scrape_test.log', filemode='w', format='%(message)s')

try:
    config = ConfigParser()
    config.read('params.ini')

    user_val = config.get('database', 'db_user')
    pass_val = config.get('database', 'db_password')
    host_val = config.get('database', 'db_host')
    db_val = config.get('database', 'db_database')

    # configuration dictionary
    config = {
        'user': user_val,
        'password': pass_val,
        'host': host_val,
        'database': db_val,
        'raise_on_warnings': True
    }


    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(buffered = True)

    if connection.is_connected():
        db_Info = connection.get_server_info()

        print("Connnected to MySQL database... MySQL Server version on ",db_Info)
        Query = "SELECT company FROM ********** " \
                "WHERE company REGEXP '^[A-Za-z0-9., áâäæãåāèéêėîíįìôöòóœøōõûüùúūçćÿśšñń()\\/-]+$' " \
                "AND company_website = '' OR company_website IS NULL " \
                "AND ******.company NOT IN ( " \
                "SELECT **********.value FROM ********* " \
                ") " \
                "GROUP BY company " \
                "ORDER BY company desc"

        cursor.execute(Query)
        record = cursor.fetchall()
        print(len(record))

        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 ' \
                     '(KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'

        # final list of URLs/one website per company
        websites = []
        # statistics variables
        count = 0
        failures = 0
        skips = 0

        try:
            for comp in record:
                company_name = comp[0]
                company_name_unedited = company_name
                count += 1
                print("Number " + str(count) + ". Company: " + str(company_name))

                company_name = cut(company_name)
                decoded_company = unidecode.unidecode(company_name)
                company_name = decoded_company.replace(',', '')

                # print(decoded_company)

                if notValid(decoded_company):
                    skips += 1
                    print("Skipped " + str(company_name_unedited))
                    logging.warning("Company: " + str(company_name_unedited) + " URL: Skipped")

                    skipped = (company_name_unedited,)
                    Insert = "UPDATE ********** SET company_website = 'SKIP' WHERE company = %s"
                    cursor.execute(Insert, skipped)
                    connection.commit()
                    continue

                param = (company_name,)
                Query2 = "SELECT company_website FROM ********** " \
                         "WHERE not company_website = '' AND company = %s"
                cursor.execute(Query2, param)
                if cursor.fetchone():
                    cursor.execute(Query2, param)
                    (found_url,) = cursor.fetchone()

                    site2 = (str(found_url), company_name_unedited)
                    print(str(found_url) + " found from other entry")
                    logging.warning("Company: " + str(company_name_unedited) + " URL: " + str(found_url))
                    Insert2 = "UPDATE ********** SET company_website = %s WHERE company = %s"
                    cursor.execute(Insert2, site2)
                    connection.commit()
                    continue



                words = company_name.split()
                acronym = "".join([word[0] for word in words if word[0].isupper()])
                found = False

                # master URL list
                urls = []
                # add all possible searches of current company to master list
                try:
                    search1 = search(company_name, tld="co.in", num=10, stop=10, pause=2)
                    for url in search1:
                        urls.append(url)

                    # check if the word company (or others as we need) exists in the name
                    # if yes, then don't make a second search
                    # if no, then we check if it's a university
                    #     if yes university, then don't make a second search
                    #     if no university, then search with 'company' appended
                    search2 = []
                    company_append = ['company']
                    for comp in company_append:
                        if comp in company_name.lower():
                            search2 = []
                            # print('skipped second search due to company')
                        else:
                            if isUniversity(company_name):
                                search2 = []
                                # print('skipped second search due to university')
                            else:
                                search2 = search(company_name + ' company', tld="co.in", num=10, stop=10, pause=2)
                                # print('searched with company')

                    for url in search2:
                        urls.append(url)
                except:
                    print("Skipped " + str(company_name_unedited))
                    logging.warning("Company: " + str(company_name_unedited) + " URL: Skipped")
                    skips += 1

                    skipped = (company_name_unedited,)
                    Insert = "UPDATE ********** SET company_website = 'SKIP' WHERE company = %s"
                    cursor.execute(Insert, skipped)
                    connection.commit()
                    continue

                urls = clean(urls)

                # search URL master list and add correct company websites to websites[]
                # case 1: check if either company name or acronym are in the name (URL)
                for url in urls:
                    name = urlstrip(url)
                    if checkurl(company_name, name, acronym):
                        websites.append(url)
                        found = True
                        break
                    if len(name) > 4 and contains(company_name, name):
                        websites.append(url)
                        found = True
                        break


                # case 2: <title> tags in HTML file
                if not found:
                    for url in urls:
                        if findtitletag(url, company_name):
                            websites.append(url)
                            found = True
                            break

                # case 3: checks if company_name and name are substrings of each other
                if not found:
                    for url in urls:
                        name = urlstrip(url)
                        if contains(company_name, name):
                            websites.append(url)
                            found = True
                            break

                # failure tracker
                if not found:
                    failures += 1
                    print("Unfound: " + str(company_name_unedited))

                    unfound = (company_name_unedited,)
                    Insert = "UPDATE ********** SET company_website = 'UNFOUND' WHERE company = %s"
                    cursor.execute(Insert, unfound)
                    connection.commit()
                    logging.warning("Company: " + str(company_name_unedited) + " URL: Unfound")
                    logging.warning("Searched List:")
                    for u in urls:
                        logging.warning(str(u))
                else:
                    print(websites[-1])
                    websites[-1] = (websites[-1][:200] + '..') if len(websites[-1]) > 200 else websites[-1]
                    site = (websites[-1],company_name_unedited)
                    Insert = "UPDATE ********** SET company_website = %s WHERE company = %s"
                    cursor.execute(Insert,site)
                    connection.commit()
                    logging.warning("Company: " + str(company_name_unedited) + " URL: " + str(websites[-1]))
                    logging.warning("Searched List:")
                    for u in urls:
                        logging.warning(str(u))

            # print(websites)
            print("There are " + str(failures) + " unfound websites")
            print("We skipped " + str(skips) + " websites")

        except KeyboardInterrupt:
            print("Exiting Program via KeyboardInterrupt")
            print("Processed " + str(count - 1) + " websites")
            print("Found " + str(count - failures - skips - 1) + " websites")
            print("Did not find " + str(failures)+ " websites")
            print("We skipped " + str(skips) + " websites")


except Error as e:
    print ("Error while connecting to MySQL", e)
finally:
    #closing database connection.
    if(connection.is_connected()):
        cursor.close()
        connection.close()
        print("MySQL connection is closed")

