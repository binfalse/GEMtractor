/*
 * This file is part of the enalyzer
 * Copyright (C) 2019 Martin Scharm <https://binfalse.de>
 * 
 * The enalyzer is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * The enalyzer is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

/**
 * 
 * toggleNaviMobile -- toggle the navigation menu on small screens
 * 
 */
function toggleNaviMobile() {
	var x = document.getElementById("navMobi");
		if (x.className.indexOf("w3-show") == -1) {
		x.className += " w3-show";
	} else {
		x.className = x.className.replace(" w3-show", "");
	}
}

/**
 * 
 * tab -- switch the visible panel in tabbed areas
 * @param tabid	the id of the div to show
 * @param tabbuttonid the id of the button that selects the tab (will be highlighted)
 * 
 */
function tab(tabid, tabbuttonid) {
	var t = $("#" + tabid);
	t.parent ().children ().hide ();
	t.show ();

	t = $("#" + tabbuttonid);
	t.parent ().children ().removeClass ("w3-flat-clouds");
	t.addClass ("w3-flat-clouds");
}


// START remapping of element ids
// as some elements may be identified by keys, that are not valid xml identifiers
// we need to remap the id to something that is for sure valid in XML and still resolvable to the original ids..
const idMap = {};
const idReMap = {};

/**
 * 
 * domIdMapper -- creates a valid DOM id based on an entity's id
 * @param str the entity's id
 * @return the DOM id
 * 
 */
function domIdMapper (str) {
	var id = str.replace(/[\W_]+/g,"_");
	while (id in idReMap)
		id = id + Math.floor((Math.random() * 10) + 1);
	idMap[str] = id;
	idReMap[id] = str;
	return id;
}
// STOP remapping of element ids


var networks = {
  original: {}
}

/**
 * storeFilters -- store the currently applied filters
 * 
 * @param s list of species' ids to discard
 * @param r list of reactions' ids to discard
 * @param g list of genes' ids to discard
 * 
 */
function storeFilters (s, r, g, successFn = undefined) {
	// send an ajax request to /api/store_filter
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
				// got something, but was it successful?
				$("#filtercontainer").hide ();
				$("#loading").hide ();
				$("#error").show ().text ("Failed to update the filters: " + data.error);
				return;
		  }
		  
		  $("#filtercontainer").show ();
		  $("#loading").hide ();
		  $("#error").hide ();
		  
		  if (successFn)
				successFn ();
		},
		error: function (jqXHR, textStatus, errorThrown) {
		  $("#filtercontainer").hide ();
		  $("#loading").hide ();
		  $("#error").show ().text ("Failed to update the filters: " + errorThrown);
		}
	});
}


/*
 * 
 * updateNetwork -- evaluate the filtered species, find inconsistencies, recompute network tables, and store the filters
 * 
 */

