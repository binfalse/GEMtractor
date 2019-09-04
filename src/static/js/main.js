/* js */
// Used to toggle the menu on small screens when clicking on the menu button
function myFunction() {
  var x = document.getElementById("navMobi");
  if (x.className.indexOf("w3-show") == -1) {
    x.className += " w3-show";
  } else { 
    x.className = x.className.replace(" w3-show", "");
  }
}
function tab(tabid, tabbuttonid) {
  var t = $("#" + tabid);
  t.parent ().children ().hide ();
  t.show ();
  
  t = $("#" + tabbuttonid);
  t.parent ().children ().removeClass ("w3-flat-clouds");
  t.addClass ("w3-flat-clouds");
}

const idMap = {};
const idReMap = {};

function domIdMapper (str) {
  var id = str.replace(/[\W_]+/g,"_");
  while (id in idReMap)
    id = id + Math.floor((Math.random() * 10) + 1);
  idMap[str] = id;
  idReMap[id] = str;
  return id;
}

var networks = {
  original: {}
}


function storeFilters (s, r, g) {
  $.ajax({
    method: "POST",
    headers: {"X-CSRFToken": token},
        url: '/api/store_filter',
        dataType: 'json',
        data: JSON.stringify({
          species: s,
          reaction: r,
          genes: g
          }),
        success: function (data) {
          
          if (data.status != 'success') {
            $("#filtercontainer").hide ();
            $("#loading").hide ();
            $("#error").show ().text ("Failed to update the filters: " + data.error);
            return;
          }
          console.log (data);
          
          $("#filtercontainer").show ();
          $("#loading").hide ();
          $("#error").hide ();
        },
        error: function (jqXHR, textStatus, errorThrown) {
          $("#filtercontainer").hide ();
          $("#loading").hide ();
          $("#error").show ().text ("Failed to update the filters: " + errorThrown);
        }
      });
}

function updateNetwork () {
  
  $("#species-table tr").removeClass ("filter-inconsistent").removeClass ("filter-excluded");
  $("#reaction-table tr").removeClass ("filter-inconsistent").removeClass ("filter-excluded");
  $("#gene-table tr").removeClass ("filter-inconsistent").removeClass ("filter-excluded");
  
  var inconsistent = [new Set(),new Set(),new Set()]
  filter_species = new Set();
  filter_reaction = new Set();
  filter_genes = new Set();
  
  console.log (idReMap);
  
  $("#species-table input[type=checkbox]").each (function (item){
    if (!$(this).prop("checked")) {
      const domId=$(this).parent ().parent ().attr ("id");
      const entId = idReMap[domId];
      console.log (domId);
      console.log (entId);
      $("#" + domId).addClass ("filter-excluded");
      filter_species.add (entId);
      networks.original.species[entId].occurence.forEach (function (r) {
        $("#" + idMap[r]).addClass ("filter-inconsistent");
        inconsistent[1].add (r);
      });
    }
  });
  
  $("#reaction-table input[type=checkbox]").each (function (item){
    if (!$(this).prop("checked")) {
      const domId=$(this).parent ().parent ().attr ("id");
      const entId = idReMap[domId];
      $("#" + domId).addClass ("filter-excluded");
      filter_reaction.add (entId);
    }
  });
  
  $("#gene-table input[type=checkbox]").each (function (item){
    if (!$(this).prop("checked")) {
      const domId=$(this).parent ().parent ().attr ("id");
      const entId = idReMap[domId];
      $("#" + domId).addClass ("filter-excluded");
      filter_genes.add (entId);
    }
  });
  
  
  for (var key in networks.original.reactions) {
   if (networks.original.reactions.hasOwnProperty(key)) {
     const item = networks.original.reactions[key];
     var occ = item.genes.some (function (r) {
       return !filter_genes.has (r);
     });
     if (!occ) {
        $("#" + item.DOM).addClass ("filter-inconsistent");
        inconsistent[1].add (key);
     }
   }};
  
  
  for (var key in networks.original.species) {
   if (networks.original.species.hasOwnProperty(key)) {
     const item = networks.original.species[key];
     var occ = item.occurence.some (function (r) {
       return !filter_reaction.has (r);
     });
     if (!occ) {
        $("#" + item.DOM).addClass ("filter-inconsistent");
        inconsistent[0].add (key);
     }
   }};
   
   for (var key in networks.original.genenet) {
   if (networks.original.genenet.hasOwnProperty(key)) {
     const item = networks.original.genenet[key];
     var occ = item.reactions.some (function (r) {
       //console.log (r)
       return !filter_reaction.has (r);
     });
     if (!occ) {
        $("#" + item.DOM).addClass ("filter-inconsistent");
        inconsistent[2].add (key);
     }
   }}
  
  
  filter_reaction.forEach (function (item) {inconsistent[1].delete (item)});
  filter_species.forEach (function (item) {inconsistent[0].delete (item)});
  filter_genes.forEach (function (item) {inconsistent[2].delete (item)});
  
    $("#s_inconsistent").text (inconsistent[0].size);
    $("#r_inconsistent").text (inconsistent[1].size);
    $("#g_inconsistent").text (inconsistent[2].size);


    $("#s_cur").text (Object.keys(networks.original.species).length - filter_species.size);
    $("#r_cur").text (Object.keys(networks.original.reactions).length - filter_reaction.size);
    $("#g_cur").text (Object.keys(networks.original.genenet).length - filter_genes.size);
    
    
    const s = Array.from(filter_species)
    const r = Array.from(filter_reaction)
    const g = Array.from(filter_genes)
    
    var batch = "species: " + s.join (", ") + "\nreactions: " + r.join (", ") + "\ngenes: " + g.join (", ");
    
    $("#batch-filter").text (batch);
    
    storeFilters (s, r, g);
}

