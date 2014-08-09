#!/usr/bin/python
# -*- coding: utf8 -*-
import appindicator
import gtk
import gobject
import tempfile
import math

from tools import *
from lxml import html, etree

COLOR_DICT={
            'white':'#fff',
            'red':'#f00',
            'green':'#090',
            'normal':'#0066cc'
}

TRAFFIC_LEFT_BEFORE_SESSION_SEARCH = re.compile('<td style="color:#000000;">(\d+\.\d+) &#208;&#191;&#208;&#190;')


def get_text(tag):
    return tag.text_content().encode('utf-8','ignore').strip()
#    return tag.text.encode('utf-8', 'ignore').strip()

class Inter():    
    def __init__(self):
        self.last_left = None
        if hasattr(settings, 'TARIFF_LIMIT_MB'):
            self.max_value = settings.TARIFF_LIMIT_MB
        else:
            self.max_value = None
        self.current_dir=os.path.dirname(os.path.abspath(__file__))+'/'
        print self.current_dir 
        self.tmp_dir=self.current_dir+'tmp/'

        self.indicator = appindicator.Indicator('inter_indicator', self.current_dir+'/icon.svg', appindicator.CATEGORY_APPLICATION_STATUS)
        self.indicator.set_status( appindicator.STATUS_ACTIVE )
#        self.indicator.set_icon_theme_path(self.tmp_dir)
        self.set_label(None)
        m = gtk.Menu()
        group = None
        time_1min_item = gtk.RadioMenuItem(group,'1 min')
        group = time_1min_item
        time_2min_item = gtk.RadioMenuItem(group,'2 min')
        time_5min_item = gtk.RadioMenuItem(group,'5 min')
        time_10min_item = gtk.RadioMenuItem(group,'10 min')
        time_15min_item = gtk.RadioMenuItem(group,'15 min')
        time_30min_item = gtk.RadioMenuItem(group,'30 min')
        time_60min_item = gtk.RadioMenuItem(group,'60 min')
        refresh_now_item = gtk.MenuItem( 'Refresh NOW' )
        
        self.ip_label = gtk.MenuItem('Ip: N/A')
        self.money_left_label = gtk.MenuItem('Money: N/A')
#         self.traffic_consumed_label = gtk.MenuItem("Total: %s Mb, Tx: N/A Mb, Rx: N/A Mb")
#         self.traffic_left_before_session = gtk.MenuItem('IP: N/A')
        self.traffic_left_label = gtk.MenuItem('Traffic Left: N/A')
        qi = gtk.MenuItem( 'Quit' )
        
        m.append(self.traffic_left_label)
        m.append(self.ip_label)
        m.append(self.money_left_label)
#         m.append(self.traffic_consumed_label)
#         m.append(self.traffuc_left_before_session_label)

        m.append(gtk.SeparatorMenuItem())
        
        m.append(time_1min_item)
        m.append(time_2min_item)
        m.append(time_5min_item)
        m.append(time_10min_item)
        m.append(time_15min_item)
        m.append(time_30min_item)
        m.append(time_60min_item)

        m.append(gtk.SeparatorMenuItem())
        m.append(refresh_now_item)
        m.append(qi)
        
        self.indicator.set_menu(m)
        m.show_all()
#        time_1min_item.show()
#        time_2min_item.show()
#        time_5min_item.show()
#        time_10min_item.show()
#        time_15min_item.show()
#        time_30min_item.show()
#        time_60min_item.show()
#        qi.show()
        
        self.timeout=settings.UPDATE_DELAY_SECONDS
        
        time_1min_item.connect('activate', self.time_1min_handler)
        time_2min_item.connect('activate', self.time_2min_handler)
        time_5min_item.connect('activate', self.time_5min_handler)
        time_10min_item.connect('activate', self.time_10min_handler)
        time_15min_item.connect('activate', self.time_15min_handler)
        time_30min_item.connect('activate', self.time_30min_handler)
        time_60min_item.connect('activate', self.time_60min_handler)
        
        refresh_now_item.connect('activate', self.update)
        qi.connect('activate', quit)
    
        self.source_id = gobject.timeout_add(1000, self.update)
    
    def set_timeout(self, mins):
        self.timeout=mins*60*1000
        gobject.source_remove(self.source_id)
        self.source_id = gobject.timeout_add(self.timeout, self.update)
        
    def time_1min_handler(self, action):
        self.set_timeout(1)

    def time_2min_handler(self, action):
        self.set_timeout(2)

    def time_5min_handler(self, action):
        self.set_timeout(5)

    def time_10min_handler(self, action):
        self.set_timeout(10)

    def time_15min_handler(self, action):
        self.set_timeout(15)

    def time_30min_handler(self, action):
        self.set_timeout(30)

    def time_60min_handler(self, action):
        self.set_timeout(60)

    def get_stats(self):    
            stage='1'
            post_fields='phone='+settings.PHONE+'&pass='+settings.PASS+'&ref_link=&js=1'
            content, code=get_page('https://assa.intertelecom.ua/ru/login', self.tmp_dir, stage, None, False, post_fields, False, True,'Get projects list')