function updateNetwork () {
	// reset filer-classes
	$("#species-table tr").removeClass ("filter-inconsistent").removeClass ("filter-excluded");
	$("#reaction-table tr").removeClass ("filter-inconsistent").removeClass ("filter-excluded");
	$("#gene-table tr").removeClass ("filter-inconsistent").removeClass ("filter-excluded");

	// prepare inconsistency sets
	var inconsistent = [new Set(),new Set(),new Set()];
	filter_species = new Set();
	filter_reaction = new Set();
	filter_genes = new Set();

	// check species for deselection
	$("#species-table input[type=checkbox]").each (function (item){
		if (!$(this).prop("checked")) {
			const domId=$(this).parent ().parent ().attr ("id");
			const entId = idReMap[domId];
			// if unchecked, fade it out
			$("#" + domId).addClass ("filter-excluded");
			filter_species.add (entId);
			networks.original.species[entId].occurence.forEach (function (r) {
				// mark reactions, in which this species appears, as inconsistent
				$("#" + idMap[r]).addClass ("filter-inconsistent");
				inconsistent[1].add (r);
			});
		}
	});

	// check reactions for deselection
	$("#reaction-table input[type=checkbox]").each (function (item){
		if (!$(this).prop("checked")) {
			const domId=$(this).parent ().parent ().attr ("id");
			const entId = idReMap[domId];
			// if unchecked, fade it out
			$("#" + domId).addClass ("filter-excluded");
			filter_reaction.add (entId);
		}
	});

	// check genes for deselection
	$("#gene-table input[type=checkbox]").each (function (item){
		if (!$(this).prop("checked")) {
			const domId=$(this).parent ().parent ().attr ("id");
			const entId = idReMap[domId];
			// if unchecked, fade it out
			$("#" + domId).addClass ("filter-excluded");
			filter_genes.add (entId);
		}
	});

	// check reactions for missing genes
	for (var key in networks.original.reactions) {
		if (networks.original.reactions.hasOwnProperty(key)) {
			const item = networks.original.reactions[key];
			// is there some gene left in this reaction?
			var occ = item.genes.some (function (r) {
				return !filter_genes.has (r);
			});
			if (!occ) {
				// otherwise highlight it as inconsistent
				$("#" + item.DOM).addClass ("filter-inconsistent");
				inconsistent[1].add (key);
			}
		}
	};

	// check for ghost species - species that do not appear in any reaction
	for (var key in networks.original.species) {
		if (networks.original.species.hasOwnProperty(key)) {
			const item = networks.original.species[key];
			// does the species appear somewhere?
			var occ = item.occurence.some (function (r) {
				return !filter_reaction.has (r);
			});
			if (!occ) {
				// otherwise highlight it as inconsistent
				$("#" + item.DOM).addClass ("filter-inconsistent");
				inconsistent[0].add (key);
			}
		}
	};

	// check for ghost genes - genes that do not appear in any reaction
	for (var key in networks.original.genenet) {
		if (networks.original.genenet.hasOwnProperty(key)) {
			const item = networks.original.genenet[key];
			var occ = item.reactions.some (function (r) {
				// does the species appear somewhere?
				return !filter_reaction.has (r);
			});
			if (!occ) {
				// otherwise highlight it as inconsistent
				$("#" + item.DOM).addClass ("filter-inconsistent");
				inconsistent[2].add (key);
			}
		}
	}

	// post-process inconsistencies
	filter_reaction.forEach (function (item) {inconsistent[1].delete (item)});
	filter_species.forEach (function (item) {inconsistent[0].delete (item)});
	filter_genes.forEach (function (item) {inconsistent[2].delete (item)});

	// display inconsistencies in the top table
	$("#s_inconsistent").text (inconsistent[0].size);
	$("#r_inconsistent").text (inconsistent[1].size);
	$("#g_inconsistent").text (inconsistent[2].size);

	// display current model size in top table
	$("#s_cur").text (Object.keys(networks.original.species).length - filter_species.size);
	$("#r_cur").text (Object.keys(networks.original.reactions).length - filter_reaction.size);
	$("#g_cur").text (Object.keys(networks.original.genenet).length - filter_genes.size);

	// prepare filters
	const s = Array.from(filter_species);
	const r = Array.from(filter_reaction);
	const g = Array.from(filter_genes);

	// update the batch field
	$("#batch-filter").val ("species: " + s.join (", ") + "\nreactions: " + r.join (", ") + "\ngenes: " + g.join (", "));

	// and store the filter at the backend session
	storeFilters (s, r, g);
}

/*
 * 
 * truncate -- shrink a string to a max size and append ...
 * @param str the long string
 * @param length the max length of the string, defaults to 40
 * @return the truncated string
 * 
 */
function truncate (str, length=40) {
	ending = "...";
	if (str.length > length)
		return str.substring(0, length - ending.length) + ending;
	return  str;
}

/*
 * 
 * fill_network_table -- fill the network tables
 * 
 * create rows for species, reactions and genes
 * and bind click logic
 * 
 * @param the initial filter
 * 
 */