function truncate (str) {
  length = 40;
  ending = "..."
  if (str.length > length) {
    return str.substring(0, length - ending.length) + ending;
  }
  return  str;
}

function draw_network_table (filter) {
  
  for (var key in networks.original.species) {
   if (networks.original.species.hasOwnProperty(key)) {
     const item = networks.original.species[key];
     item.DOM = domIdMapper (item.identifier);
     var checked = filter["filter_species"].includes(key) ? "" : " checked";
    const row = $("<tr id='"+item.DOM+"'><td class='check'><input type='checkbox'"+checked+"></td><td><abbr title='"+item.identifier+"'>"+truncate (item.identifier)+"</abbr></td><td><abbr title='"+item.name+"'>"+truncate (item.name)+"</abbr></td><td title='occurs in "+item.occurence.join (", ")+"'>"+item.occurence.length+"</td></tr>");
    $('#species-table').append(row);
  }};
  
  for (var key in networks.original.reactions) {
   if (networks.original.reactions.hasOwnProperty(key)) {
     const item = networks.original.reactions[key];
     item.DOM = domIdMapper (item.identifier);
     var checked = filter["filter_reactions"].includes(key) ? "" : " checked";
    const row = $("<tr id='"+item.DOM+"'><td class='check'><input type='checkbox'"+checked+"></td><td><abbr title='"+item.identifier+"'>"+truncate (item.identifier)+"</abbr></td><td><abbr title='"+item.name+"'>"+truncate (item.name)+"</abbr></td><td><small>"+item.consumed.join (" + ") + "</small> <i class='fas fa-arrow-right'></i> <small>" + item.produced.join (" + ") +"</small></td><td><small>"+item.genes.join ("</small> [OR] <small>") +"</small></td></tr>");
    $('#reaction-table').append(row);
  }};
  
  for (var key in networks.original.genenet) {
   if (networks.original.genenet.hasOwnProperty(key)) {
     const item = networks.original.genenet[key];
     item.DOM = domIdMapper (key);
     var checked = filter["filter_genes"].includes(key) ? "" : " checked";
     const row = $("<tr id='"+item.DOM+"'><td class='check'><input type='checkbox'"+checked+"></td><td title='occurs in "+networks.original.genenet[key].reactions.join (", ")+"'>"+key+"</td></tr>");
    $('#gene-table').append(row);
   }
 }
 
 
  
  $("#filter-tables input[type=checkbox]").change (updateNetwork);
  
  
  prepareTableSorting ();
  
  
}

