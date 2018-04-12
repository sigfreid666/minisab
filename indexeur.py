import requests
import re
import html.parser
import logging

logger = logging.getLogger(__name__)


class MyParserNzb(html.parser.HTMLParser):

        def __init__(self):
            html.parser.HTMLParser.__init__(self)
            self.detecttable = False
            self.resultat = []
            self.debug = 0
            self.infoinput = ''

        def tri(x):
            res = 0
            if 'taille' not in x:
                res = 0
            elif x['taille'].find('GB') > 0:
                res = float(x['taille'][0:x['taille'].find('GB')]) * 100 * 1000
            elif x['taille'].find('MB') > 0:
                res = float(x['taille'][0:x['taille'].find('MB')]) * 100
            elif x['taille'].find('KB') > 0:
                res = float(x['taille'][0:x['taille'].find('KB')])
            return res

        def getresultat(self):
            self.resultat.sort(key=MyParserNzb.tri)
            return self.resultat

        def handle_starttag(self, tag, attr):
            if (tag == 'table') and (('class', 'xMenuT') in attr) and (('id', 'r2') in attr):
                    if self.debug == 1:
                            print('tag table trouve')
                    self.detecttable = True
            if (tag == 'input') and (('type', 'checkbox') in attr):
                    if self.debug == 1:
                            print('inputtrouve')
                    for x in attr:
                        if (x[0] == 'name'):
                            self.resultat.append({'id': x[1], 'url': r'http://www.binsearch.info/?action=nzb&%s=1' % x[1]})
            if (tag == 'span') and (('class', 'd') in attr):
                    self.infoinput = 'description'
            if (tag == 'span') and (('class', 's') in attr):
                    self.infoinput = 'title'
            if self.debug == 1:
                    print('Nouveau tag:', tag, ' attr:', attr)

        def handle_endtag(self, tag):
            if self.detecttable and (tag == 'table'):
                    self.detecttable = False
            if self.debug == 1:
                    print('fin tag:', tag)
            if (tag == 'span'):
                    self.infoinput = ''

        def handle_data(self, data):
            if (self.infoinput != '') and self.detecttable:
                if self.infoinput == 'description':
                    # if 'taille' in self.resultat[-1]:
                    #     self.resultat[-1]['taille'].append(data)
                    #     ind0 = data.strip().find('size:')
                    #     self.resultat[-1]['taille'].append(ind0)
                    # else:
                    #     self.resultat[-1]['taille'] = [ data ]
                    #     ind0 = data.strip().find('size:')
                    #     self.resultat[-1]['taille'].append(ind0)
                    ind0 = data.strip().find('size:')
                    if ind0 >= 0:
                        # ind1 = data.strip().find('size:', ind0)
                        # if ind1 > ind0:
                        self.resultat[-1]['taille'] = data.strip()[ind0 + len('size:'):]
                    else:
                        ind0 = data.strip().find('KB')
                        if ind0 >= 0:
                            self.resultat[-1]['taille'] += ' ' + data[:2]
                        ind0 = data.strip().find('MB')
                        if ind0 >= 0:
                            self.resultat[-1]['taille'] += ' ' + data[:2]
                        ind0 = data.strip().find('GB')
                        if ind0 >= 0:
                            self.resultat[-1]['taille'] += ' ' + data[:2]
                else:
                    # filtre pour virer le surplus
                    res = re.match(r'.*"(.*)".*', data)
                    if res:
                        data = res.group(1)
                    if self.infoinput in self.resultat[-1]:
                        self.resultat[-1][self.infoinput] += data
                    else:
                        self.resultat[-1][self.infoinput] = data
                    if not re.match(r'.*.nzb', data) is None:
                        if 'taille' in self.resultat[-1]:
                            self.resultat[-1]['taille'] += 'NZB'
                        else:
                            self.resultat[-1]['taille'] = 'NZB'


class MyParserNzbIndex(html.parser.HTMLParser):

    def __init__(self):
        html.parser.HTMLParser.__init__(self)
        self.resultat = []
        self.encours = {}
        self.debug = False