function fill_network_table (filter) {
	// species
	for (var key in networks.original.species) {
		if (networks.original.species.hasOwnProperty(key)) {
			const item = networks.original.species[key];
			item.DOM = domIdMapper (item.identifier);
			// is it filtered?
			var checked = filter["filter_species"].includes(key) ? "" : " checked";
			// create DOM row
			const row = $("<tr id='"+item.DOM+"'><td class='check'><input type='checkbox'"+checked+"></td><td><abbr title='"+item.identifier+"'>"+truncate (item.identifier, 20)+"</abbr></td><td><abbr title='"+item.name+"'>"+truncate (item.name)+"</abbr></td><td title='occurs in "+item.occurence.join (", ")+"'>"+item.occurence.length+"</td></tr>");
			$('#species-table').append(row);
		}
	};
	//reactions
	for (var key in networks.original.reactions) {
		if (networks.original.reactions.hasOwnProperty(key)) {
			const item = networks.original.reactions[key];
			item.DOM = domIdMapper (item.identifier);
			// is it filtered?
			var checked = filter["filter_reactions"].includes(key) ? "" : " checked";
			// create DOM row
			const row = $("<tr id='"+item.DOM+"'><td class='check'><input type='checkbox'"+checked+"></td><td><abbr title='"+item.identifier+"'>"+truncate (item.identifier, 20)+"</abbr></td><td><abbr title='"+item.name+"'>"+truncate (item.name)+"</abbr></td><td><small>"+item.consumed.join (" + ") + "</small> <i class='fas fa-arrow-right'></i> <small>" + item.produced.join (" + ") +"</small></td><td><small>"+item.genes.join ("</small> [OR] <small>") +"</small></td></tr>");
			$('#reaction-table').append(row);
		}
	};
	// genes
	for (var key in networks.original.genenet) {
		if (networks.original.genenet.hasOwnProperty(key)) {
			const item = networks.original.genenet[key];
			item.DOM = domIdMapper (key);
			// is it filtered?
			var checked = filter["filter_genes"].includes(key) ? "" : " checked";
			// create DOM row
			const row = $("<tr id='"+item.DOM+"'><td class='check'><input type='checkbox'"+checked+"></td><td title='occurs in "+networks.original.genenet[key].reactions.join (", ")+"'>"+key+"</td></tr>");
			$('#gene-table').append(row);
		}
	};

	// if a checkbox is clicked: update the network and store the filters
	$("#filter-tables input[type=checkbox]").change (updateNetwork);
	
	// make the tables sortable
	prepareTableSorting ();
}


/*
 * 
 * getCellValue --get the value of a cell
 * 
 * if the cell contains a checkbox, it will return the 'checked' state (so people can sort for included/excluded entities),
 * otherwise it will just return the textual content of the cell -> lexicographical sorting of columns
 * 
 * @param row the row of the cell in the table
 * @param index the column of the cell in the table
 * @return the value to compare
 * 
 */
function getCellValue(row, index){
	var td = $(row).children('td').eq(index);
	if (td.hasClass ("check"))
		return td.find ("input[type=checkbox]").first ().prop("checked") == true;
	return td.text();
}

/*
 * 
 * comparer -- get a comparator to compare rows in a table
 * @param index the column to compare
 * @return lamda to compare columns in two rows
 * 
 */
function comparer(index) {
  return function(a, b) {
	  var valA = getCellValue(a, index), valB = getCellValue(b, index);
	  return $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.toString().localeCompare(valB);
  }
}
/*
 * 
 * prepareTableSorting -- prepare the tables for sorting
 * 
 * that is, make the headers "clickable"
 * 
 */
