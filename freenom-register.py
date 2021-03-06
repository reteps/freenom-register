#!/usr/bin/env python3


import requests, sys
from bs4 import BeautifulSoup


class FreenomError(Exception):
    pass


class Freenom(object):
    def __init__(self):
        self.session = requests.Session()

    def login(self, email, password):
        url = "https://my.freenom.com/dologin.php"
        payload = {'token': self.get_token('https://my.freenom.com/clientarea.php'),
                    'username': email,
                    'password': password}
        r = self.session.post(url, payload, headers={'Host': 'my.freenom.com', 'Referer': 'https://my.freenom.com/clientarea.php'})
        if r.status_code != 200:
            raise FreenomError(f"Could not reach {url}")
        elif 'Hello' not in r.text:
            raise FreenomError("Email or password is incorrect.")

    def is_available(self, domain):
        payload = {
                'domain':domain.split(".")[0],
                'tld':domain.split(".")[1]
        }
        r = self.session.post("https://my.freenom.com/includes/domains/fn-available.php", payload, headers={'Host': 'my.freenom.com', 'Referer': 'https://my.freenom.com/domains.php'}).json()['top_domain']
        return r["status"] == "AVAILABLE" and r["type"] == "FREE"

    def get_token(self, url):
        return self.session.get(url).text.split('name="token" value="',2)[1].split('"',1)[0]

    def register_domain(self, domain):
        self.domain = domain
        self.add_to_cart()
        self.checkout()

    def add_to_cart(self):
        url = "https://my.freenom.com/includes/domains/confdomain-update.php"
        if not self.is_available(self.domain):
            raise FreenomError("Domain is not available.")
        payload = {
                'domain': self.domain,
                'period': '12M'
        }
        r = self.session.post(url, payload, headers={'Host': 'my.freenom.com', 'Referer': 'https://my.freenom.com/cart.php?a=confdomains'}).json()
        if r["status"] != "OK":
            raise FreenomError("Something went wrong.")

    def checkout(self): 
        token = self.get_token("https://my.freenom.com/cart.php?a=confdomains")
        periodName = self.domain.split(".")[0] + "_" + self.domain.split(".")[1] + "_period"
        payload = {
                "token": token,
                "update": "true",
                periodName: "12M",
                "idprotection[0]":"on",
                "domainns1":"ns01.freenom.com",
                "domainns2":"ns02.freenom.com",
                "domainns3":"ns03.freenom.com",
                "domainns4":"ns04.freenom.com",
                "domainns5":""
        }
        r = self.session.post("https://my.freenom.com/cart.php?a=confdomains", payload, headers={'Host': 'my.freenom.com', 'Referer': 'https://my.freenom.com/cart.php?a=confdomains'})
        soup = BeautifulSoup(r.text,"lxml")
        form = soup.find("form", {"id":"mainfrm"}).findAll("input")
        skipValues = ["accepttos", "fpbb"]
        # generate fpbb value with https://repl.it/repls/FamousVoluminousDesigners
        fpbb = "0400tfefJbtE5xsNf94lis1zth5kjp6ui/+cWtQkekKVyR8+WO5tA7Jn6YfuVhgCd8ygDIKINVrQrNKlRNM4vbTYwJwRbjiPURafex1TLARybUqvwFRqyepQW4stPHxOZiJVdLDs+1JC1RHeqz7TtH33U+dEACNvUWfJFmQWppRl6Bv4pp48B2PR0LUM6Rn3JtHEfF9hXdZ4DRRiwxmZVjl9I9/GSHlRbmqB3FC5PmOztORMyPpjzYuuV+VhT2JQxvTdjNXsgMEghG0w/Sp/nxaSrvPoP5g1QwsR7BNGGqFxo7/8Iivq5JsyIM0XRTItYnO2hCiebBE66IIElXD0hEMtvQl2olrNgUNPh5iH0wK6uVK7Hlz2rUeAnePp/Vp8gaYPika5+mDohXq9f2PXvHogeO3Gk9aWzC1q6smjVLTDyc/3oU6k968Na1C/0PQwVK9AfF9hXdZ4DRRkrbXWcoCj3I1znntcmg8XIiroNPn6uMQnzqtbxtgjn55JX+F1MJDnYeTcLtcejyCxPk2UkqDvdYEYDfmfBwBYRhc3f5urJ1aotlycMEBL1IzyVekwhI5/tPvXfQEg+KLRVsDNUznM+4IlRQO86SD0OIS7LH591kg7Q92FGKueuw=="
        payload = {
                "accepttos": "on",
                "token": token,
                "country": "US",
                "fpbb": fpbb,
        }
        for value in form:
            if value.get("name") in skipValues or value.get("name") == None:
                continue
            payload[value.get("name")] = value.get("value")
        r = self.session.post("https://my.freenom.com/cart.php?a=checkout", payload, headers={'Host': 'my.freenom.com', 'Referer': 'https://my.freenom.com/cart.php?a=checkout'})
        if "Your Order Number is:" not in r.text:
            raise FreenomError("Registering the domain was unsuccessful. You may of been banned.")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("usage: freenom EMAIL PASSWORD DOMAIN")
        exit()
    freenom = Freenom()
    freenom.login(sys.argv[1], sys.argv[2])
    freenom.register_domain(sys.argv[3])
