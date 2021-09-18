#!/usr/bin/env python
#-*- coding: UTF-8 -*-

from genericpath import isdir
import sys, os
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication,  QVBoxLayout, QLabel, QMainWindow, QProgressBar,\
    QToolBar, QAction,  QStyle, QSlider, QWidget, QToolButton, QMenu, QStatusBar, QStyleFactory, \
    QPushButton, QFileDialog, QListView
from PyQt5.QtCore import QStringListModel
from PyQt5.QtGui import QIcon
import mpd
import glob
import time
import configparser
#import Notify


configdir = os.path.expanduser('~/')
configname=os.path.join(configdir, 'qmini_mpd.ini')
config = configparser.ConfigParser()
port=6600
addr="localhost"
def N_(msg): return msg

def getrecords(i):
	try:
		artist=i['artist']
	except KeyError:
			artist = "Unknown Artist"
	try:
		album=i['album']
	except KeyError:
		album = "Unknown Artist"
	try:
		title=i['title']
	except KeyError:
		try:
			title = i["file"].split("/")[-1]
		except KeyError:
			title= "Unknown Title"
	try:
		year=i['date']
	except KeyError:
		year = "Unknown Year"
	#~ lst=	[title, 
	lst=[title, album, artist, year]
	"""for i in lst:
		if i.find('&')>0:
			lst[lst.index(i)]=i.replace('&', '&amp;')
	lst.insert(0, .replace('&', '&amp;'))
	#~ print lst"""
	return lst

def date_fmt(d):
	if d>86400:fmt="%d:%H:%M:%S"
	elif d>3600:fmt="%H:%M:%S"
	else:fmt="%M:%S"
	return fmt

client=mpd.MPDClient()
is_connected=False

def make_con():
 conn=False
 ps=0
 global is_connected
#  print(ps)
 while (conn==False and ps<5):
  try:
  #  print(addr, port, ps)
   client.connect(addr, port)
   conn=True
   is_connected=True
  #  print('connected')
  except:
   conn=False
  #  print('not connected', ps)
   ps+=1
   is_connected=False
   time.sleep(2)


def _check():
	print ('client.ping', client.ping())

tags1=[
"title",
"album", "artist","date", "time",

"genre",
"arranger", "author", "comment","composer","conductor",
"contact", "copyright", "description",  "performer", "grouping",
"language",
"license","location",
"lyricist","organization", "version",
"website", "albumartist",  "isrc","discsubtitle","part",
"discnumber", "tracknumber","labelid", "originaldate", "originalalbum",
"originalartist",
"recordingdate",
"releasecountry","performers",
"added",
"lastplayed", "disc", "discs","track", "tracks","laststarted", "filename",
"basename", "dirname", "mtime", "playcount", "skipcount", "uri", "mountpoint",

"length", "people", "rating",  "originalyear", "bookmark", "bitdepth",
"bitrate", "filesize","format", "codec", "encoding","playlists", "samplerate",
"channels","bpm",
]