function prepareTableSorting () {
	// do it for all .sortable tables
	$('.sortable th').click(function(){
		$( this ).parent ().find('.sortsymbol').remove ();
		var asc = !$( this ).hasClass ("sorted-asc");
		$( this ).parent ().find ('th').removeClass ("sorted-desc");
		$( this ).parent ().find ('th').removeClass ("sorted-asc");
		
		var table = $(this).parents('table').eq(0);
		var rows = table.find('tr:gt(0)').toArray().sort(comparer($(this).index()));
		
		if (asc)
			$(this).addClass ("sorted-asc").append (" <i class='fas fa-sort-up sortsymbol'></i>");
		else {
			$(this).addClass ("sorted-desc").append (" <i class='fas fa-sort-down sortsymbol'></i>");
			rows = rows.reverse();
		}
		
		for (var i = 0; i < rows.length; i++)
			table.append(rows[i]);
	});
	
	// trigger initial sorting of the table
	$('.sortable th').eq(0).click ();
	$('.sortable.notfirst th').eq(1).click ();
}

/**
 * 
 * loadNetwork -- load the current network from the api
 * 
 * and build the tables
 * 
 */
function loadNetwork () {
	$("#error").hide ();
	$.ajax({
		url: '/api/get_network',
		dataType: 'json',
		success: function (data) {
			// got something, but was it successfull?
			if (data.status != 'success') {
				$("#filtercontainer").hide ();
				$("#loading").hide ();
				$("#error").show ().text ("Failed to retrieve the network: " + data.error);
				return;
			}
			
			// fill the table with original values
			$("#s_org").text (Object.keys(data.network.species).length);
			$("#r_org").text (Object.keys(data.network.reactions).length);
			$("#g_org").text (Object.keys(data.network.genenet).length);
			networks.original = data.network;
		  
			// display the necessary things..
			$("#filtercontainer").show ();
			$("#loading").hide ();
			$("#error").hide ();
		  
			// fill the filter tables
			fill_network_table (data.filter);
			updateNetwork ();
		},
		error: function (jqXHR, textStatus, errorThrown) {
			$("#filtercontainer").hide ();
			$("#loading").hide ();
			$("#error").show ().text ("Failed to retrieve the network: " + errorThrown + " (" + textStatus + ")");
		}
	});
	
	$("#batch-button").click (function (){
		filters = $("#batch-filter").val().split("\n");
		var s = [];
		var r = [];
		var g = [];
		for(var n = 0; n < filters.length; n++) {
			var l = filters[n].split(":");
			if (l.length != 2)
				continue;
			var ids = l[1].split(",");
			var cleanids = [];
			for(var m = 0; m < ids.length; m++) {
				var i = ids[m].trim ();
				if (i.length > 0)
					cleanids.push (i);
			}
			if (l[0].trim () === "species")
				s = cleanids;
			if (l[0].trim () === "reactions")
				r = cleanids;
			if (l[0].trim () === "genes")
				g = cleanids;
		}
	
		storeFilters (s, r, g, function () {location.reload();});
		
		
	});
}

/**
 * 
 * prepareExport -- prepare the export page
 * 
 * implement form logic (for enzyme networks, something must be selected etc...)
 * 
 */
function prepareExport () {
	// find the "id" of the enzyme network option in the select field
	var enzyme_option = 'en';
	$("#" + network_type_id + " option").each (function () {
		if ($(this).text().toLowerCase().includes("enzyme")) {
			enzyme_option = $(this).val();
		}
	});
  
	// enable/disable remove_reaction_genes_removed_id radio button, depending on the choice of the network type...
	$("#" + network_type_id).change (function () {
		if ($("#" + network_type_id).val () == enzyme_option) {
			$("#" + remove_reaction_genes_removed_id).prop ("checked", true);
			$("#" + remove_reaction_genes_removed_id).prop ("disabled", true);
		} else {
			$("#" + remove_reaction_genes_removed_id).prop ("disabled", false);
		}
	});
	
	// trigger the logic
	$("#" + network_type_id).change ();
  
  $("#export_form").submit (function (event){
    event.preventDefault();
    $("#download-error").text ("");
    var datastring = $("#export_form").serialize();
    $("#download-button").prop("disabled",true);
    $.ajax({
      type: "POST",
      data: datastring,
      url: "/api/export",
      dataType: "json",
      success: function(data) {
        $("#download-button").prop("disabled",false);
        window.location = '/api/serve/' + data["name"] + "/" + data["mime"];
      },
      error: function (jqXHR, textStatus, errorThrown) {
        $("#download-error").text ("error generating file: " + errorThrown + " -- " + textStatus);
        $("#download-button").prop("disabled",false);
      }
    });
    
  })
}

