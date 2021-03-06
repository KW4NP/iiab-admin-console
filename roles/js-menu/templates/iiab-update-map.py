#!/usr/bin/env python
# Scan the osm-vector-maps directory, update the vector-map-idx.json, add menu-defs

from geojson import Feature, Point, FeatureCollection, Polygon
import geojson
import json
import os
import sys
import fnmatch
import subprocess
import re

IIAB_PATH='/etc/iiab'
if not IIAB_PATH in sys.path:
    sys.path.append(IIAB_PATH)
from iiab_env import get_iiab_env

#SCRIPT_DIR = '/opt/admin/cmdsrv/scripts'
SCRIPT_DIR = '{{ cmdsrv_dir }}/scripts'
if not SCRIPT_DIR in sys.path:
    sys.path.append(SCRIPT_DIR)
if os.path.exists(os.path.join(SCRIPT_DIR,'iiab_update_menus.py')):
   import iiab_update_menus as menus

doc_root = get_iiab_env('WWWROOT')
menuDefs = doc_root + "/js-menu/menu-files/menu-defs/"
vector_map_idx_dir = doc_root + "/common/assets"
map_doc_root = '{{ vector_map_path }}'
iiab_map_url = '(( iiab_map_url }}'
#map_doc_root = '/library/www/osm-vector-maps'
# map_catalog will be global, assumed always available
map_catalog = {}
map_menu_def_list = []

def main():
   global map_menu_def_list
   get_newest_osm_catalog()
   get_map_catalog()
   #print(json.dumps(map_catalog,indent=2))
   
   map_menu_def_list = get_menu_def_names()
   #print(json.dumps(map_menu_def_list,indent=2))

   installed_maps = get_installed_regions()
   #print(installed_maps)

   write_vector_map_idx(installed_maps)

   # For installed regions, check that a menu def exists, and it's on home page
   for fname in installed_maps:
      region = extract_region_from_filename(fname)
      #print('checking for %s region'%region)
      if region == 'maplist': # it is the splash page, display only if no others
         menu_ref = 'en-test_map'
         if len(installed_maps) == 1:
            menus.update_menu_json(menu_ref)
            return
      else:
          item = map_catalog['regions'][region]
          menu_ref = item['perma_ref']
          if not (region in map_menu_def_list):
             #print('creating menu def for %s'%item['perma_ref'])
             create_menu_def(region,item['perma_ref'] + '.json')
      if fetch_menu_json_value('autoupdate_menu'):
         #print('autoudate of menu items is enabled:%s. Adding %s'%(\
                    #fetch_menu_json_value('autoupdate_menu'),region,))
         # verify this menu def is on home page
         menus.update_menu_json(menu_ref)

def get_newest_osm_catalog():
   cmd = 'wget -P ' +map_doc_root + '/maplist/assets/' + \
                  '{{ iiab_map_url }}/assets/regions.json'
   subprocess.call(cmd,shell=True)

def get_map_catalog():
   global map_catalog
   input_json = map_doc_root + '/maplist/assets/regions.json'
   with open(input_json,'r') as regions:
      reg_str = regions.read()
      map_catalog = json.loads(reg_str)
   #print(json.dumps(map_catalog,indent=2))

def get_menu_def_names(intended_use='map'):
   menu_def_list =[] 
   os.chdir(menuDefs)
   for filename in os.listdir('.'):
      if fnmatch.fnmatch(filename, '*.json'):
         try:
            with open(filename,'r') as json_file:
                readstr = json_file.read()
                data = json.loads(readstr)
         except:
            print("failed to parse %s"%filename)
            print(readstr)
         if data.get('intended_use','') != intended_use:
            continue
         map_name = data.get('name','')
         if map_name != '':
            menu_def_list.append(data['name'])
   return menu_def_list

def get_installed_regions():
   installed = []
   os.chdir(map_doc_root)
   for filename in os.listdir('.'):
      if fnmatch.fnmatch(filename, '??-osm-omt*'):
         region = re.sub(r'^..-osm-omt_(.*)',r'\1',filename)
         installed.append(region)
   # add the splash page if no other maps are present
   if len(installed) == 0:
         installed.append('maplist')
   return installed

def write_vector_map_idx(installed_maps):
   map_dict ={} 
   idx_dict = {}
   for fname in installed_maps:
      region = extract_region_from_filename(fname)
      if map == 'maplist': continue # not a real region
      map_dict = map_catalog['regions'].get(region,'')
      if map_dict == '': continue

      # Create the idx file in format required bo js-menu system
      item = map_dict['perma_ref']
      idx_dict[item] = {} 
      idx_dict[item]['file_name'] = os.path.basename(map_dict['url'][:-4])
      idx_dict[item]['menu_item'] = map_dict['perma_ref']
      idx_dict[item]['size'] = map_dict['size']
      idx_dict[item]['date'] = map_dict['date']
      idx_dict[item]['region'] = region
      idx_dict[item]['language'] = map_dict['perma_ref'][:2]

   with open(vector_map_idx_dir + '/osm_version_idx.json','w') as idx:
      idx.write(json.dumps(idx_dict,indent=2)) 

def create_menu_def(region,default_name,intended_use='map'):
   item = map_catalog['regions'][region]
   if len(item.get('language','')) > 2:
     lang = item['language'][:2]
   else: # default to english
     lang = 'en'
   filename = lang + '-' + item['perma_ref'] + '.json'
   # create a stub for this zim
   menuDef = {}
   default_logo = 'osm.jpg'
   menuDef["intended_use"] = "map"
   menuDef["lang"] = lang
   menuDef["logo_url"] = default_logo
   menuitem = lang + '-' + item['perma_ref']
   menuDef["menu_item_name"] = default_name
   menuDef["title"] = "OpenStreetMap: 18 Levels of Zoom for <b> " + item.get('title','ERROR') + '</b>'
   menuDef["map_name"] = item['perma_ref']
   menuDef["file_name"] = lang + '-osm-omt_' + region + '_' + \
                      os.path.basename(item['url'])[:-4]
   menuDef["description"] = '<p>Resolution of the Whole World to 5 KM. OpenStreetMap data for <b>' + item.get('title','') + '</b> with details down to 5 Meters</p>'
   menuDef["extra_html"] = ""
   menuDef["automatically_generated"] = "true"
   if not os.path.isfile(menuDefs + default_name): # logic to here can still overwrite existing menu def
       print("creating %s"%menuDefs + default_name)
       with open(menuDefs + default_name,'w') as menufile:
          menufile.write(json.dumps(menuDef,indent=2))
   return default_name[:-5]

def human_readable(num):
    # return 3 significant digits and unit specifier
    num = float(num)
    units = [ '','K','M','G']
    for i in range(4):
        if num<10.0:
            return "%.2f%s"%(num,units[i])
        if num<100.0:
            return "%.1f%s"%(num,units[i])
        if num < 1000.0:
            return "%.0f%s"%(num,units[i])
        num /= 1000.0

def fetch_menu_json_value(key):
   with open( doc_root + '/home/menu.json','r') as menudef:
      data = json.loads(menudef.read())
      return data.get(key,'')

def extract_region_from_filename(fname):
   nibble = re.search(r"^.*omt_(.*)_[0-9]{4}",fname)
   if not nibble:
      return("maplist")
   resp = nibble.group(1)
   return(resp)
      
if __name__ == '__main__':
   if os.path.isdir(map_doc_root):
      main()