#             print content
            tree = html.fromstring(content)
            # we don't know the td_num for these 3 yet, setting None so id doesn't match unless we find the num
            traffic_consumed_td_num = None 
            td_money_left_td_num = None
            td_ip_td_num = None
            ip = "N/A"
            
            td_num = 0
            for td in tree.cssselect("td"):
                td_num+=1
                try:
                    td_content = etree.tostring(td)
#                     print td_num,")", td_content 
                except Exception:
                    continue

                if td_content.find('<td>IP</td>&#13;') > -1:
                    td_ip_td_num = td_num +1
                if td_ip_td_num == td_num:
                    ip = get_text(td)
                    
                if td_content.find('<td>&#208;&#161;&#208;&#176;&#208;&#187;&#209;&#140;&#208;&#180;&#208;&#190;</td>&#13;') > -1:
                    td_money_left_td_num = td_num + 1
                if td_money_left_td_num == td_num:
                    money_left_str = get_text(td)

                if td_content.find('<td>&#208;&#162;&#209;&#128;&#208;&#176;&#209;&#132;&#208;&#184;&#208;&#186; &#208;&#156;&#208;&#145;</td>&#13;') > -1:
                    traffic_consumed_td_num = td_num + 1
                if td_num == traffic_consumed_td_num:
                    try:
                        traffic_consumed_str = td.cssselect('strong')[0].text.strip()
                    except Exception:
                        pass

                try:
                    match = TRAFFIC_LEFT_BEFORE_SESSION_SEARCH.search(td_content)
                    if match:
                        traffic_left_before_session_str = match.group(1) 
                except Exception as err:
                    print td_num,")","error:\n", err
            try:
                money_left=float(money_left_str)
            except Exception:
                money_left = "N/A"
            try:
                traffic_consumed=float(traffic_consumed_str)
            except Exception:
                traffic_consumed = "N/A"
            try:
                traffic_left_before_session=float(traffic_left_before_session_str)
            except Exception:
                traffic_left_before_session = "N/A"
            try:
                traffic_left=traffic_left_before_session-traffic_consumed
            except Exception:
                traffic_left = "N/A"
            
            result={
                        'ip':ip,
                        'money_left':money_left,
                        'traffic_consumed':traffic_consumed,
                        'traffic_left_before_session':traffic_left_before_session,
                        'traffic_left':traffic_left
                    }
            print result
            return result
    
    def quit(self, item):
            gtk.main_quit()
    
    def set_label(self, value, progress=0.0, text_color='normal', progress_color='normal'):
        print "set_label: %s of color %s, progress = %s" % (value, text_color, progress)
        if value:
            text=str(value)
        else:
            text="N/A"
        self.indicator.set_label(text)
        
        with open(self.current_dir + '/icon.svg') as svg_file, tempfile.NamedTemporaryFile(delete=True) as temp_file:
            svg = svg_file.read()
            svg = svg.replace('%percent%', text)
            svg = svg.replace('%color%', COLOR_DICT[text_color])
            svg = svg.replace('%progress_color%', COLOR_DICT[progress_color])
            if progress:
                svg = svg.replace('%path%', self.create_svg_arc_path(progress))
            print temp_file.name
            temp_file.write(svg)
            temp_file.flush()
            self.indicator.set_icon(temp_file.name)

        while gtk.events_pending():
            gtk.main_iteration()
    
    def update(self, action=None):
        print "=== update ==="
        if not self.last_left:
            self.set_label('N/A', 0, text_color='green')
        timeout = self.timeout
        try:
            stats=self.get_stats()
            self.last_left=int(stats['traffic_left'])
            self.max_value = self.max_value or self.last_left
            percentage = float(self.last_left) / float(self.max_value)
        except Exception:
            print "Update problem ... Last Left: %s" % self.last_left            
            self.set_label(self.last_left, text_color='red')
            self.traffic_left_label.set_label("Traffic Left: N/A")
            self.money_left_label.set_label("Money:  N/A")
            self.ip_label.set_label("IP: N/A")
            timeout = 10*60*1000 #10 minutes
        else:
            print "Updating... Left: %s" % self.last_left
            color = 'normal' if percentage > 0.2 else 'red'
            self.set_label(self.last_left, progress=percentage, progress_color=color)
            self.traffic_left_label.set_label("Traffic Left: %s Mb" % self.last_left)
            self.money_left_label.set_label("Money: %s" % stats['money_left'])
            self.ip_label.set_label("IP: %s" % stats['ip'])
        try:
            gobject.source_remove(self.source_id)
        except Exception:
            pass
        self.source_id = gobject.timeout_add(timeout, self.update)
        
    def create_svg_arc_path(self, percentage):
        print 'generating path', percentage
        percentage = percentage if percentage != 1.0 else 0.99
        canvasSize = 64
        centre = canvasSize / 2
        radius = canvasSize * 0.8 / 2
        startY = centre-radius

        d = percentage * 360
        radians = math.pi * (d - 90) / 180
        endx = centre + radius * math.cos(radians)
        endy = centre + radius * math.sin(radians)
        largeArc = 1 if d > 180 else 0
        return "M{},{} A{},{} 0 {},1 {},{}".format(centre, startY, radius, radius, largeArc, endx, endy)


if __name__ ==  '__main__':
    inter=Inter()
    gtk.main()