# <input type="checkbox" id="box142826553" name="r[]" value="142826553" onclick="shiftclick(arguments[0]);">

    def tri(x):
        res = 0
        # on filtre les virgules qui pollue la conversion
        if 'taille' in x:
            x['taille'] = x['taille'].replace(',', '')
        try:
            if 'taille' not in x:
                res = 0
            elif x['taille'].find('GB') > 0:
                res = float(x['taille'][0:x['taille'].find('GB')]) * 100 * 1000
            elif x['taille'].find('MB') > 0:
                res = float(x['taille'][0:x['taille'].find('MB')]) * 100
            elif x['taille'].find('KB') > 0:
                res = float(x['taille'][0:x['taille'].find('KB')])
        except:
            res = 0
        return res

    def getresultat(self):
        self.resultat.sort(key=MyParserNzbIndex.tri)
        return self.resultat

    def output(self, *data):
        if self.debug:
            print(*data)

    def handle_starttag(self, tag, attr):
        attr = dict(attr)
        if (tag == 'input') and ('id' in attr) and (attr['id'].find('box') != -1):
            self.encours['id'] = attr['value']
        if 'id' in self.encours:
            if (tag == 'label') and ('for' in attr) and (attr['for'] == 'box%s' % self.encours['id']):
                self.encours['label'] = ''
                self.encours['title'] = ''
            if (tag == 'span') and ('label' in self.encours):
                self.encours['span'] = ''
            if (tag == 'div') and ('divinfo' in self.encours):
                self.encours['divinfo'] += 1
            if (tag == 'div') and ('class' in attr) and (attr['class'] == 'info'):
                self.encours['divinfo'] = 1
            if (tag == 'a') and ('href' in attr) and ('divinfo' in self.encours):
                self.encours['href'] = attr['href']
            if (tag == 'td') and ('class' in attr) and (attr['class'] == 'nowrap') and ('url' in self.encours) and ('taille' not in self.encours):
                self.encours['td_div'] = ''
            if (tag == 'div') and ('td_div' in self.encours):
                self.encours['td_div'] = 'div'

    def handle_endtag(self, tag):
        if (tag == 'span') and ('span' in self.encours):
            del self.encours['span']
        if (tag == 'label') and ('label' in self.encours):
            del self.encours['label']
        if (tag == 'div') and ('divinfo' in self.encours):
            self.encours['divinfo'] -= 1
            if self.encours['divinfo'] == 0:
                del self.encours['divinfo']
        if (tag == 'a') and ('href' in self.encours):
            del self.encours['href']
        if (tag == 'tr') and ('id' in self.encours) and ('url' in self.encours):
            self.resultat.append(self.encours)
            self.encours = {}

    def handle_data(self, data):
        if ('label' in self.encours) and ('title' in self.encours):
            self.encours['title'] += data
        if ('href' in self.encours) and (data == 'Download'):
            self.encours['url'] = self.encours['href']
        if ('td_div' in self.encours) and (self.encours['td_div'] == 'div'):
            self.encours['taille'] = data
            del self.encours['td_div']


def recherche_indexeur(url, fichier, parseur=MyParserNzb):
    logger.debug('recherche_indexeur %s %s %s', url, fichier, str(type(parseur)))
    url = url.format(fichier)
    r = requests.get(url, cookies={'agreed': 'True'})
    #req2.add_header('Cookie', 'agreed=true')

    if r.status_code == 200:
        resultat = r.text
        logger.debug('recherche_indexeur : resultat %s ', resultat)
        parse = parseur()
        parse.feed(resultat)
        res = parse.getresultat()
        logger.info('recherche_indexeur : %d reponse(s)', len(res))
        return res
    else:
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    ur = 'http://www.nzbindex.nl/search/?q={0}&max=100'
    ur2 = 'https://binsearch.info/?q={0}&max=100'
    ret = recherche_indexeur(ur, 'yw2jLohnTIKTdJC36ltHaTB', MyParserNzbIndex)
    print(ret)