/**
 * 
 * select_biomodel -- select a model from biomodels using ist model id
 * will redirect to the filter page if successful
 * 
 * @param modelid the id of the model, such as MODEL1212060001 or BIOMD0000000469
 * 
 */
function select_biomodel (modelid) {
		if (!modelid.match (/^(BIOMD|MODEL)[0-9]{10}$/)) {
			$("#error").show ().text ("Invalid model id. Please go to Biomodels to copy a valid model id, such as MODEL1212060001 or BIOMD0000000469.");
			return
		}
		$("#error").hide ();
		
		$.ajax({
			url: '/api/select_biomodel',
			dataType: 'json',
			method: "POST",
			headers: {"X-CSRFToken": token},
			data: JSON.stringify({
				biomodels_id: modelid
			}),
			success: function (data) {
				// successfully downloaded something, but was the request also successfull?
				if (data.status != 'success') {
					$("#error").show ().text ("Failed to select Biomodel: " + data.error);
					$("#specific-biomodel-loading").hide ();
					return;
				}
				// all right, let's move on to filtering
				window.location = filter_url;
			},
			error: function (jqXHR, textStatus, errorThrown) {
				$("#error").show ().text ("Failed to obtain Biomodel: " + errorThrown);
				$("#specific-biomodel-loading").hide ();
			}
		});
	
}


/**
 * 
 * prepareIndex -- prepare the enalyzing index page
 * 
 * including download of bigg models and biomodels, binding click events to buttons, etc
 * 
 */
