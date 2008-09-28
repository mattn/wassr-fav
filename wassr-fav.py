#!-*- coding:utf-8 -*-
import os
import re
import logging
import wsgiref.handlers
from BeautifulSoup import BeautifulSoup,Tag
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

def to_text(soup, use_img_alt=False):
  ret = ""
  for e in soup.recursiveChildGenerator():
    if isinstance(e,Tag) and e.name == 'img' and not "icn-balloon" in e['src']:
      if use_img_alt:
        ret += "(%s)" % e['alt']
      else:
        e['src'] = "http://wassr.jp%s" % e['src']
        ret += unicode(e)
    elif isinstance(e,unicode):
      ret += e.strip()
  ret = ret.replace('&nbsp;', ' ').replace('  ', '\n')
  #ret = ' '.join([e.strip() for e in soup.recursiveChildGenerator() if isinstance(e,unicode) or (isinstance(e,Tag) and e.name == 'img')]).replace('&nbsp;', ' ').replace('  ', '\n')
  #soup = BeautifulSoup(ret, convertEntities=BeautifulSoup.HTML_ENTITIES)
  #return soup and soup.contents and soup.contents[0].encode('utf-8', 'replace').replace('\n', '') or ''
  return ret

class MainPage(webapp.RequestHandler):
  def head(self):
    self.get(True)

  def get(self, user):
    template_values = {
      'title' : 'Wassr fav',
      'link' : 'http://wassr-fav.appspot.com/',
      'user' : '',
      'favs' : [],
    }
    if user:
      template_values['link'] += user
      template_values['user'] += user

      page = urlfetch.fetch('http://wassr.jp/user/%s/received_favorites' % user)
      soup = BeautifulSoup(page.content)

      page_favs = soup.findAll('div', { 'class' : 'favorited_message'})
      r1 = re.compile(r'.*/([^/]*)/$')
      r2 = re.compile(r'(.*)\([^\)]+\) (.*)')
      for page_fav in page_favs:
        authors = page_fav.findAll('form', { 'class' : 'followbutton favorited_user noteTxt' })
        for author in authors:
          author = r1.sub(lambda x: x.group(1), author.find('a')['href'])
          template_values['favs'].append({
            'title' : to_text(page_fav.find('p', { 'class' : 'message description' }), True).strip(),
            'link' : 'http://wassr.jp%s' % page_fav.find('a', { 'class' : 'MsgDateTime' })['href'],
            'guid' : 'http://wassr.jp%s#%s' % (page_fav.find('a', { 'class' : 'MsgDateTime' })['href'], author),
            'author' : author,
            'icon' : 'http://wassr.jp/user/%s/profile_img.png.16' % author,
            'pubDate'  : r2.sub(lambda x: '%sT%s+0900' % (x.group(1), x.group(2)), to_text(page_fav.find('a', { 'class' : 'MsgDateTime' })).strip()),
          })

      self.response.headers['Content-Type'] = 'text/xml'
      path = os.path.join(os.path.dirname(__file__), 'wassr-fav.rss')
      self.response.out.write(template.render(path, template_values))
    else:
      path = os.path.join(os.path.dirname(__file__), 'wassr-fav.html')
      self.response.out.write(template.render(path, template_values))

def main():
  application = webapp.WSGIApplication([
    ('/(.*)', MainPage),
  ], debug=False)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