function prepareTableSorting () {
  
  // prepare tables
  function comparer(index) {
      return function(a, b) {
          var valA = getCellValue(a, index), valB = getCellValue(b, index)
          return $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.toString().localeCompare(valB)
      }
  }
  function getCellValue(row, index){
    var td = $(row).children('td').eq(index);
    if (td.hasClass ("check"))
      return td.find ("input[type=checkbox]").first ().prop("checked") == true;
    return td.text()
    }
  $('.sortable th').click(function(){
    $('.sortable th .sortsymbol').remove ();
    var asc = !$( this ).hasClass ("sorted-asc");
    $('.sortable th').removeClass ("sorted-desc");
    $('.sortable th').removeClass ("sorted-asc");
    
    
    var table = $(this).parents('table').eq(0)
    var rows = table.find('tr:gt(0)').toArray().sort(comparer($(this).index()))
    
    if (asc) {
      $(this).addClass ("sorted-asc").append (" <i class='fas fa-sort-up sortsymbol'></i>");
    }
    else {
      $(this).addClass ("sorted-desc").append (" <i class='fas fa-sort-down sortsymbol'></i>");
      rows = rows.reverse()
    }
    
    for (var i = 0; i < rows.length; i++){table.append(rows[i])}
  });
  $('.sortable th').eq(0).click ();
  $('.sortable.notfirst th').eq(1).click ();
}

function loadNetwork () {
          $("#error").hide ();
  $.ajax({
        url: '/api/get_network',
        dataType: 'json',
        success: function (data) {
          
          if (data.status != 'success') {
            $("#filtercontainer").hide ();
            $("#loading").hide ();
            $("#error").show ().text ("Failed to retrieve the network: " + data.error);
            return;
          }
          console.log (data);
          
          $("#s_org").text (Object.keys(data.network.species).length);
          $("#r_org").text (Object.keys(data.network.reactions).length);
          $("#g_org").text (Object.keys(data.network.genenet).length);
          networks.original = data.network
          
          $("#filtercontainer").show ();
          $("#loading").hide ();
          $("#error").hide ();
          
          draw_network_table (data.filter);
          updateNetwork ();
        },
        error: function (jqXHR, textStatus, errorThrown) {
          $("#filtercontainer").hide ();
          $("#loading").hide ();
          $("#error").show ().text ("Failed to retrieve the network: " + errorThrown + " (" + textStatus + ")");
        }
      });
}

function prepareExport () {
  var enzyme_option = 'en';
  $("#" + network_type_id + " option").each (function () {
    //if ($(this).)
    if ($(this).text().toLowerCase().includes("enzyme")) {
    enzyme_option = $(this).val()
  }
  })
  
  $("#" + network_type_id).change (function () {
    if ($("#" + network_type_id).val () == enzyme_option) {
      $("#" + remove_reaction_genes_removed_id).prop ("checked", true)
      $("#" + remove_reaction_genes_removed_id).prop ("disabled", true)
    } else {
      $("#" + remove_reaction_genes_removed_id).prop ("disabled", false)
    }
    
  });
  $("#" + network_type_id).change ();
  
  
}