function prepareIndex () {
	$("#error").hide ();
	
	// download the bigg models list
	$.ajax({
        url: '/api/get_bigg_models',
        dataType: 'json',
        success: function (data) {
					// successfully downloaded something, but was the request also successfull?
					if (data.status != 'success') {
						$("#error").show ().text ("Failed to obtain BiGG models: " + data.error);
						return;
					}
					
					// if it was successful: build the table
					for (var model of data.results) {
						model.DOM = domIdMapper (model.bigg_id);
						const row = $("<tr id='"+model.DOM+"'><td><a class='bigg_id'>"+model.bigg_id+"</a></td><td>"+model.organism+"</td><td>"+model.metabolite_count+"</td><td>"+model.reaction_count+"</td><td>"+model.gene_count+"</td></tr>");
						$('#bigg-table').append(row);
					};
					
					// add click events to model ids
					$('.bigg_id').click (function () {
						const modelid = $(this).text ();
						$(this).html ("<i class='fa fa-spinner w3-spin'></i> loading model");
						
						// select the model
						$.ajax({
							url: '/api/select_bigg_model',
							dataType: 'json',
							method: "POST",
							headers: {"X-CSRFToken": token},
							data: JSON.stringify({
								bigg_id: modelid
							}),
							success: function (data) {
								// successfully downloaded something, but was the request also successfull?
								if (data.status != 'success') {
									$("#error").show ().text ("Failed to select BiGG model: " + data.error);
									return;
								}
								// all right, let's move on to filtering
								window.location = filter_url;
							},
							error: function (jqXHR, textStatus, errorThrown) {
								$("#error").show ().text ("Failed to obtain BiGG models: " + errorThrown);
							}
						});
					});
					$("#bigg_loading").hide ();
					$("#choose-bigg table").show ();
        },
        error: function (jqXHR, textStatus, errorThrown) {
					$("#bigg_loading").hide ();
					$("#choose-bigg table").hide ();
					$("#error").show ().text ("Failed to obtain BiGG models: " + errorThrown);
        }
    });
      
      
  // select a specific biomodel
  $('#specific-biomodel').click (function () {
		const modelid = $("#biomodelsid").val ().trim ();
		if (!modelid.match (/^(BIOMD|MODEL)[0-9]{10}$/)) {
			$("#error").show ().text ("Invalid model id. Please go to Biomodels to copy a valid model id, such as MODEL1212060001 or BIOMD0000000469.");
			return
		}
		$("#error").hide ();
		$("#specific-biomodel-loading").show ();
		// select the model
		select_biomodel (modelid);
	});
  
	// download the biomodels list  
	$.ajax({
        url: '/api/get_biomodels',
        dataType: 'json',
        success: function (data) {
					if (data.status != 'success') {
						$("#error").show ().text ("Failed to obtain Biomodels: " + data.error);
						return;
					}
					
					// if it was successful: build the table
					for (var model of data.models) {
						model.DOM = domIdMapper (model.id);
						const row = $("<tr id='"+model.DOM+"'><td><a class='biomodels_id'>"+model.id+"</a></td><td>"+model.name+"</td></tr>");
						$('#biomodels-table').append(row);
					}
			
					// add click events to model ids
					$('.biomodels_id').click (function () {
						const modelid = $(this).text ();
						$(this).html ("<i class='fa fa-spinner w3-spin'></i> loading model");
						// select the model
						select_biomodel (modelid);
					});
							
							
					$("#biomodels_loading").hide ();
					$("#choose-biomodels table").show ();
        },
        error: function (jqXHR, textStatus, errorThrown) {
          $("#biomodels_loading").hide ();
          $("#choose-biomodels table").hide ();
          $("#error").show ().text ("Failed to obtain Biomodels: " + errorThrown);
        }
    });
	prepareTableSorting ();
	
	
	
	$.ajax({
        url: '/api/status',
        dataType: 'json',
        success: function (data) {
					console.log (data)
				},
        error: function (jqXHR, textStatus, errorThrown) {
					console.log (errorThrown + " -- " + textStatus)
        }
    });
  
  
  $('#custom-model').change (function() {
		var fileName = '';
		fileName = $(this).val();
		if (fileName.indexOf("\\") !== -1)
			fileName = fileName.substring(fileName.lastIndexOf("\\") + 1, fileName.length);
		$('#upload-name').html(fileName);
	 });
}


/**
 * 
 * prepareImprint -- prepare the imprint page
 * 
 * including download of bigg models and biomodels, binding click events to buttons, etc
 * 
 */
function prepareImprint () {
	
	// get session information
	$.ajax({
        url: '/api/get_session_data',
        dataType: 'json',
        success: function (data) {
					if (data.status != 'success') {
						$("#sessionlist").append ("<li>Error retrieving session information: "+data.error+"</li>");
						return;
					}
					for (var key in data.data.session) {
						if (data.data.session.hasOwnProperty(key)) {
							$("#sessionlist").append ("<li><strong>" + key + ":</strong> " + data.data.session[key] + "</li>");
							$("#sessionlistNone").remove ();
						}
					}
					for (var i in data.data.files) {
						$("#fileslist").append ("<li>" + data.data.files[i] + "</li>");
						$("#fileslistNone").remove ();
					}
				},
        error: function (jqXHR, textStatus, errorThrown) {
					$("#sessionlist").append ("<li>Error retrieving session information: "+errorThrown+"</li>");
        }
	});
	
	$("#clear-session").click (function () {
		$.ajax({
			url: '/api/clear_data',
			dataType: 'json',
			success: function (data) {
				location.reload(); 
			},
			error: function (jqXHR, textStatus, errorThrown) {
				alert ("Error clearing data: "+errorThrown);
			}
		});
	});
}
