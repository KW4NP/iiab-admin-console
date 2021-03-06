// map_functions.js
// copyright 2019 George Hunt

var regionGeojson = {};
var regionList = [];
var regionInstalled = [];
var commonAssetsDir = '/common/assets/';
var mapAssetsDir = '/osm-vector-maps/maplist/assets/';
var iiab_config_dir = '/etc/iiab/';
var onChangeFunc = "setSize";

// following 2 lines an experiment to see if test page and console can be common
//var jquery = require("./assets/jquery.min");
//window.$ = window.jQuery = jquery;

function getMapStat(){
  // called during the init
  console.log('in getMapStat');
  readMapCatalog( true ); // we want checkboxes
  readMapIdx();
}

function readMapIdx(){
	//consoleLog ("in readMapIdx");
  var resp = $.ajax({
    type: 'GET',
    url: consoleJsonDir + 'vector-map-idx.json',
    dataType: 'json'
  })
  .done(function( data ) {
  	mapInstalled = data['regions'];
   regionInstalled = [];
   for (region in data['regions']) {
    if (data['regions'].hasOwnProperty(region)) {
        regionInstalled.push(region);
    }
}
    //consoleLog(mapInstalled + '');
  })
  .fail(jsonErrhandler);

  return resp;
}

function readMapCatalog(checkbox){
   checkbox = checkbox || true;
	console.log ("in readMapCalalog");
   regionList = [];
  var resp = $.ajax({
    type: 'GET',
    url: mapAssetsDir + 'regions.json',
    dataType: 'json'
  })
  .done(function( data ) {
  	 regionJson = data;
    mapCatalog = regionJson['regions'];
    for(var key in mapCatalog){
      //console.log(key + '  ' + mapCatalog[key]['title']);
      mapCatalog[key]['name'] = key;
      regionList.push(mapCatalog[key]);
    }
  })
  .fail(jsonErrhandler);
  return resp;
}

function renderRegionList(checkbox) { // generic
	var html = "";
   // order the regionList by seq number
   var regions = regionList;
	console.log ("in renderRegionList");

	// sort on basis of seq
  regions = regions.sort(function(a,b){
    if (a.seq < b.seq) return -1;
    else return 1;
    });
  //console.log(regions);
	// render each region
   html += '<form>';
	regions.forEach((region, index) => { // now render the html
      //console.log(region.title + " " +region.seq);
      html += genRegionItem(region,checkbox);
  });
  html += '</form>';
  //console.log(html);
  $( "#regionlist" ).html(html);
}


function genRegionItem(region,checkbox) {
  var html = "";
  console.log("in genRegionItem: " + region.name);
  var itemId = region.title;
  var ksize = region.size / 1000;
  //console.log(html);
  html += '<div class="extract" data-region={"name":"' + region.name + '"}> ';
  html += '<label>';
  if ( checkbox ) {
    if (selectedMapItems.indexOf(region.name) != -1)
      checked = 'checked';
    else
      checked = '';
      html += '<input type="checkbox" name="' + region.name + '"';
      html += ' onChange="updateMapSpace(this)" ' + checked + '> ';
  }
  html += itemId;
  if ( checkbox ) { html += '</input>';};
  html += '</label>'; // end input
  html += ' ' + readableSize(ksize);
  html += '</div>';
  //console.log(html);

  return html;
}

function instMapItem(name) {
  var command = "INST-OSM-VECT-SET";
  var cmd_args = {};
  cmd_args['map_vect_id'] = name;
  cmd = command + " " + JSON.stringify(cmd_args);
  sendCmdSrvCmd(cmd, genericCmdHandler);
  mapDownloading.push(name);
  if ( mapWip.indexOf(name) != -1 )
     mapWip.push(mapCatalog[name]);
  console.log('mapWip: ' + mapWip);
  return true;
}

function updateMapSpace(cb){
  console.log("in updateMapSpace" + cb);
  var region = cb.name;
  updateMapSpaceUtil(region, cb.checked);
}

function updateMapSpaceUtil(region, checked){
  var size =  parseInt(mapCatalog[region].size);

  var modIdx = selectedMapItems.indexOf(region);

  if (checked){
    if (regionInstalled.indexOf(region) == -1){ // only update if not already installed mods
      sysStorage.map_selected_size += size;
      selectedMapItems.push(region);
    }
  }
  else {
    if (modIdx != -1){
      sysStorage.map_selected_size -= size;
      selectedMapItems.splice(modIdx, 1);
    }
  }

  displaySpaceAvail();
}

/*
function totalSpace(){
  // obsolete but perhaps useful in debugging since it worked
  var sum = 0;
  $( ".extract" ).each(function(ind,elem){
    var data = JSON.parse($(this).attr('data-region'));
    var region = data.name;
    var size = parseInt(mapCatalog[region]['size']);
    var chk = $( this ).find(':checkbox').prop("checked") == true;
    if (chk && typeof size !== 'undefined')
        sum += size;
    });
   var ksize = sum / 1000;
  $( "#mapDiskSpace" ).html(readableSize(ksize));
}

$( '#instMapRegion').on('click', function(evnt){
   readMapCatalog();
   map.render();
});
*/
function renderMap(){
   console.log('in renderMap');
   window.map.setTarget($("#map-container")[0]);
   window.map.render();
   renderRegionList(true);
}
function initMap(){
   var url =  mapAssetsDir + 'regions.json';
   if (UrlExists(url)){
      sysStorage.map_selected_size = 0;
      $.when(readMapCatalog(true)).then(renderRegionList);
   }
}
function UrlExists(url)
{
    var http = new XMLHttpRequest();
    http.open('HEAD', url, false);
    http.send();
    return http.status!=404;
}