function prepareIndex () {
  
          $("#error").hide ();
          
  $.ajax({
        url: '/api/get_bigg_models',
        dataType: 'json',
        success: function (data) {
          
          if (data.status != 'success') {
            //$("#filtercontainer").hide ();
            //$("#loading").hide ();
            $("#error").show ().text ("Failed to obtain BiGG models: " + data.error);
            return;
          }
          //console.log (data);
          
          
          
  for (var model of data.results) {
    //console.log (model);
     model.DOM = domIdMapper (model.bigg_id);
    const row = $("<tr id='"+model.DOM+"'><td><a class='bigg_id'>"+model.bigg_id+"</a></td><td>"+model.organism+"</td><td>"+model.metabolite_count+"</td><td>"+model.reaction_count+"</td><td>"+model.gene_count+"</td></tr>");
    $('#bigg-table').append(row);
  };
  $('.bigg_id').click (function () {
    //console.log ($(this).text ());
    const modelid = $(this).text ();
    $(this).html ("<i class='fa fa-spinner w3-spin'></i> loading model")
  $.ajax({
        url: '/api/select_bigg_model',
        dataType: 'json',
    method: "POST",
    headers: {"X-CSRFToken": token},
        data: JSON.stringify({
          bigg_id: modelid
          }),
        success: function (data) {
          
          if (data.status != 'success') {
            //$("#filtercontainer").hide ();
            //$("#loading").hide ();
            $("#error").show ().text ("Failed to select BiGG model: " + data.error);
            return;
          }
          window.location = filter_url;
        },
        error: function (jqXHR, textStatus, errorThrown) {
          $("#error").show ().text ("Failed to obtain BiGG models: " + errorThrown);
        }
      });
  });
          
          
          //$("#s_org").text (Object.keys(data.network.species).length);
          //$("#r_org").text (Object.keys(data.network.reactions).length);
          //$("#g_org").text (Object.keys(data.network.genenet).length);
          //networks.original = data.network
          
          //$("#filtercontainer").show ();
          //$("#loading").hide ();
          $("#bigg_loading").hide ();
          $("#choose-bigg table").show ();
          //draw_network_table (data.filter);
          //updateNetwork ();
  prepareTableSorting ();
        },
        error: function (jqXHR, textStatus, errorThrown) {
          //$("#filtercontainer").hide ();
          //$("#loading").hide ();
          $("#bigg_loading").hide ();
          $("#choose-bigg table").hide ();
          $("#error").show ().text ("Failed to obtain BiGG models: " + errorThrown);
        }
      });
      
      
      
      
          
  $.ajax({
        url: '/api/get_biomodels',
        dataType: 'json',
        success: function (data) {
          
          if (data.status != 'success') {
            //$("#filtercontainer").hide ();
            //$("#loading").hide ();
            $("#error").show ().text ("Failed to obtain Biomodels: " + data.error);
            return;
          }
          console.log (data);
          
          
          
  for (var model of data.models) {
    //console.log (model["id"]);
     model.DOM = domIdMapper (model.id);
     
    const row = $("<tr id='"+model.DOM+"'><td><a class='biomodels_id'>"+model.id+"</a></td><td>"+model.name+"</td></tr>");
    $('#biomodels-table').append(row);
  }
  
  $('.biomodels_id').click (function () {
    //console.log ($(this).text ());
    const modelid = $(this).text ();
    $(this).html ("<i class='fa fa-spinner w3-spin'></i> loading model")
  $.ajax({
        url: '/api/select_biomodel',
        dataType: 'json',
    method: "POST",
    headers: {"X-CSRFToken": token},
        data: JSON.stringify({
          biomodels_id: modelid
          }),
        success: function (data) {
          
          if (data.status != 'success') {
            //$("#filtercontainer").hide ();
            //$("#loading").hide ();
            $("#error").show ().text ("Failed to select Biomodel: " + data.error);
            return;
          }
          window.location = filter_url;
        },
        error: function (jqXHR, textStatus, errorThrown) {
          $("#error").show ().text ("Failed to obtain Biomodel: " + errorThrown);
        }
      });
  });
          
          
          $("#biomodels_loading").hide ();
          $("#choose-biomodels table").show ();
  prepareTableSorting ();
        },
        error: function (jqXHR, textStatus, errorThrown) {
          //$("#filtercontainer").hide ();
          //$("#loading").hide ();
          $("#biomodels_loading").hide ();
          $("#choose-biomodels table").hide ();
          $("#error").show ().text ("Failed to obtain Biomodels: " + errorThrown);
        }
      });
          
}