class QMiniMPD(QMainWindow):

 def __init__(self):
  super().__init__()
  self.songs=[]
  # self.song_ptr=0
  # self.cur_handle=None
  self.timer=QtCore.QTimer()
  self.timer.timeout.connect(self.timer_func)
  self.timer.start()
  # status=client.status()['status']
  # if status=='pause' or status=='play':

  #~ self.statusBar().showMessage('Ready')
  self.setGeometry(50, 300, 500, 50)
  self.setWindowTitle('qmini_mpd')
  self.setWindowIcon(QIcon(self.style().standardIcon(getattr(QStyle, 'SP_MediaPlay'))))
  #~ self.setAcceptDrops(True)
  # Using a title
  a_rev = QAction(QIcon(self.style().standardIcon(getattr(QStyle, 'SP_MediaSeekBackward'))), 'Rewind', self)
  a_forw = QAction(QIcon(self.style().standardIcon(getattr(QStyle, 'SP_MediaSeekForward'))), 'Forward', self)
  a_stop = QAction(QIcon(self.style().standardIcon(getattr(QStyle, 'SP_MediaStop'))), 'Stop', self)
  """
  'SP_MediaPause',
  'SP_MediaPlay',
  """
  self.a_pause = QAction(QIcon(self.style().standardIcon(getattr(QStyle, 'SP_MediaPlay'))), 'Play/Pause', self)
  a_back = QAction(QIcon(self.style().standardIcon(getattr(QStyle, 'SP_MediaSkipBackward'))), 'Back', self)
  a_next = QAction(QIcon(self.style().standardIcon(getattr(QStyle, 'SP_MediaSkipForward'))), 'Next', self)

  a_stop.triggered.connect(self.pstop)
  self.a_pause.triggered.connect(self.ppause)
  a_rev.triggered.connect(self.skip_back)
  a_forw.triggered.connect(self.skip_fwd)
  a_back.triggered.connect(self.prev_song)
  a_next.triggered.connect(self.next_song)

  a_shuffle=QAction('Shuffle', self)
  a_repeat=QAction('Repeat', self)
  self.a_consume=QAction('Consume', self)
  self.a_consume.setCheckable(True)
  #exitAction.setShortcut('Ctrl+Q')
  #exitAction.triggered.connect(qApp.quit)

  #~ ptToolbar = self.addToolBar("play")
  ptToolbar=QToolBar("play")
  #ptToolbar.setIconSize(QtCore.QSize(16, 16))
  self.addToolBar(QtCore.Qt.BottomToolBarArea, ptToolbar)
  ptToolbar.addAction(a_rev)
  ptToolbar.addAction(a_forw)
  ptToolbar.addSeparator()
  ptToolbar.addAction(a_stop)
  ptToolbar.addAction(self.a_pause)
  ptToolbar.addSeparator()
  ptToolbar.addAction(a_back)
  ptToolbar.addAction(a_next)


  self.hscale=QSlider(QtCore.Qt.Horizontal)
  self.hscale.setTickInterval(10);
  self.hscale.setSingleStep(1);

  self.cLabel=QLabel('<b>00:00</b>')
  self.cLabel.setTextFormat(QtCore.Qt.RichText)
  self.aLabel=QLabel('/00:00')
  self.aLabel.setTextFormat(QtCore.Qt.RichText)
  ptToolbar.addSeparator()
  ptToolbar.addWidget(self.hscale)
  ptToolbar.addSeparator()
  ptToolbar.addWidget(self.cLabel)
  ptToolbar.addWidget(self.aLabel)
  #ptToolbar.addAction(a_shuffle)
  #ptToolbar.addAction(a_repeat)
  menuToolButton=QToolButton()
  # menuToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
  menuToolButton.setText('Menu ')
  #QAction(QIcon(self.style().standardIcon(getattr(QStyle, 'SP_DockWidgetCloseButton'))),
                               #'Options', self)
  menuToolButton.setPopupMode(QToolButton.InstantPopup)
  #menuToolButton.setArrowType(QtCore.Qt.DownArrow)
  ptToolbar.addWidget(menuToolButton)
  """a_openfile=QAction(QIcon(self.style().standardIcon(getattr(QStyle, 'SP_DialogOpenButton'))), 'Add file(s)', self)
  a_openfile.triggered.connect(self.add_files)
  a_openfolder=QAction(QIcon(self.style().standardIcon(getattr(QStyle, 'SP_DirOpenIcon'))), 'Add folder(s)', self)
  a_openfolder.triggered.connect(self.add_folders)"""
  oMenu=QMenu('Options')
  #oMenu.addAction(a_openfile)

  #oMenu.addAction(a_openfolder)
  #oMenu.addSeparator()
  oMenu.addAction(a_shuffle)
  oMenu.addAction(a_repeat)
  oMenu.addAction(self.a_consume)
  oMenu.addSeparator()

  a_connection=QAction('Connect', self)
  oMenu.addAction(a_connection)
  a_connection.triggered.connect(self.make_connect)


  """sMenu=oMenu.addMenu('Styles')
  sPlastic= QAction('Plastic', self)
  sMac=QAction('Mac', self)
  sWindows=QAction('Windows', self)
  sWindowsXP=QAction('Windows XP', self)
  sWindowsVista=QAction('Windows Vista', self)
  sCleanlooks=QAction('Cleanlooks', self)
  sMotif=QAction('Motif', self)
  sCustom=QAction('Cutsom style', self)
  sMenu.addAction(sPlastic)
  sMenu.addAction(sMac)
  sMenu.addAction(sWindows)
  sMenu.addAction(sWindowsXP)
  sMenu.addAction(sWindowsVista)
  sMenu.addAction(sCleanlooks)
  sMenu.addAction(sMotif)
  sMenu.addSeparator()
  sMenu.addAction(sCustom)"""
  menuToolButton.setMenu(oMenu)
  #sWindows.triggered.connect(self.set_style, 'Fusion')
  #sWindows.triggered.connect(lambda x:QApplication.setStyle(x), 'Fusion')
  self.repeat=False
  a_repeat.triggered.connect(lambda x: not x, self.repeat)
  self.random=False
  a_shuffle.triggered.connect(lambda x: not x, self.random)
  self.a_consume.triggered.connect(self.set_consume)
  

  #pShuffle=QCheckBox("Shuffle")
  #pRandom=QCheckBox("Random")
  #ptToolbar.addWidget(pShuffle)
  #ptToolbar.addWidget(pRandom)
  hbox=QVBoxLayout()
  #
  #a_openfile = QPushButton("Open file")
  #a_openfile.setIcon(QIcon())
  #a_openfile.resize(QtCore.QSize(16, 16))
  self.titl_label=QLabel('')
  self.titl_label.setTextFormat(QtCore.Qt.RichText)
  #hbox.addWidget(a_openfile)
  hbox.addWidget(self.titl_label)
  #
  """pList=QListView()
  self.pListModel=QStringListModel(self.songs)
  pList.setModel(self.pListModel)
  hbox.addWidget(pList)"""
  wdg = QWidget()
  wdg.setLayout(hbox);
  self.setCentralWidget(wdg)
  #~ sb=QStatusBar()
  #sb.setSizeGripEnabled(False)
  #~ self.setStatusBar(sb)
  self.show()
  self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
  self.destroyed.connect(self.on_destroy)
  self.a_lst=(a_back, a_forw, a_shuffle, a_stop, a_next, a_repeat, a_rev, self.a_pause)
  make_con()
  global is_connected
  pl_len=0
  if is_connected:
  #  print(0)
   status=client.status()
  #  print (status)
   pl_len=int(status['playlistlength'])
   cnm=status['consume']
   #~ print(cnm)
   self.a_consume.setChecked(cnm=='1')
  # elif not is_connected or pl_len>0:
    # self.set_enabled(a_lst, False)
  # else:
  self.set_enabled(self.a_lst, (is_connected and pl_len>0))
  self.set_enabled([self.a_consume], is_connected)


 def set_enabled(self, lst, what):
  # print (lst)
  for i in lst:
   i.setEnabled(what)
  
  #QApplication.setStyle('Macintosh')

 """def add_folders(self):
  folders=QFileDialog.getExistingDirectory(self, "Add folder(s)", "", QFileDialog.ShowDirsOnly)
  print(folders)"""

 """def add_files(self):
  #maskname=
  mask=""
  for n in formats:
   mask+=str(n)+";"
  mask+=";"
  for n in formats:
   mask+=str(n)+";;"
  files= QFileDialog.getOpenFileNames(self, "Add file(s)", "", mask)
  print(files)
  for i in files:
   if (os.path.isdir(i)):
    self.add_from_dir(i)
   else:
    self.add_file_to_list(i)"""

 def set_style(self, style):
  QApplication.setStyle(QStyleFactory.create(style))

 def make_connect(self, event=0):
  global is_connected
  if is_connected:
    return True
  make_con()
  if is_connected:
   st=client.status()
   cnm=st['consume']
   s=st['stat']
  #  print(cnm)
   self.a_consume.setChecked(cnm=='1')
   """if s=='pause' or s=='stop':
    s.a_pause.setIcon(QIcon(s.style().standardIcon(getattr(QStyle, 'SP_MediaPlay'))))
   else:
    s.a_pause.setIcon(QIcon(s.style().standardIcon(getattr(QStyle, 'SP_MediaPause'))))"""

 def set_consume(self, event=0):
  s=client.status()['consume']
  self.a_consume.setChecked(s=='0')
  if s=='0':
    client.consume('1')
  else:
    client.consume('0')


  #~ print(client.status()) 

 @staticmethod
 def on_destroy(self):
  print(self.parent())
  p= QtCore.QPoint()
  self.mapToGlobal(p)
  if not os.path.exists(configdir):
   os.makedirs(configdir)
  if not config.has_section("main"):
   config.add_section("main")
  config.set('main', 'y', str(p.y()))
  config.set('main', 'x', str(p.x()))
  #config.set('main', 'randon', str(self.random))
  #config.set('main', 'repeat', str(self.repeat))
  with open(configname, 'w') as configfile:
   config.write(configfile)


 def timer_func(self):
  global is_connected
  if not is_connected: return True
  try:
   clst=client.status()
   pl_len=int(clst['playlistlength'])
   self.set_enabled(self.a_lst, pl_len>0)
   cst=clst['state']
   if cst=='stop':
    return True
  # print(status)
   if 'time' in clst:
    self.hscale.setMaximum(int(clst['time'].split(':')[1]))

   if cst=='play' or  cst=='pause':
    ttm=clst['time']
    ttm=ttm.split(":")
			
    t1=time.strftime(date_fmt(float(ttm[0])), time.gmtime(float(ttm[0])))
    t2=time.strftime(date_fmt(float(ttm[1])), time.gmtime(float(ttm[1])))
    self.hscale.setValue(int(ttm[0]))

    self.cLabel.setText(t1)
    self.aLabel.setText("/%s"%t2)
    csong=client.currentsong()
    cba=getrecords(csong)
    self.titl_label.setText("<b>%s</b> :: <i>%s</i> :: %s (%s)"%(cba[0], cba[2], cba[1], cba[3]))

   csong=client.currentsong()
   tt=csong['title']
   return True
  except:
    return True

 def prev_song(self, w=None):
  print('prev_song')
  client.previous()

 def next_song(self, w=None):
  client.next()

 def ppause(s,  e):
  status=client.status()['state']
  if status=='play':
   client.pause()
   s.a_pause.setIcon(QIcon(s.style().standardIcon(getattr(QStyle, 'SP_MediaPlay'))))
  elif status=='pause' or status=='stop':
   client.play()
   s.a_pause.setIcon(QIcon(s.style().standardIcon(getattr(QStyle, 'SP_MediaPause'))))
  s.timer.start()

   


 def pstop(s,  e=0):
   client.stop()
   s.a_pause.setIcon(QIcon(s.style().standardIcon(getattr(QStyle, 'SP_MediaPlay'))))
   s.titl_label.setText('')
   s.aLabel.setText('/00:00')
   s.cLabel.setText('<b>00:00</b>')
   s.timer.stop()
   s.hscale.setValue(0)

 def skip_fwd(self, w=None):
  self.skip('+20')
  pass
 def skip_back(self, w=None):
  self.skip('-20')
  pass

 def skip(self, sec):
  status=client.status()['state']
  if status=='stop':
   return
  client.seekcur(sec)





 """def playfile(s, f):
  print('playfile')
  status=client.status()['state']
  if status=='pause' or status=='stop':
   client.play()
   s.a_pause.setIcon(QIcon(s.style().standardIcon(getattr(QStyle, 'SP_MediaPause'))))
  elif status=='play':
   client.pause()
   s.a_pause.setIcon(QIcon(s.style().standardIcon(getattr(QStyle, 'SP_MediaPlay'))))"""





if __name__ == '__main__':
  #~ BASS_Init(-1, 44100,0, 0,0)
  # ~ print BASS_PluginLoad("libtags.so", 0)
  #~ LoadPlugins()
  #print (plugins)
  #print (BASS_GetVersion())
  # make_con()
  # _check()
  app = QApplication(sys.argv)
  ex = QMiniMPD()
  # client.ping()
  #w = QWidget()
  #w.resize(250, 150)
  #w.move(300, 300)
  #w.setWindowTitle('Simple')
  #w.show()

  sys.exit(app.exec())
